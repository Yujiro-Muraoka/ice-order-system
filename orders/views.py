from django.shortcuts import render, redirect, get_object_or_404, get_list_or_404
from django.http import HttpResponseRedirect, JsonResponse
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from django.utils.timezone import localtime
from django.db.models import Count
from .models import Order
import uuid
from datetime import timedelta
import time
from django.utils.timezone import now as tz_now
from django.utils.timezone import now as timezone_now


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

# アイスの種類
FLAVORS = [
    "ジャージー牛乳", "抹茶", "マンゴー", "チョコミント", "黒豆", "塩キャラ",
    "いちご", "いちごミルク", "井田塩", "カシス", "ショコラ", "さくらもち"
]

@csrf_exempt
def add_temp_ice(request):
    if request.method == 'POST':
        flavor1 = request.POST.get('flavor1')
        flavor2 = request.POST.get('flavor2') or None
        size = request.POST.get('size')
        container = request.POST.get('container')

        if not (flavor1 and size and container):
            return JsonResponse({'status': 'error', 'message': '必要な情報が不足しています'}, status=400)

        ice = {
            'flavor1': flavor1,
            'flavor2': flavor2,
            'size': size,
            'container': container
        }
        temp_ice = request.session.get('temp_ice', [])
        temp_ice.append(ice)
        request.session['temp_ice'] = temp_ice

        clip_color = request.POST.get('clip_color')
        clip_number = request.POST.get('clip_number')

        if clip_color and clip_number:
            request.session['clip_color'] = clip_color
            request.session['clip_number'] = clip_number

        return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'error', 'message': 'POST以外は許可されていません'}, status=405)

def submit_order_group(request):
    temp_ice = request.session.get('temp_ice', [])
    if not temp_ice:
        return redirect('/register')

    clip_color = request.POST.get('clip_color')
    clip_number = request.POST.get('clip_number')
    
    # 🆕 ここで group_id を作成
    group_id = f"{clip_color}-{clip_number}-{int(time.time() * 1000)}"

    for item in temp_ice:
        Order.objects.create(
            size=item['size'],
            container=item['container'],
            flavor1=item['flavor1'],
            flavor2=item.get('flavor2'),
            group_id=group_id,
            status='ok',
            clip_color=clip_color,
            clip_number=clip_number
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

    all_orders = Order.objects.order_by('timestamp')

    grouped_orders = {}
    for order in all_orders:
        grouped_orders.setdefault(order.group_id, []).append(order)

    now = timezone.localtime()

    active_count = sum(
        1 for orders in grouped_orders.values()
        if any(not o.is_completed for o in orders)
    )

    filtered_grouped_orders = {}
    completed_grouped_orders = {}

    for group_id, orders in grouped_orders.items():
        for o in orders:
            o.elapsed_seconds = int((now - o.timestamp).total_seconds())
            o.elapsed_minutes = o.elapsed_seconds // 60

        if all(o.is_completed for o in orders):
            latest_completion = max((o.completed_at for o in orders if o.completed_at), default=None)
            if latest_completion and now - latest_completion <= timedelta(seconds=30):
                completed_grouped_orders[group_id] = orders
        else:
            filtered_grouped_orders[group_id] = orders

    return render(request, 'orders/ice.html', {
        'grouped_orders': filtered_grouped_orders,
        'completed_orders': completed_grouped_orders,
        'now': now,
        'active_count': active_count,
    })


def complete_order(request, order_id):
    if not request.session.get('logged_in'):
        return redirect('/login')
    order = get_object_or_404(Order, id=order_id)
    order.is_completed = True
    order.completed_at = timezone.now()
    order.status = 'hold'
    order.save()
    return HttpResponseRedirect('/ice')

@csrf_exempt
def complete_group(request, group_id):
    if request.method == 'POST':
        orders = Order.objects.filter(group_id=group_id)
        now = timezone.now()
        for order in orders:
            order.is_completed = True
            order.completed_at = now
            order.status = 'hold'
            order.save()
    return redirect('/ice')

@csrf_protect
def delete_group(request, group_id):
    if request.method == 'POST':
        Order.objects.filter(group_id=group_id).delete()
    return redirect('/ice')

@csrf_protect
def delete_group_from_deshap(request, group_id):
    if request.method == 'POST':
        Order.objects.filter(group_id=group_id).delete()
    return redirect('/deshap')


def order_detail(request, order_id):
    if not request.session.get('logged_in'):
        return redirect('/login')
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'orders/detail.html', {'order': order})

def delete_temp_ice(request, index):
    temp_ice = request.session.get('temp_ice', [])
    if 0 <= index < len(temp_ice):
        del temp_ice[index]
        request.session['temp_ice'] = temp_ice
    return redirect('/register')



def deshap_view(request):
    # 自動ステータス切り替え
    pending = Order.objects.filter(is_completed=False).exclude(status='hold')
    count = pending.values('group_id').distinct().count()

    target_groups = pending.values_list('group_id', flat=True).distinct()
    for group_id in target_groups:
        group_orders = Order.objects.filter(group_id=group_id)
        if group_orders.exists():
            if group_orders.first().status in ['ok', 'stop']:
                continue
            new_status = 'ok' if count <= 3 else 'stop'
            group_orders.update(status=new_status)

    # グループごとに分ける（完了／未完了）
    all_orders = Order.objects.order_by('timestamp')
    grouped = {}
    for order in all_orders:
        grouped.setdefault(order.group_id, []).append(order)

    now = localtime()
    active_orders = {}
    completed_orders = {}

    for group_id, orders in grouped.items():
        if all(o.is_completed for o in orders):
            completed_times = [o.completed_at for o in orders if o.completed_at]
            if completed_times and now - max(completed_times) <= timedelta(seconds=30):
                completed_orders[group_id] = orders
        else:
            active_orders[group_id] = orders

    active_count = sum(
        1 for orders in active_orders.values()
        if any(not o.is_completed for o in orders)
    )

    return render(request, 'orders/deshap.html', {
        'grouped_orders': active_orders,
        'completed_orders': completed_orders,
        'now': now,
        'active_count': active_count,
    })

@csrf_exempt
def update_status(request, group_id, new_status):
    if request.method == 'POST' and new_status in ['ok', 'stop']:
        Order.objects.filter(group_id=group_id).update(status=new_status)
    return redirect('/deshap')
