#!/usr/bin/env bash
# Render用のビルドスクリプト

set -o errexit  # エラーが発生した場合にスクリプトを終了

# 依存関係のインストール
pip install -r requirements.txt

# データベースマイグレーション
python manage.py migrate

# 静的ファイルの収集
python manage.py collectstatic --noinput