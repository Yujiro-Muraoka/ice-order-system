from django.shortcuts import render, redirect
from .models import FoodOrder
import time
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from collections import defaultdict


def food_register(request):
    temp_food = request.session.get('temp_food', [])

    if request.method == "POST":
        clip_color = request.POST.get('clip_color')
        clip_number = request.POST.get('clip_number')
        note = request.POST.get('note', '')
        if not clip_color or not clip_number:
            return redirect('food_register')  # 安全にリダイレクト
        group_id = f"{clip_color}-{clip_number}-{int(time.time() * 1000)}"
        for item in temp_food:
            FoodOrder.objects.create(
                menu=item['menu'],
                quantity=item['quantity'],
                clip_color=clip_color,
                clip_number=int(clip_number),
                group_id=group_id,
                status='ok',
                note=note
            )
        request.session['temp_food'] = []
        return redirect('food_register')

    # GET時はテンプレートを返す（ここが今抜けてる）
    return render(request, 'food/food_register.html', {
        'temp_food': temp_food,
        'quantity_range': range(1, 6),
        'clip_numbers': range(1, 17),  # テンプレートで番号生成に使用
    })


@csrf_exempt
def add_temp_food(request):
    if request.method == "POST":
        menu = request.POST['menu']
        quantity = int(request.POST['quantity'])
        temp_food = request.session.get('temp_food', [])
        temp_food.append({'menu': menu, 'quantity': quantity})
        request.session['temp_food'] = temp_food
        return redirect('food_register')
    

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