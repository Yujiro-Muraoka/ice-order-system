#!/usr/bin/env python
"""
cafeMuji - カフェ注文管理システム
Djangoの管理コマンド実行用スクリプト

このファイルは、Djangoプロジェクトの管理タスク（サーバー起動、マイグレーション、コマンド実行など）
を実行するためのエントリーポイントです。

使用方法:
    python manage.py runserver     # 開発サーバー起動
    python manage.py makemigrations # マイグレーションファイル作成
    python manage.py migrate       # データベースマイグレーション実行
    python manage.py createsuperuser # 管理者ユーザー作成
"""
import os
import sys


def main():
    """
    Django管理コマンドのメイン実行関数
    
    この関数は以下の処理を行います：
    1. Django設定モジュールの指定（config.settings）
    2. Djangoの管理コマンド実行機能のインポート
    3. コマンドライン引数に基づく管理タスクの実行
    
    Raises:
        ImportError: Djangoがインストールされていない場合
    """
    # Django設定モジュールを環境変数に設定
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    
    try:
        # Djangoの管理コマンド実行機能をインポート
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        # Djangoがインストールされていない場合のエラーメッセージ
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    
    # コマンドライン引数に基づいてDjango管理コマンドを実行
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    # このファイルが直接実行された場合のみmain関数を呼び出し
    main()
