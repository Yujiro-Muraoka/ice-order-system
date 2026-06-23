"""
cafeMuji - フード注文管理システム
ビュー（画面表示・処理）定義

このファイルは、フード注文システムの画面表示と処理ロジックを定義します。
主な機能：
- 注文登録画面の表示
- 仮注文の追加・削除・管理
- キッチン画面での注文一覧表示
- 注文の完了処理
- 本注文のデータベース保存

各ビュー関数は、ユーザーのリクエストを受け取り、
適切な処理を行ってレスポンスを返します。
"""

from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from collections import defaultdict, Counter
from django.db.models import Count, Sum, Max, Q
from .models import FoodOrder
import time

FOOD_CATEGORIES = [
    {
        'name': 'パンケーキ',
        'items': ['パンケーキ'],
    },
    {
        'name': '麺・フォー',
        'items': ['チキンのフォー', 'ソトアヤムのフォー', 'ルーロー麺'],
    },
    {
        'name': 'その他',
        'items': [
            'ハンバーグ',
            'からあげ',
            'ルーロー飯',
            'ライスバーガー',
            'バターチキンカレー',
            'いわし梅カレー',
        ],
    },
]

FOOD_MENU_NAMES = {
    menu
    for category in FOOD_CATEGORIES
    for menu in category['items']
}


def _split_active_completed(grouped, now):
    active = {}
    completed = {}
    for gid, ords in grouped.items():
        if all(o.is_completed for o in ords):
            latest = max((o.completed_at for o in ords if o.completed_at), default=None)
            if latest and now - latest <= timezone.timedelta(seconds=30):
                completed[gid] = ords
        else:
            active[gid] = ords
    return active, completed


def _group_by_group_id(queryset):
    grouped = defaultdict(list)
    for obj in queryset:
        grouped[obj.group_id].append(obj)
    return grouped


def _calculate_food_refresh_metrics():
    aggregates = FoodOrder.objects.aggregate(
        active_items=Sum('quantity', filter=Q(is_completed=False)),
        latest_id=Max('id'),
        active_stop_groups=Count(
            'group_id',
            filter=Q(is_completed=False, status='stop'),
            distinct=True,
        ),
    )
    active_order_total = aggregates['active_items'] or 0
    latest_order_id = aggregates['latest_id'] or 0
    active_stop_groups = aggregates['active_stop_groups'] or 0
    refresh_value = f"{active_order_total}:{latest_order_id}:{active_stop_groups}"
    return {
        'active_order_total': active_order_total,
        'latest_order_id': latest_order_id,
        'active_stop_groups': active_stop_groups,
        'refresh_value': refresh_value,
    }


def _get_food_order_context():
    now = timezone.localtime()
    all_food = FoodOrder.objects.all().order_by('timestamp')
    for order in all_food:
        order.elapsed_seconds = int((now - order.timestamp).total_seconds())
        order.elapsed_minutes = order.elapsed_seconds // 60

    grouped = _group_by_group_id(all_food)
    active_orders, completed_orders = _split_active_completed(grouped, now)
    metrics = _calculate_food_refresh_metrics()

    return {
        'active_orders': active_orders,
        'completed_orders': completed_orders,
        'now': now,
        'active_count': len(active_orders),
        'active_order_total': metrics['active_order_total'],
        'latest_order_id': metrics['latest_order_id'],
        'refresh_value': metrics['refresh_value'],
    }


def _food_orders_partial(context, request, template_name='food/_food_orders.html'):
    return render_to_string(template_name, context, request=request)


def food_register(request):
    """
    フード注文登録画面を表示するビュー
    
    この画面では、レジ担当者がフード注文を受け付けます。
    仮注文の追加・削除・確認ができ、最終的に本注文として確定できます。
    
    Args:
        request: HTTPリクエストオブジェクト
        
    Returns:
        HttpResponse: フード注文登録画面のHTMLレスポンス
        
    Context:
        temp_food: 現在の仮注文リスト
        karaage_count: からあげ丼の合計数量
        lurowfan_count: ルーロー飯の合計数量
        clip_color: 選択されたクリップの色
        clip_number: 選択されたクリップの番号
    """
    # セッションから仮注文リストを取得
    temp_food = request.session.get('temp_food', [])
    
    # メニューごとの合計数を計算（表示用）
    counts = Counter()
    for item in temp_food:
        counts[item['menu']] += item['quantity']
    
    # セッションからクリップ情報を取得
    clip_color = request.session.get('clip_color', '')
    clip_number = request.session.get('clip_number', '')
    
    # テンプレートに渡すデータを準備
    context = {
        'temp_food': temp_food,
        'food_categories': FOOD_CATEGORIES,
        'karaage_count': counts.get('からあげ丼', 0),
        'lurowfan_count': counts.get('ルーロー飯', 0),
        'clip_color': clip_color,
        'clip_number': clip_number,
    }
    
    return render(request, 'food/food_register.html', context)


@csrf_exempt
def add_temp_food(request):
    """
    仮注文をセッションに追加するビュー
    
    レジ担当者が選択したメニュー・数量・店内/テイクアウトを
    セッション内の仮注文リストに追加します。
    
    Args:
        request: HTTPリクエストオブジェクト（POSTメソッド）
        
    Returns:
        HttpResponse: フード注文登録画面へのリダイレクト
        
    POST Parameters:
        menu: メニュー名（からあげ丼、ルーロー飯）
        quantity: 数量（文字列）
        eat_in: 店内/テイクアウト（'0'=テイクアウト、'1'=店内）
    """
    # POSTメソッド以外は注文画面にリダイレクト
    if request.method != "POST":
        return redirect('food_register')
    
    # POSTデータから注文情報を取得
    menu = request.POST.get('menu')
    quantity_str = request.POST.get('quantity', '1')
    eat_in_str = request.POST.get('eat_in')
    
    # 入力値の妥当性チェック
    if not menu or eat_in_str not in ['0', '1']:
        return redirect('food_register')
    if menu not in FOOD_MENU_NAMES:
        return redirect('food_register')
    
    # 数量を整数に変換（エラー時は1に設定）
    try:
        quantity = int(quantity_str)
        if quantity <= 0:
            quantity = 1
    except (ValueError, TypeError):
        quantity = 1
    
    # 店内/テイクアウトをブール値に変換
    eat_in = True if eat_in_str == '1' else False
    
    # セッションから仮注文リストを取得して新しい注文を追加
    temp_food = request.session.get('temp_food', [])
    temp_food.append({'menu': menu, 'quantity': quantity, 'eat_in': eat_in})
    
    # セッションを更新
    request.session['temp_food'] = temp_food
    request.session.modified = True
    
    return redirect('food_register')


def food_kitchen(request):
    """
    キッチン画面：注文をグループごとに集計して表示するビュー
    
    キッチン担当者が注文の状況を確認できる画面です。
    未完了の注文と完了済みの注文（30秒以内）を分けて表示します。
    
    Args:
        request: HTTPリクエストオブジェクト
        
    Returns:
        HttpResponse: キッチン画面のHTMLレスポンス
        
    Context:
        active_orders: 未完了の注文グループ
        completed_orders: 完了済みの注文グループ（30秒以内）
        now: 現在時刻
        active_count: 未完了注文数
    """
    context = _get_food_order_context()
    now = context['now']
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('format') == 'json':
        return JsonResponse({
            'value': context['refresh_value'],
            'refresh_value': context['refresh_value'],
            'active_order_total': context['active_order_total'],
            'active_count': context['active_count'],
            'latest_order_id': context['latest_order_id'],
            'html': _food_orders_partial(context, request),
            'timestamp': now.isoformat(),
        })
    
    return render(request, 'food/food_kitchen.html', context)


@csrf_exempt
def complete_food_group(request, group_id):
    """
    指定グループの注文を一括完了にするビュー
    
    キッチン担当者が注文の作成を完了した際に呼び出されます。
    指定されたグループIDの全注文を完了状態に更新します。
    
    Args:
        request: HTTPリクエストオブジェクト（POSTメソッド）
        group_id: 完了にする注文グループのID
        
    Returns:
        HttpResponse: キッチン画面へのリダイレクト
    """
    if request.method == 'POST':
        now = timezone.now()
        # 指定グループの未完了注文を一括で完了状態に更新
        FoodOrder.objects.filter(
            group_id=group_id, 
            is_completed=False
        ).update(is_completed=True, completed_at=now)
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'ok'})
    
    return redirect('food_kitchen')


@csrf_exempt
def complete_food_order(request, order_id):
    """
    指定IDの注文を個別に完了にするビュー
    """
    if request.method == 'POST':
        now = timezone.now()
        try:
            order = FoodOrder.objects.get(id=order_id)
            order.is_completed = True
            order.completed_at = now
            order.save()
        except FoodOrder.DoesNotExist:
            pass
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'ok'})
    return redirect('food_kitchen')


@csrf_exempt
def food_update_status(request, group_id, new_status):
    """フードデシャップ画面からグループの状態を更新"""
    if request.method == 'POST' and new_status in {'ok', 'stop'}:
        FoodOrder.objects.filter(group_id=group_id, is_completed=False).update(
            status=new_status
        )
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'ok'})
    return redirect('food_deshap')


def food_deshap_view(request):
    """フードデシャップ担当画面"""
    context = _get_food_order_context()
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('format') == 'json':
        return JsonResponse({
            'value': context['refresh_value'],
            'refresh_value': context['refresh_value'],
            'active_order_total': context['active_order_total'],
            'active_count': context['active_count'],
            'latest_order_id': context['latest_order_id'],
            'html': _food_orders_partial(context, request, 'food/_food_deshap_orders.html'),
            'timestamp': context['now'].isoformat(),
        })
    return render(request, "food/food_deshap.html", context)


def food_wait_time_view(request):
    """
    フードの未完了商品数から待ち時間（1商品1分）を計算して表示するビュー
    """
    uncompleted_count = FoodOrder.objects.filter(is_completed=False).aggregate(
        total=Sum('quantity')
    )['total'] or 0
    wait_minutes = uncompleted_count
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
    return render(request, 'food/food_wait_time.html', context)


@csrf_exempt
def delete_temp_food(request, index):
    """
    仮注文リストから指定インデックスの注文を削除するビュー
    
    レジ担当者が間違って追加した仮注文を削除できます。
    
    Args:
        request: HTTPリクエストオブジェクト（POSTメソッド）
        index: 削除する注文のインデックス
        
    Returns:
        HttpResponse: フード注文登録画面へのリダイレクト
    """
    if 'temp_food' in request.session:
        temp_food = request.session['temp_food']
        # インデックスの範囲チェック
        if 0 <= index < len(temp_food):
            # 指定インデックスの注文を削除
            del temp_food[index]
            request.session['temp_food'] = temp_food
            request.session.modified = True
    
    return redirect('food_register')


@csrf_exempt
def delete_all_temp_food(request):
    """
    仮注文リストを全て削除するビュー
    
    レジ担当者が仮注文を全てクリアしたい場合に使用します。
    
    Args:
        request: HTTPリクエストオブジェクト（POSTメソッド）
        
    Returns:
        HttpResponse: フード注文登録画面へのリダイレクト
    """
    # セッションの仮注文リストを空にする
    request.session['temp_food'] = []
    request.session.modified = True
    return redirect('food_register')


@csrf_exempt
def submit_order_group(request):
    """
    仮注文を本注文としてデータベースに保存するビュー
    
    レジ担当者が仮注文を確定し、キッチンに送信する際に呼び出されます。
    セッション内の仮注文をデータベースに保存し、セッションをクリアします。
    
    Args:
        request: HTTPリクエストオブジェクト（POSTメソッド）
        
    Returns:
        HttpResponse: フード注文登録画面へのリダイレクト
        
    POST Parameters:
        clip_color: クリップの色
        clip_number: クリップの番号
        note: 備考欄
    """
    # POSTメソッド以外は注文画面にリダイレクト
    if request.method != "POST":
        return redirect('food_register')
    
    # セッションから仮注文リストを取得
    temp_food = request.session.get('temp_food', [])
    
    # POSTデータから注文情報を取得
    clip_color = request.POST.get('clip_color')
    clip_number_str = request.POST.get('clip_number')
    note = request.POST.get('note', '')
    
    # 入力値の妥当性チェック
    if not temp_food or not clip_color or not clip_number_str:
        return redirect('food_register')
    
    # クリップ番号を整数に変換
    try:
        clip_number = int(clip_number_str)
    except (ValueError, TypeError):
        return redirect('food_register')
    
    # グループIDを現在時刻で生成（一意性を保証）
    group_id = str(int(time.time()))

    has_stop = FoodOrder.objects.filter(is_completed=False, status='stop').exists()
    status = 'stop' if has_stop else 'ok'
    
    # 仮注文をデータベースに保存
    for item in temp_food:
        FoodOrder.objects.create(
            menu=item['menu'],
            quantity=item.get('quantity', 1),
            eat_in=item.get('eat_in', True),
            clip_color=clip_color,
            clip_number=clip_number,
            note=note,
            group_id=group_id,
            status=status,
            is_completed=False
        )
    
    # セッションを初期化（注文完了）
    request.session['temp_food'] = []
    request.session['clip_color'] = ''
    request.session['clip_number'] = ''
    request.session.modified = True
    
    return redirect('food_register')


# ==================== 監視・ヘルスチェック機能 ====================

from django.http import JsonResponse
from django.db import connection

def food_health_check(request):
    """
    フードシステムのヘルスチェック
    """
    del request
    try:
        # データベース接続確認
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM food_foodorder")
            total_orders = cursor.fetchone()[0]
        
        # 未完了注文数の取得
        pending_orders = FoodOrder.objects.filter(is_completed=False).count()
        
        # 今日の完了注文数
        today = timezone.now().date()
        completed_today = FoodOrder.objects.filter(
            is_completed=True,
            timestamp__date=today
        ).count()
        
        return JsonResponse({
            'status': 'healthy',
            'timestamp': timezone.now().isoformat(),
            'data': {
                'total_orders': total_orders,
                'pending_orders': pending_orders,
                'completed_today': completed_today
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'unhealthy',
            'error': str(e)
        }, status=503)


def food_statistics(request):
    """
    フード注文の統計情報
    """
    del request
    try:
        today = timezone.now().date()
        
        # 今日の統計
        today_orders = FoodOrder.objects.filter(timestamp__date=today)
        
        # メニュー別集計
        from django.db.models import Count
        menu_stats = today_orders.values('menu').annotate(
            count=Count('id')
        ).order_by('-count')
        
        return JsonResponse({
            'date': str(today),
            'total_orders': today_orders.count(),
            'completed_orders': today_orders.filter(is_completed=True).count(),
            'menu_statistics': list(menu_stats)
        })
        
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500)
