from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from django.views.decorators.http import require_POST
from collections import defaultdict
from datetime import timedelta
from .models import Order, FLAVOR_CHOICES
from food.models import FoodOrder
import time

# 共有パスコード
SHARED_PASSCODE = "1234"

# フレーバー一覧
FLAVORS = [
    "ジャージー牛乳", "マンゴー", "チョコミント", "塩キャラ",
    "井田塩", "カシス", "ショコラ", "さくらもち",
    "抹茶", "いちご", "ほうじ茶", "ゆず",
]


def _group_orders_by_id(orders):
    grouped = {}
    for order in orders:
        grouped.setdefault(order.group_id, []).append(order)
    return grouped


def _separate_active_completed(grouped_orders, now):
    active = {}
    completed = {}
    for group_id, orders in grouped_orders.items():
        sorted_orders = sorted(orders, key=lambda o: o.timestamp)
        if all(o.is_completed for o in sorted_orders):
            completed_times = [o.completed_at for o in sorted_orders if o.completed_at]
            if completed_times and now - max(completed_times) <= timedelta(seconds=30):
                completed[group_id] = sorted_orders
        else:
            active[group_id] = sorted_orders
    return active, completed


def _update_hold_status():
    pending_groups = list(
        Order.objects.filter(is_completed=False, status='hold')
        .values_list('group_id', flat=True)
        .distinct()
    )
    if not pending_groups:
        return
    new_status = 'ok' if len(pending_groups) <= 3 else 'stop'
    Order.objects.filter(group_id__in=pending_groups).update(status=new_status)


def _find_recent_groups(grouped_orders, threshold_seconds=3, reference_time=None):
    now = reference_time or timezone.now()
    recent_ids = []
    for group_id, orders in grouped_orders.items():
        if all(not o.is_completed for o in orders):
            if any((now - o.timestamp).total_seconds() < threshold_seconds for o in orders):
                recent_ids.append(group_id)
    return recent_ids


def _count_pudding_by_group(group_orders):
    return {
        group_id: sum(1 for o in orders if o.is_pudding)
        for group_id, orders in group_orders.items()
    }


def _count_active_order_items(active_orders):
    return sum(
        1
        for orders in active_orders.values()
        for order in orders
        if not order.is_completed
    )


def role_select(request):
    """役割選択画面"""
    if not request.session.get('logged_in'):
        return redirect('login')
    
    return render(request, 'common/role_select.html')


@csrf_exempt
def add_temp_ice(request):
    """仮注文をセッションに追加"""
    if request.method != 'POST':
        return JsonResponse(
            {
                'status': 'error',
                'message': 'POST以外は許可されていません'
            },
            status=405,
        )

    flavor1 = request.POST.get('flavor1')
    flavor2 = request.POST.get('flavor2') or None
    size = request.POST.get('size')
    container = request.POST.get('container')

    if not (flavor1 and size and container):
        messages.error(request, '必要な情報が不足しています。')
        return redirect('register_view')

    ice = {
        'flavor1': flavor1,
        'flavor2': flavor2,
        'size': size,
        'container': container,
    }

    temp_ice = request.session.get('temp_ice', [])
    temp_ice.append(ice)
    request.session['temp_ice'] = temp_ice
    request.session.modified = True

    clip_color = request.POST.get('clip_color')
    clip_number = request.POST.get('clip_number')
    if clip_color and clip_number:
        request.session['clip_color'] = clip_color
        request.session['clip_number'] = clip_number
        request.session.modified = True

    wants_json = (
        request.headers.get('x-requested-with') == 'XMLHttpRequest'
        or 'application/json' in request.headers.get('accept', '')
    )
    if wants_json:
        return JsonResponse({'status': 'ok'})

    return redirect('register_view')


@require_POST
def add_temp_pudding(request):
    """仮注文リストにアフォガードプリンを追加"""
    temp_ice = request.session.get('temp_ice', [])
    temp_ice.append({'is_pudding': True})
    request.session['temp_ice'] = temp_ice
    request.session.modified = True
    return HttpResponse("ok")


@csrf_exempt
def submit_order_group(request):
    """仮注文を本注文としてDBに保存"""
    if request.method != 'POST':
        return redirect('register_view')
    
    temp_ice_list = request.session.get('temp_ice', [])
    clip_color = request.POST.get('clip_color')
    clip_number_str = request.POST.get('clip_number')
    note = request.POST.get('note', "")
    
    # 入力チェック
    if not temp_ice_list or not clip_color or not clip_number_str:
        messages.warning(request, '仮注文またはクリップ情報が不足しています。')
        return redirect('register_view')
    
    try:
        clip_number = int(clip_number_str)
    except (ValueError, TypeError):
        messages.warning(request, 'クリップ番号が正しくありません。')
        return redirect('register_view')
    
    # グループID生成
    group_id = f"{clip_color}-{clip_number}-{int(time.time() * 1000)}"
    
    # 状態判定
    has_stop = Order.objects.filter(is_completed=False, status='stop').exists()
    status = 'stop' if has_stop else 'ok'
    auto_stopped = has_stop
    
    # 注文をDBに保存
    for ice in temp_ice_list:
        if ice.get('is_pudding'):
            Order.objects.create(
                is_pudding=True,
                clip_color=clip_color,
                clip_number=clip_number,
                group_id=group_id,
                status=status,
                is_auto_stopped=auto_stopped,
                note=note
            )
        else:
            Order.objects.create(
                size=ice['size'],
                container=ice['container'],
                flavor1=ice['flavor1'],
                flavor2=ice.get('flavor2'),
                clip_color=clip_color,
                clip_number=clip_number,
                group_id=group_id,
                status=status,
                is_auto_stopped=auto_stopped,
                note=note,
            )
    
    # セッション初期化
    request.session['temp_ice'] = []
    request.session.pop('clip_color', None)
    request.session.pop('clip_number', None)
    request.session.modified = True
    return redirect('register_view')


def register_view(request):
    """注文登録画面を表示"""
    temp_ice = request.session.get('temp_ice', [])
    
    # アフォガードプリンの数をカウント
    pudding_count = sum(1 for item in temp_ice if item.get('is_pudding'))
    
    # FLAVOR_CHOICESから日本語名のみを抽出
    flavors = [label for value, label in FLAVOR_CHOICES]
    
    # 容器表示用マップ
    container_map = {
        'cup': 'カップ',
        'cone': 'コーン'
    }
    
    context = {
        'flavors': flavors,
        'container_map': container_map,
        'temp_ice': temp_ice,
        'pudding_count': pudding_count,
    }
    
    return render(request, 'ice/register.html', context)


def ice_view(request):
    """アイスクリーム一覧画面を表示"""
    now = timezone.localtime()
    
    # 全注文を取得
    all_orders = Order.objects.order_by('timestamp')
    
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
    active_order_total = _count_active_order_items(active_orders)
    
    # プリン数を計算
    pudding_count_active = sum(
        sum(1 for o in orders if o.is_pudding)
        for orders in active_orders.values()
    )
    pudding_count_completed = sum(
        sum(1 for o in orders if o.is_pudding)
        for orders in completed_orders.values()
    )
    
    # 一覧上で「どのグループにプリンが何個あるか」を表示するため、グループ単位の個数も計算する。
    pudding_counts_active_by_group = {
        group_id: sum(1 for o in orders if o.is_pudding)
        for group_id, orders in active_orders.items()
    }
    pudding_counts_completed_by_group = {
        group_id: sum(1 for o in orders if o.is_pudding)
        for group_id, orders in completed_orders.items()
    }

    context = {
        'grouped_orders': active_orders,
        'completed_orders': completed_orders,
        'now': now,
        'active_count': active_count,
        'active_order_total': active_order_total,
        'pudding_count_active': pudding_count_active,
        'pudding_count_completed': pudding_count_completed,
        'pudding_counts_active_by_group': pudding_counts_active_by_group,
        'pudding_counts_completed_by_group': pudding_counts_completed_by_group,
    }
    
    context['is_logged_in'] = request.session.get('logged_in', False)
    return render(request, 'ice/ice.html', context)


@require_POST
def complete_order(request, order_id):
    """指定IDの注文を完了"""
    order = get_object_or_404(Order, id=order_id)
    order.is_completed = True
    order.completed_at = timezone.now()
    order.status = 'hold'
    order.save()
    
    return redirect('ice_view')


@csrf_exempt
def complete_group(request, group_id):
    """指定グループの注文を一括完了"""
    if request.method == 'POST':
        try:
            orders = Order.objects.filter(group_id=group_id, is_completed=False)
            now = timezone.now()
            
            for order in orders:
                order.is_completed = True
                order.completed_at = now
                order.status = 'hold'
                order.save()
        except Exception as e:
            print("[complete_group error]", e)

    return redirect('ice_view')


def get_grouped_active_orders():
    """未完了注文をグループごとにまとめて返す"""
    from collections import defaultdict
    from .models import Order
    
    grouped = defaultdict(list)
    now_time = timezone.now()
    
    active_orders = Order.objects.filter(is_completed=False).order_by('timestamp')
    for order in active_orders:
        delta = now_time - order.timestamp
        order.elapsed_minutes = int(delta.total_seconds() // 60)
        grouped[order.group_id].append(order)
    
    return grouped


def get_grouped_completed_orders():
    """完了注文をグループごとにまとめて返す"""
    completed_orders = Order.objects.filter(is_completed=True).order_by('-completed_at')
    grouped = defaultdict(list)
    
    for order in completed_orders:
        grouped[order.group_id].append(order)
    
    return grouped


@csrf_protect
def delete_group(request, group_id):
    """指定グループの注文を削除"""
    if request.method == 'POST':
        Order.objects.filter(group_id=group_id).delete()

    return redirect('ice_view')


@csrf_protect
def delete_group_from_deshap(request, group_id):
    """デシャップ画面から指定グループの注文を削除"""
    if request.method == 'POST':
        Order.objects.filter(group_id=group_id).delete()

    return redirect('deshap')


def order_detail(request, order_id):
    """注文詳細画面を表示"""
    if not request.session.get('logged_in'):
        return redirect('login')
    
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'ice/detail.html', {'order': order})


def delete_temp_ice(request, index):
    """仮注文リストから指定インデックスの注文を削除"""
    temp_ice = request.session.get('temp_ice', [])
    if 0 <= index < len(temp_ice):
        del temp_ice[index]
        request.session['temp_ice'] = temp_ice
        request.session.modified = True

    return redirect('register_view')


def deshap_view(request):
    """デシャップ画面を表示"""
    _update_hold_status()
    now = timezone.now()

    grouped_orders = _group_orders_by_id(Order.objects.order_by('timestamp'))
    active_orders, completed_orders = _separate_active_completed(grouped_orders, now)

    active_count = len(active_orders)
    active_order_total = _count_active_order_items(active_orders)
    newly_created_group_ids = _find_recent_groups(grouped_orders, reference_time=now)
    pudding_counts_active_by_group = _count_pudding_by_group(active_orders)
    pudding_counts_completed_by_group = _count_pudding_by_group(completed_orders)

    context = {
        'grouped_orders': active_orders,
        'completed_orders': completed_orders,
        'now': now,
        'active_count': active_count,
        'active_order_total': active_order_total,
        'newly_created_group_ids': newly_created_group_ids,
        'pudding_counts_active_by_group': pudding_counts_active_by_group,
        'pudding_counts_completed_by_group': pudding_counts_completed_by_group,
    }

    return render(request, 'ice/deshap.html', context)


def delete_all_pudding(request):
    """仮注文リストからアフォガードプリンを全て削除"""
    temp_ice = request.session.get('temp_ice', [])
    temp_ice = [item for item in temp_ice if not item.get('is_pudding')]
    request.session['temp_ice'] = temp_ice
    request.session.modified = True
    
    return HttpResponse("ok")


@csrf_exempt
def update_status(request, group_id, new_status):
    """指定グループの状態を更新"""
    if request.method == 'POST':
        Order.objects.filter(group_id=group_id).update(status=new_status)

    return redirect('deshap')


def health_check(request):
    """ヘルスチェック"""
    return HttpResponse("OK")


def api_active_count(request):
    """未完了オーダー数を返すAPI"""
    from .models import Order
    active_count = Order.objects.filter(is_completed=False).count()
    return JsonResponse({'active_count': active_count})

