from django.shortcuts import render, redirect, get_object_or_404, get_list_or_404
from django.http import HttpResponseRedirect, JsonResponse
from django.contrib import messages
from django.utils import timezone
from .models import IceOrder
import uuid
from datetime import timedelta
from django.views.decorators.csrf import csrf_protect
from django.utils.timezone import localtime
from django.db.models import Count


SHARED_PASSCODE = "1234"  # 任意の共有パスコード

# ログインビュー
def login_view(request):
    if request.method == 'POST':
        code = request.POST.get('passcode')
        if code == SHARED_PASSCODE:
            request.session['logged_in'] = True
            return redirect('/')
        else:
            messages.error(request, "パスコードが間違っています")
    return render(request, 'orders/login.html')


def logout_view(request):
    request.session.flush()
    return redirect('/login')


# ロール選択
def role_select(request):
    if not request.session.get('logged_in'):
        return redirect('/login')
    return render(request, 'orders/role_select.html')


# アイスクリームの種類
FLAVORS = [
    "ジャージー牛乳", "抹茶", "マンゴー", "チョコミント", "黒豆", "塩キャラ",
    "いちご", "いちごミルク", "井田塩", "カシス", "ショコラ", "さくらもち"
]

def add_temp_ice(request):
    if request.method == 'POST':
        flavor1 = request.POST.get('flavor1')
        flavor2 = request.POST.get('flavor2') or None
        size = request.POST.get('size')
        container = request.POST.get('container')

        ice = {
            'flavor1': flavor1,
            'flavor2': flavor2,
            'size': size,
            'container': container
        }

        temp_ice = request.session.get('temp_ice', [])
        temp_ice.append(ice)
        request.session['temp_ice'] = temp_ice
        return JsonResponse({'status': 'ok'})



# 仮アイス一覧送信（まとめて保存）
def submit_order_group(request):
    temp_ice = request.session.get('temp_ice', [])
    if not temp_ice:
        return redirect('/register')

    now = localtime()
    hour_start = now.replace(minute=0, second=0, microsecond=0)

    # この1時間に登録済みの件数を数える
    order_count = IceOrder.objects.filter(timestamp__gte=hour_start).count() + 1

    # オーダー番号：2025-0509-14-03
    group_id = now.strftime('%Y-%m%d-%H') + f'-{order_count:02d}'

    for item in temp_ice:
        IceOrder.objects.create(
            size=item['size'],
            container=item['container'],
            flavor1=item['flavor1'],
            flavor2=item.get('flavor2'),
            order_group=group_id
        )

    request.session['temp_ice'] = []
    return redirect('/register')



def register_view(request):
    if not request.session.get('logged_in'):
        return redirect('/login')

    temp_ice = request.session.get('temp_ice', [])

    return render(request, 'orders/register.html', {
        'flavors': FLAVORS,
        'temp_ice': temp_ice,
        'container_map': {
            'cup': 'カップ',
            'cone': 'コーン'
        }
    })



def ice_view(request):
    if not request.session.get('logged_in'):
        return redirect('/login')

    all_orders = IceOrder.objects.order_by('timestamp')

    grouped_orders = {}
    for order in all_orders:
        grouped_orders.setdefault(order.order_group, []).append(order)

    # ✅ 現在時刻
    now = timezone.localtime()

    # ✅ 未完了数の集計
    active_count = sum(
        1 for orders in grouped_orders.values()
        if any(not o.is_completed for o in orders)
    )

    # ✅ 完了済み注文のうち、完了から1分未満のオーダーだけ残す
    filtered_grouped_orders = {}
    for group_id, orders in grouped_orders.items():
        if all(o.is_completed for o in orders):
            # すべて完了 → completed_at の最も遅い時刻を基準に経過時間を確認
            latest_completion = max(o.completed_at for o in orders if o.completed_at)
            if now - latest_completion <= timedelta(minutes=1):
                filtered_grouped_orders[group_id] = orders
        else:
            # 未完了のオーダーグループは常に表示
            filtered_grouped_orders[group_id] = orders

    return render(request, 'orders/ice.html', {
        'grouped_orders': filtered_grouped_orders,
        'now': now,
        'active_count': active_count,
    })




# 注文完了処理
def complete_order(request, order_id):
    if not request.session.get('logged_in'):
        return redirect('/login')

    order = get_object_or_404(IceOrder, id=order_id)
    order.is_completed = True
    order.completed_at = timezone.now()
    order.save()
    return HttpResponseRedirect('/ice')

@csrf_protect
def complete_group(request, group_id):
    orders = get_list_or_404(IceOrder, order_group=group_id)
    now = timezone.now()
    for order in orders:
        order.is_completed = True
        order.completed_at = now
        order.save()
    return redirect('/ice')

@csrf_protect
def delete_group(request, group_id):
    if request.method == 'POST':
        IceOrder.objects.filter(order_group=group_id).delete()
    return redirect('/ice')

# 注文詳細画面
def order_detail(request, order_id):
    if not request.session.get('logged_in'):
        return redirect('/login')

    order = get_object_or_404(IceOrder, id=order_id)
    return render(request, 'orders/detail.html', {'order': order})


def delete_temp_ice(request, index):
    temp_ice = request.session.get('temp_ice', [])
    if 0 <= index < len(temp_ice):
        del temp_ice[index]
        request.session['temp_ice'] = temp_ice
    return redirect('/register')

