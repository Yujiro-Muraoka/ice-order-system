from django.contrib import admin
from .models import Order

# Register your models here.
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """アイスクリーム注文の管理画面設定"""
    list_display = ['group_id', 'size', 'flavor1', 'flavor2', 'clip_color', 'clip_number', 'status', 'is_completed', 'timestamp']
    list_filter = ['status', 'is_completed', 'clip_color', 'size', 'container']
    search_fields = ['group_id', 'note']
    ordering = ['-timestamp']
