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
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from collections import defaultdict, Counter
from .models import FoodOrder
import time


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
        pudding_count_active: 未完了のアフォガードプリン数
        pudding_count_completed: 完了済みのアフォガードプリン数
        active_count: 未完了注文数
    """
    from ice.models import Order as IceOrder

    now = timezone.now()

    # Food orders
    all_food = FoodOrder.objects.all().order_by('timestamp')
    for o in all_food:
        o.elapsed_seconds = int((now - o.timestamp).total_seconds())
        o.elapsed_minutes = o.elapsed_seconds // 60
    food_grouped = _group_by_group_id(all_food)
    active_orders, completed_orders = _split_active_completed(food_grouped, now)

    # Ice orders for pudding counts only
    ice_all = IceOrder.objects.order_by('timestamp')
    ice_grouped = _group_by_group_id(ice_all)
    ice_active, ice_completed = _split_active_completed(ice_grouped, now)
    
    # アイスクリームのアフォガードプリン数を計算
    ice_active_orders = {}
    ice_completed_orders = {}
    ice_all_orders = IceOrder.objects.order_by('timestamp')
    ice_grouped_orders = defaultdict(list)
    
    for order in ice_all_orders:
        ice_grouped_orders[order.group_id].append(order)
    
    for group_id, orders in ice_grouped_orders.items():
        if all(o.is_completed for o in orders):
            latest = max((o.completed_at for o in orders if o.completed_at), default=None)
            if latest and now - latest <= timezone.timedelta(seconds=30):
                ice_completed_orders[group_id] = orders
        else:
            ice_active_orders[group_id] = orders
    
    # プリン数を計算
    pudding_count_active = sum(
        sum(1 for o in orders if getattr(o, 'is_pudding', False))
        for orders in ice_active.values()
    )
    pudding_count_completed = sum(
        sum(1 for o in orders if getattr(o, 'is_pudding', False))
        for orders in ice_completed.values()
    )
    
    # キッチン画面ではグループ単位のプリン個数までは不要なので、総数だけコンテキストに渡す。
    active_count = len(active_orders)
    active_order_total = sum(
        order.quantity
        for orders in active_orders.values()
        for order in orders
        if not order.is_completed
    )

    # アイス画面と同様に、新規注文と同時に別注文が完了して件数が差し引きゼロになるケースでも
    # 自動更新が発火するよう合成値を導入する。
    # 件数が同じでも最新IDが増えれば refresh_value が必ず増加する。
    latest_order_id = FoodOrder.objects.order_by('-id').values_list('id', flat=True).first() or 0
    refresh_value = active_order_total * 1_000_000 + latest_order_id
    
    # テンプレートに渡すデータを準備
    context = {
        'active_orders': active_orders,
        'completed_orders': completed_orders,
        'now': now,
        'pudding_count_active': pudding_count_active,
        'pudding_count_completed': pudding_count_completed,
        'active_count': active_count,
        'active_order_total': active_order_total,
        'refresh_value': refresh_value,
    }
    
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
    return redirect('food_kitchen')


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
