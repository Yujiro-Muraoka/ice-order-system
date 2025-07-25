from django.shortcuts import render, redirect
from food.models import FoodOrder
import time


def mobile_order_entry(request):
    """
    モバイル注文画面を表示
    """
    return render(request, 'mobile/mobile_order.html', {
        'quantity_range': range(1, 6),
        'clip_numbers': range(1, 17),
    })


def submit_mobile_order(request):
    """
    モバイル注文を処理
    """
    if request.method == 'POST':
        menu = request.POST.get('menu')
        quantity_str = request.POST.get('quantity')
        clip_color = request.POST.get('clip_color')
        clip_number_str = request.POST.get('clip_number')
        note = request.POST.get('note', '')
        
        # 入力チェック
        if not all([menu, quantity_str, clip_color, clip_number_str]):
            return redirect('mobile_order')
        
        try:
            quantity = int(quantity_str)
            clip_number = int(clip_number_str)
        except (ValueError, TypeError):
            return redirect('mobile_order')
        
        group_id = f"{clip_color}-{clip_number}-{int(time.time() * 1000)}"
        
        for _ in range(quantity):
            FoodOrder.objects.create(
                menu=menu,
                quantity=1,
                clip_color=clip_color,
                clip_number=clip_number,
                group_id=group_id,
                status='ok',
                note=note,
            )
        
        return redirect('mobile_order_complete')
    
    return redirect('mobile_order')


def mobile_order_complete(request):
    """
    モバイル注文完了画面を表示
    """
    return render(request, 'mobile/mobile_complete.html') 