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
    """
    now = timezone.now()
    grouped_orders = defaultdict(list)
    
    # 全注文をグループIDでグループ化
    all_orders = FoodOrder.objects.all().order_by('timestamp')
    for order in all_orders:
        grouped_orders[order.group_id].append(order)
    
    # 未完了・完了注文を分離
    active_orders = {}
    completed_orders = {}
    
    for group_id, orders in grouped_orders.items():
        # グループ内の全注文が完了しているかチェック
        if all(o.is_completed for o in orders):
            # 完了時刻の最新を取得
            latest = max((o.completed_at for o in orders if o.completed_at), default=None)
            # 30秒以内に完了した注文のみ表示
            if latest and now - latest <= timezone.timedelta(seconds=30):
                completed_orders[group_id] = orders
        else:
            # 未完了の注文はactive_ordersに追加
            active_orders[group_id] = orders
    
    # テンプレートに渡すデータを準備
    context = {
        'active_orders': active_orders,
        'completed_orders': completed_orders,
        'now': now,
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
            quantity=item['quantity'],
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
