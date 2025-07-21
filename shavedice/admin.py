from django.contrib import admin
from .models import ShavedIceOrder

# Register your models here.
@admin.register(ShavedIceOrder)
class ShavedIceOrderAdmin(admin.ModelAdmin):
    """かき氷注文の管理画面設定"""
    list_display = ['flavor', 'clip_color', 'clip_number', 'is_completed', 'timestamp']
    list_filter = ['is_completed', 'clip_color', 'flavor']
    search_fields = ['note']
    readonly_fields = ['timestamp', 'completed_at']
    ordering = ['-timestamp']
