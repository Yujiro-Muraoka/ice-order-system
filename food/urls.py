"""
cafeMuji - フード注文管理システム
URLルーティング設定

このファイルは、フード注文システムのURLパスとビュー関数の対応を定義します。
各URLパターンは、特定の機能に対応するビュー関数にリクエストを振り分けます。

URL構造（/food/プレフィックスの下）:
- /food/register/              → フード注文登録画面
- /food/add_temp_food/         → 仮注文追加処理
- /food/kitchen/               → キッチン画面
- /food/complete_group/<id>/   → 注文完了処理
- /food/delete_temp_food/<i>/  → 仮注文削除処理
- /food/delete_all_temp_food/  → 全仮注文削除処理
- /food/submit_order_group/    → 本注文確定処理
"""

from django.urls import path
from . import views

# フード注文システムのURLパターン定義
urlpatterns = [
    # フード注文登録画面（レジ担当者用）
    # メニュー選択、数量指定、仮注文管理、本注文確定
    path('register/', views.food_register, name='food_register'),
    
    # 仮注文追加処理（POST専用）
    # 選択したメニュー・数量・店内/テイクアウトを仮注文リストに追加
    path('add_temp_food/', views.add_temp_food, name='add_temp_food'),
    
    # キッチン画面（キッチン担当者用）
    # 未完了注文の一覧表示、完了済み注文の表示（30秒間）
    path('kitchen/', views.food_kitchen, name='food_kitchen'),
    
    # 注文完了処理（POST専用）
    # 指定されたグループIDの注文を一括で完了状態に更新
    # group_id: 完了にする注文グループのID
    path('complete_group/<str:group_id>/', views.complete_food_group, name='complete_food_group'),
    
    # 仮注文削除処理（POST専用）
    # 指定されたインデックスの仮注文を削除
    # index: 削除する仮注文のインデックス（0から開始）
    path('delete_temp_food/<int:index>/', views.delete_temp_food, name='delete_temp_food'),
    
    # 全仮注文削除処理（POST専用）
    # セッション内の仮注文リストを全てクリア
    path('delete_all_temp_food/', views.delete_all_temp_food, name='delete_all_temp_food'),
    
    # 本注文確定処理（POST専用）
    # 仮注文をデータベースに保存し、キッチンに送信
    # クリップ情報と備考も同時に保存
    path('submit_order_group/', views.submit_order_group, name='submit_order_group'),
]
