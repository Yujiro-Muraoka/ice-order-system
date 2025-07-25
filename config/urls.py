"""
cafeMuji - カフェ注文管理システム
メインURLルーティング設定

このファイルは、cafeMujiプロジェクト全体のURLパスを管理します。
各アプリケーション（ice, food, shavedice）のURLを統合し、
適切なアプリケーションにリクエストを振り分けます。

URL構造:
- /admin/          → Django管理画面
- /                → アイスクリーム注文システム（メイン）
- /food/           → フード注文システム
- /shavedice/      → かき氷注文システム
"""

from django.contrib import admin
from django.urls import path, include

# プロジェクト全体のURLパターン定義
urlpatterns = [
    # Django管理画面（データベース管理用）
    path('admin/', admin.site.urls),
    
    # アイスクリーム注文システム（メインアプリケーション）
    # ルートパス（/）にアクセスした場合、iceアプリのURLに振り分け
    path('', include('ice.urls')),
    
    # フード注文システム
    # /food/で始まるURLをfoodアプリのURLに振り分け
    path('food/', include('food.urls')),
    
    # かき氷注文システム
    # /shavedice/で始まるURLをshavediceアプリのURLに振り分け
    path('shavedice/', include('shavedice.urls')),

    # モバイルオーダーシステム
    # /mobile/で始まるURLをmobileアプリのURLに振り分け
    path('mobile/', include('mobile.urls')),
]
