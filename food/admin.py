"""
cafeMuji - フード注文管理システム
Django管理画面設定

このファイルは、Django管理画面でのフード注文データの表示・編集・管理方法を定義します。
管理者はこの画面を通じて、注文データの確認、編集、削除ができます。

主な機能：
- 注文一覧の表示（メニュー、数量、クリップ情報、状態等）
- 注文の検索・フィルタリング
- 注文状態の編集
- 注文データの削除
"""

from django.contrib import admin
from .models import FoodOrder


@admin.register(FoodOrder)
class FoodOrderAdmin(admin.ModelAdmin):
    """
    フード注文の管理画面設定クラス
    
    このクラスは、Django管理画面でのFoodOrderモデルの表示方法を定義します。
    管理者が注文データを効率的に管理できるよう、適切な表示項目と
    フィルタリング機能を設定しています。
    """
    
    # 一覧画面で表示する項目（左から順番に表示）
    list_display = [
        'menu',           # メニュー名
        'quantity',       # 数量
        'clip_color',     # クリップ色
        'clip_number',    # クリップ番号
        'group_id',       # グループID
        'status',         # 注文状態
        'is_completed',   # 完了フラグ
        'timestamp'       # 受注時刻
    ]
    
    # フィルタリング用の項目（右サイドバーに表示）
    list_filter = [
        'status',         # 注文状態でフィルタ（ok/stop）
        'is_completed',   # 完了フラグでフィルタ（True/False）
        'clip_color',     # クリップ色でフィルタ（yellow/white）
        'menu'            # メニューでフィルタ（からあげ丼/ルーロー飯）
    ]
    
    # 検索対象の項目（検索ボックスで検索可能）
    search_fields = [
        'group_id',       # グループIDで検索
        'note'            # 備考欄で検索
    ]
    
    # 編集不可の項目（自動設定される項目）
    readonly_fields = [
        'timestamp',      # 受注時刻（自動設定）
        'completed_at'    # 完了時刻（完了時に自動設定）
    ]
    
    # デフォルトの並び順（新しい注文から表示）
    ordering = ['-timestamp']
