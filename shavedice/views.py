from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import ShavedIceOrder
from django.shortcuts import render, redirect, get_object_or_404, get_list_or_404
from django.http import HttpResponseRedirect, JsonResponse
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from django.utils.timezone import localtime
from django.db.models import Count
import uuid
from datetime import timedelta
import time
from django.utils.timezone import now
from collections import defaultdict
from django.views.decorators.http import require_POST
from food.models import FoodOrder
from django.utils.timezone import now as tz_now
from django.utils.timezone import now as timezone_now
from django.http import HttpResponse
from django.utils import timezone

# views.py

def shavedice_register(request):
    print("--- shavedice_register ---")
    temp_ice = request.session.get("temp_ice", [])
    print("Session temp_ice (in register view):", temp_ice) # この出力
    flavors = [f[0] for f in ShavedIceOrder.FLAVOR_CHOICES]
    return render(request, "shavedice/shavedice_register.html", {
        "temp_ice": temp_ice,
        "flavors": flavors
    })

@csrf_exempt
def add_temp_ice(request):
    if request.method == 'POST':
        flavor = request.POST.get('flavor')

        if not (flavor):
            return JsonResponse({'status': 'error', 'message': '必要な情報が不足しています'}, status=400)

        ice = {
            'flavor': flavor,
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

@csrf_exempt
def submit_order_group(request):
    if request.method == 'POST':
        temp_ice_list = request.session.get('temp_ice', [])
        clip_color = request.POST.get('clip_color', 'white')
        clip_number = int(request.POST.get('clip_number', 0))
        note = request.POST.get('note', "")
        group_id = f"{clip_color}-{clip_number}-{int(time.time() * 1000)}"

        has_stop = ShavedIceOrder.objects.filter(is_completed=False, status='stop').exists()
        status = 'stop' if has_stop else 'ok'
        auto_stopped = has_stop

        for ice in temp_ice_list:
                ShavedIceOrder.objects.create(
                    flavor=ice['flavor'],
                    clip_color=clip_color,
                    clip_number=clip_number,
                    group_id=group_id,
                    status=status,
                    is_auto_stopped=auto_stopped,
                    note=note
                )

        request.session['temp_ice'] = []
        return redirect('shavedice_register')


    
def register_view(request):
    # セッションから仮オーダーを取得（なければ空リスト）
    temp_ice = request.session.get('temp_ice', [])

    # フレーバーの一覧（必要に応じて調整）
    flavors = [
        "🍧いちご🍧", "🍧抹茶🍧", "🍧ほうじ茶🍧", "🍧ゆず🍧"
    ]

    return render(request, 'shavedice/shavedice_register.html', {
        'flavors': flavors,
        'temp_ice': temp_ice,
    })
def shavedice_kitchen(request):
    now = timezone.localtime()

    active_orders = ShavedIceOrder.objects.filter(is_completed=False).order_by('timestamp')
    completed_orders = ShavedIceOrder.objects.filter(is_completed=True).order_by('-completed_at')

    grouped_active = {}
    grouped_completed = {}

    for order in active_orders:
        delta = now - order.timestamp
        order.elapsed_minutes = int(delta.total_seconds() // 60)
        grouped_active.setdefault(order.group_id, []).append(order)

    for order in completed_orders:
        grouped_completed.setdefault(order.group_id, []).append(order)

    return render(request, "shavedice/shavedice_kitchen.html", {
        "grouped_orders": grouped_active,
        "completed_orders": grouped_completed,
        "now": now,
        "active_count": len(grouped_active),
        "debug": True  # ← この行を追加
    })


def ice_view(request):
    if not request.session.get('logged_in'):
        return redirect('/login')

    now = timezone.localtime()

    # 全ての注文を取得（完了・未完了を含む）
    all_orders = ShavedIceOrder.objects.order_by('timestamp')

    # group_id = clip_color_clip_number で統一
    grouped_orders = {}
    for order in all_orders:
        grouped_orders.setdefault(order.group_id, []).append(order)

    active_orders = {}
    completed_orders = {}

    for group_id, orders in grouped_orders.items():
        for o in orders:
            o.elapsed_seconds = int((now - o.timestamp).total_seconds())
            o.elapsed_minutes = o.elapsed_seconds // 60

        if all(o.is_completed for o in orders):
            latest_completion = max((o.completed_at for o in orders if o.completed_at), default=None)
            if latest_completion and now - latest_completion <= timedelta(seconds=30):
                completed_orders[group_id] = orders  # ✅ 30秒以内のものだけ表示
        else:
            active_orders[group_id] = orders


    active_count = len(active_orders)

    return render(request, 'shavedice/ice.html', {
        'grouped_orders': active_orders,
        'completed_orders': completed_orders,
        'now': now,
        'active_count': active_count,
    })


def complete_order(request, order_id):
    if not request.session.get('logged_in'):
        return redirect('/login')
    order = get_object_or_404(ShavedIceOrder, id=order_id)
    order.is_completed = True
    order.completed_at = timezone.now()
    order.status = 'hold'
    order.save()
    return HttpResponseRedirect('/ice')

@csrf_exempt
def complete_group(request, group_id):
    if request.method == 'POST':
        try:
            # ✅ group_idは保存済みのもの（例: yellow-2-1747123456789）そのまま使う
            orders = ShavedIceOrder.objects.filter(group_id=group_id, is_completed=False)

            now = timezone.now()
            for order in orders:
                order.is_completed = True
                order.completed_at = now
                order.save()
        except Exception as e:
            print("[complete_group error]", e)
    return redirect('/ice')



def get_grouped_active_orders():
    from collections import defaultdict
    import datetime

    grouped = defaultdict(list)
    now_time = now()

    active_orders = ShavedIceOrder.objects.filter(is_completed=False).order_by('timestamp')
    for order in active_orders:
        # 経過分数を追加
        delta = now_time - order.timestamp
        order.elapsed_minutes = int(delta.total_seconds() // 60)
        grouped[order.group_id].append(order)

    return grouped

def get_grouped_completed_orders():
    completed_orders = ShavedIceOrder.objects.filter(is_completed=True).order_by('-completed_at')
    grouped = defaultdict(list)
    for order in completed_orders:
        grouped[order.group_id].append(order)
    return grouped

    
@csrf_protect
def delete_group(request, group_id):
    if request.method == 'POST':
        ShavedIceOrder.objects.filter(group_id=group_id).delete()
    return redirect('/shavedice_kitchen')

def order_detail(request, order_id):
    if not request.session.get('logged_in'):
        return redirect('/login')
    order = get_object_or_404(ShavedIceOrder, id=order_id)
    return render(request, 'shavedice/detail.html', {'order': order})

def delete_temp_ice(request, index):
    temp_ice = request.session.get('temp_ice', [])
    if 0 <= index < len(temp_ice):
        del temp_ice[index]
        request.session['temp_ice'] = temp_ice
    return redirect('/shavedice_register')