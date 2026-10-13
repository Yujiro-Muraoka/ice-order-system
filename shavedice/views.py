from common.orders import migrate_legacy_cart
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
from django.db.models import Count, Max, Q
from uuid import uuid4


def _calculate_shavedice_refresh_metrics():
    aggregates = ShavedIceOrder.objects.aggregate(
        active_items=Count('id', filter=Q(is_completed=False)),
        latest_id=Max('id'),
        latest_status_ts=Max('status_modified_at'),
    )
    active_order_total = aggregates['active_items'] or 0
    latest_order_id = aggregates['latest_id'] or 0
    latest_status_ts = aggregates['latest_status_ts']
    status_marker = (
        str(latest_status_ts.timestamp()) if latest_status_ts else '0'
    )
    refresh_value = f"{active_order_total}:{latest_order_id}:{status_marker}"
    return {
        'active_order_total': active_order_total,
        'latest_order_id': latest_order_id,
        'latest_status_marker': status_marker,
        'refresh_value': refresh_value,
    }


def _get_order_context():
    """キッチンビューとデシャップビューで共通のコンテキストを取得する"""
    now = timezone.localtime()
    
    # 注文を取得
    active_orders = ShavedIceOrder.objects.filter(is_completed=False).order_by('timestamp')
    completed_orders = ShavedIceOrder.objects.filter(is_completed=True, completed_at__gte=now - timedelta(seconds=30)).order_by('completed_at')
    
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
            
    metrics = _calculate_shavedice_refresh_metrics()

    return {
        "grouped_orders": grouped_active,
        "completed_orders": grouped_completed,
        "now": now,
        "active_count": len(grouped_active),
        "active_order_total": metrics['active_order_total'],
        "refresh_value": metrics['refresh_value'],
    }


def shavedice_register(request):
    """かき氷注文登録画面を表示"""
    migrate_legacy_cart(request.session)
    temp_ice = request.session.get("temp_shavedice", [])
    
    flavor_choices = ShavedIceOrder.FLAVOR_CHOICES
    
    context = {
        "temp_ice": temp_ice,
        "flavor_choices": flavor_choices,
        "clip_numbers_first": list(range(1, 9)),
        "clip_numbers_second": list(range(9, 17)),
    }
    
    return render(request, "shavedice/shavedice_register.html", context)


@csrf_exempt
def add_temp_ice(request):
    """仮注文をセッションに追加"""
    migrate_legacy_cart(request.session)
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
    temp_ice = request.session.get('temp_shavedice', [])
    temp_ice.append(ice)
    request.session['temp_shavedice'] = temp_ice
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
    migrate_legacy_cart(request.session)
    if request.method != 'POST':
        return redirect('shavedice_register')
    
    temp_ice_list = request.session.get('temp_shavedice', [])
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
    group_id = uuid4().hex[:20]
    
    # 状態判定
    has_stop = ShavedIceOrder.objects.filter(is_completed=False, status='stop').exists()
    status = 'stop' if has_stop else 'ok'
    auto_stopped = has_stop
    
    orders = []
    # 注文をDBに保存
    for ice in temp_ice_list:
        flavor = ice.get('flavor')
        if not flavor:
            continue
        orders.append(ShavedIceOrder(
            flavor=flavor,
            clip_color=clip_color,
            clip_number=clip_number,
            group_id=group_id,
            status=status,
            is_auto_stopped=auto_stopped,
            note=note
        ))
    
    ShavedIceOrder.objects.bulk_create(orders)

    # セッション初期化
    request.session['temp_shavedice'] = []
    request.session.pop('clip_color', None)
    request.session.pop('clip_number', None)
    request.session.modified = True
    return redirect('shavedice_register')


def shavedice_kitchen(request):
    """かき氷キッチン画面を表示"""
    context = _get_order_context()
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('format') == 'json':
        return JsonResponse({
            'value': context['refresh_value'],
            'refresh_value': context['refresh_value'],
            'active_order_total': context['active_order_total'],
            'active_count': context['active_count'],
            'timestamp': context['now'].isoformat(),
        })
    return render(request, "shavedice/shavedice_kitchen.html", context)


def ice_view(request):
    """かき氷一覧画面を表示"""
    return shavedice_kitchen(request)


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
    migrate_legacy_cart(request.session)
    temp_ice = request.session.get('temp_shavedice', [])
    if 0 <= index < len(temp_ice):
        del temp_ice[index]
        request.session['temp_shavedice'] = temp_ice
        request.session.modified = True
    
    return redirect('shavedice_register')


@csrf_exempt
def shavedice_update_status(request, group_id, new_status):
    """かき氷デシャップ画面からグループの状態を更新"""
    if request.method == 'POST' and new_status in {'ok', 'stop', 'hold'}:
        ShavedIceOrder.objects.filter(group_id=group_id, is_completed=False).update(
            status=new_status,
            is_auto_stopped=False,
            status_modified_at=timezone.now(),
        )
    return redirect('shavedice_deshap')


def shavedice_deshap_view(request):
    """かき氷デシャップ担当画面"""
    context = _get_order_context()
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('format') == 'json':
        return JsonResponse({
            'value': context['refresh_value'],
            'refresh_value': context['refresh_value'],
            'active_order_total': context['active_order_total'],
            'active_count': context['active_count'],
            'timestamp': context['now'].isoformat(),
        })
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
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('format') == 'json':
        return JsonResponse({
            'value': wait_minutes,
            'wait_minutes': wait_minutes,
            'uncompleted_count': uncompleted_count,
            'timestamp': timezone.now().isoformat(),
        })
    return render(request, 'shavedice/wait_time.html', context)