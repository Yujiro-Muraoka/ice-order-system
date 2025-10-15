from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.views.decorators.http import require_POST
from django.utils import timezone
from collections import defaultdict
from datetime import timedelta
from django.contrib import messages
from .models import ShavedIceOrder
from food.models import FoodOrder
import time


def _get_order_context():
    """キッチンビューとデシャップビューで共通のコンテキストを取得する"""
    now = timezone.localtime()
    
    # 注文を取得
    active_orders = ShavedIceOrder.objects.filter(is_completed=False).order_by('timestamp')
    completed_orders = ShavedIceOrder.objects.filter(is_completed=True).order_by('-completed_at')
    
    # グループ化
    grouped_active = {}
    grouped_completed = {}
    
    for order in active_orders:
        delta = now - order.timestamp
        order.elapsed_minutes = int(delta.total_seconds() // 60)
        grouped_active.setdefault(order.group_id, []).append(order)
    
    for order in completed_orders:
        # 完了から30秒以内のみ表示
        if order.completed_at and (now - order.completed_at).total_seconds() <= 30:
            grouped_completed.setdefault(order.group_id, []).append(order)
            
    return {
        "grouped_orders": grouped_active,
        "completed_orders": grouped_completed,
        "now": now,
        "active_count": len(grouped_active),
    }


def shavedice_register(request):
    """かき氷注文登録画面を表示"""
    temp_ice = request.session.get("temp_ice", [])
    
    flavor_choices = ShavedIceOrder.FLAVOR_CHOICES
    
    context = {
        "temp_ice": temp_ice,
        "flavor_choices": flavor_choices
    }
    
    return render(request, "shavedice/shavedice_register.html", context)


@csrf_exempt
def add_temp_ice(request):
    """仮注文をセッションに追加"""
    if request.method != 'POST':
        return JsonResponse({
            'status': 'error', 
            'message': 'POST以外は許可されていません'
        }, status=405)
    
    flavor = request.POST.get('flavor', '').strip()
    
    # 入力チェック
    if not flavor:
        messages.error(request, 'フレーバーを選択してください。')
        return redirect('shavedice_register')
    
    # 仮注文を作成
    ice = {'flavor': flavor}
    temp_ice = request.session.get('temp_ice', [])
    temp_ice.append(ice)
    request.session['temp_ice'] = temp_ice
    request.session.modified = True
    
    # クリップ情報も保存
    clip_color = request.POST.get('clip_color')
    clip_number = request.POST.get('clip_number')
    if clip_color and clip_number:
        request.session['clip_color'] = clip_color
        request.session['clip_number'] = clip_number
        request.session.modified = True
    
    wants_json = request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in request.headers.get('accept', '')
    if wants_json:
        return JsonResponse({'status': 'ok'})
    
    return redirect('shavedice_register')


@csrf_exempt
def submit_order_group(request):
    """仮注文を本注文としてDBに保存"""
    if request.method != 'POST':
        return redirect('shavedice_register')
    
    temp_ice_list = request.session.get('temp_ice', [])
    clip_color = request.POST.get('clip_color', 'white')
    clip_number_str = request.POST.get('clip_number', '0')
    note = request.POST.get('note', "")
    
    # 入力チェック
    if not temp_ice_list:
        return redirect('shavedice_register')
    
    try:
        clip_number = int(clip_number_str)
    except (ValueError, TypeError):
        clip_number = 0
    
    # グループID生成
    group_id = f"{clip_color}-{clip_number}-{int(time.time() * 1000)}"
    
    # 状態判定
    has_stop = ShavedIceOrder.objects.filter(is_completed=False, status='stop').exists()
    status = 'stop' if has_stop else 'ok'
    auto_stopped = has_stop
    
    # 注文をDBに保存
    for ice in temp_ice_list:
        flavor = ice.get('flavor')
        if not flavor:
            continue
        ShavedIceOrder.objects.create(
            flavor=flavor,
            clip_color=clip_color,
            clip_number=clip_number,
            group_id=group_id,
            status=status,
            is_auto_stopped=auto_stopped,
            note=note
        )
    
    # セッション初期化
    request.session['temp_ice'] = []
    request.session.pop('clip_color', None)
    request.session.pop('clip_number', None)
    request.session.modified = True
    return redirect('shavedice_register')


def shavedice_kitchen(request):
    """かき氷キッチン画面を表示"""
    context = _get_order_context()
    context["debug"] = True 
    return render(request, "shavedice/shavedice_kitchen.html", context)


def ice_view(request):
    """かき氷一覧画面を表示"""
    now = timezone.localtime()
    
    # 全注文を取得
    all_orders = ShavedIceOrder.objects.order_by('timestamp')
    
    # グループ化
    grouped_orders = {}
    for order in all_orders:
        grouped_orders.setdefault(order.group_id, []).append(order)
    
    # 未完了・完了注文を分離
    active_orders = {}
    completed_orders = {}
    
    for group_id, orders in grouped_orders.items():
        # 経過時間を計算
        for o in orders:
            o.elapsed_seconds = int((now - o.timestamp).total_seconds())
            o.elapsed_minutes = o.elapsed_seconds // 60
        
        if all(o.is_completed for o in orders):
            latest_completion = max(
                (o.completed_at for o in orders if o.completed_at), 
                default=None
            )
            if latest_completion and now - latest_completion <= timedelta(seconds=30):
                completed_orders[group_id] = orders
        else:
            active_orders[group_id] = orders
    
    active_count = len(active_orders)
    
    context = {
        'grouped_orders': active_orders,
        'completed_orders': completed_orders,
        'now': now,
        'active_count': active_count,
    }
    
    context['is_logged_in'] = request.session.get('logged_in', False)
    return render(request, 'shavedice/ice.html', context)


@require_POST
def complete_order(request, order_id):
    """指定IDの注文を完了"""
    order = get_object_or_404(ShavedIceOrder, id=order_id)
    order.is_completed = True
    order.completed_at = timezone.now()
    order.status = 'hold'
    order.save()
    
    return redirect('shavedice_kitchen')


@csrf_exempt
def complete_group(request, group_id):
    """指定グループの注文を一括完了"""
    if request.method == 'POST':
        now = timezone.now()
        ShavedIceOrder.objects.filter(group_id=group_id).update(is_completed=True, completed_at=now)
    return redirect('shavedice_kitchen')


@csrf_protect
def delete_group(request, group_id):
    """指定グループの注文を削除"""
    if request.method == 'POST':
        ShavedIceOrder.objects.filter(group_id=group_id).delete()
    
    return redirect('shavedice_kitchen')


def order_detail(request, order_id):
    """注文詳細画面を表示"""
    if not request.session.get('logged_in'):
        return redirect('login')
    
    order = get_object_or_404(ShavedIceOrder, id=order_id)
    return render(request, 'shavedice/detail.html', {'order': order})


def delete_temp_ice(request, index):
    """仮注文リストから指定インデックスの注文を削除"""
    temp_ice = request.session.get('temp_ice', [])
    if 0 <= index < len(temp_ice):
        del temp_ice[index]
        request.session['temp_ice'] = temp_ice
        request.session.modified = True
    
    return redirect('shavedice_register')


@csrf_exempt
def shavedice_update_status(request, group_id, new_status):
    """かき氷デシャップ画面からグループの状態を更新"""
    if request.method == 'POST':
        ShavedIceOrder.objects.filter(group_id=group_id).update(status=new_status)
    return redirect('shavedice_deshap')


def shavedice_deshap_view(request):
    """かき氷デシャップ担当画面"""
    context = _get_order_context()
    return render(request, "shavedice/deshap.html", context)


def wait_time_view(request):
    """
    かき氷の未完了注文数から待ち時間（1つ3分）を計算して表示するビュー
    """
    from .models import ShavedIceOrder
    uncompleted_count = ShavedIceOrder.objects.filter(is_completed=False).count()
    wait_minutes = uncompleted_count * 3
    context = {
        'uncompleted_count': uncompleted_count,
        'wait_minutes': wait_minutes,
    }
    return render(request, 'shavedice/wait_time.html', context)