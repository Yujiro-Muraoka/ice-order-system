from django.shortcuts import render, redirect
from .models import FoodOrder
import time
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from collections import defaultdict
from django.shortcuts import redirect
from collections import Counter


def food_register(request):
    # セッションから仮オーダーを取得（なければ空）
    temp_food = request.session.get('temp_food', [])

    # メニューごとの合計数を計算
    counts = Counter()
    for item in temp_food:
        counts[item['menu']] += item['quantity']

    # クリップ情報も取得（なければ空文字）
    clip_color = request.session.get('clip_color', '')
    clip_number = request.session.get('clip_number', '')

    return render(request, 'food/food_register.html', {
        'temp_food': temp_food,
        'karaage_count': counts.get('からあげ丼', 0),
        'lurowfan_count': counts.get('ルーロー飯', 0),
        'clip_color': clip_color,
        'clip_number': clip_number,
    })


@csrf_exempt
def add_temp_food(request):
    if request.method == "POST":
        menu = request.POST.get('menu')
        quantity = int(request.POST.get('quantity', 1))

        # セッションから仮オーダー取得（なければ空配列）
        temp_food = request.session.get('temp_food', [])

        # 新しい注文を追加
        temp_food.append({'menu': menu, 'quantity': quantity})

        # セッションに再代入 & 明示的に変更通知
        request.session['temp_food'] = temp_food
        request.session.modified = True

    return redirect('food_register')  # ← urls.py に登録されている 'food_register' 名前付きルートへ戻す

def food_kitchen(request):
    now = timezone.now()
    grouped_orders = defaultdict(list)

    all_orders = FoodOrder.objects.all().order_by('timestamp')
    for order in all_orders:
        grouped_orders[order.group_id].append(order)

    active_orders = {}
    completed_orders = {}

    for group_id, orders in grouped_orders.items():
        if all(o.is_completed for o in orders):
            latest = max((o.completed_at for o in orders if o.completed_at), default=None)
            if latest and now - latest <= timezone.timedelta(seconds=30):
                completed_orders[group_id] = orders
        else:
            active_orders[group_id] = orders

    return render(request, 'food/food_kitchen.html', {
        'active_orders': active_orders,
        'completed_orders': completed_orders,
        'now': now,
    })


@csrf_exempt
def complete_food_group(request, group_id):
    if request.method == 'POST':
        now = timezone.now()
        FoodOrder.objects.filter(group_id=group_id, is_completed=False).update(
            is_completed=True, completed_at=now
        )
    return redirect('food_kitchen')

@csrf_exempt
def delete_temp_food(request, index):
    if 'temp_food' in request.session:
        temp_food = request.session['temp_food']
        if 0 <= index < len(temp_food):
            del temp_food[index]
            request.session['temp_food'] = temp_food
            request.session.modified = True
    return redirect('food_register')

@csrf_exempt
def delete_all_temp_food(request):
    request.session['temp_food'] = []
    request.session.modified = True
    return redirect('food_register')

@csrf_exempt
def submit_order_group(request):
    if request.method == "POST":
        temp_food = request.session.get('temp_food', [])
        clip_color = request.POST.get('clip_color')
        clip_number = request.POST.get('clip_number')
        note = request.POST.get('note', '')

        if not temp_food or not clip_color or not clip_number:
            return redirect('food_register')  # 入力不備があれば戻す

        # group_id はタイムスタンプベース
        group_id = str(int(time.time()))

        for item in temp_food:
            FoodOrder.objects.create(
                menu=item['menu'],
                quantity=item['quantity'],
                clip_color=clip_color,
                clip_number=clip_number,
                note=note,
                group_id=group_id,
                is_completed=False
            )

        # セッション初期化
        request.session['temp_food'] = []
        request.session['clip_color'] = ''
        request.session['clip_number'] = ''
        request.session.modified = True

        return redirect('food_register')  # 完了後は同じ画面に戻す（必要なら success メッセージ可）
