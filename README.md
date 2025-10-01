# cafeMuji 注文管理システム v2.0

![Django](https://img.shields.io/badge/Django-5.2.6-brightgreen)
![Python](https://img.shields.io/badge/Python-3.13.7-blue)
![DRF](https://img.shields.io/badge/DRF-3.14.0-orange)
![Tests](https://img.shields.io/badge/Tests-27%20passed-brightgreen)

## 📋 概要

cafe&meal MUJIの業務効率化を目的とした注文管理用Webアプリケーション。  
フード、アイスクリーム、かき氷の統合管理システムです。

## 🚀 v2.0 新機能

### ✨ 主要な強化項目
- **REST API**: 完全なCRUD操作対応
- **テストスイート**: 27個の包括的テスト
- **パフォーマンス最適化**: データベースインデックス追加
- **エラーハンドリング**: 包括的エラー処理とログ機能
- **監視機能**: システムヘルスチェックと統計
- **キャッシュシステム**: 応答時間向上

## 🛠️ 技術スタック

- **Backend**: Django 5.2.6, Python 3.13.7
- **API**: Django REST Framework 3.14.0
- **Database**: SQLite (PostgreSQL対応)
- **Cache**: Django LocMem Cache
- **Deployment**: Render.com
- **Testing**: Django Test Framework + Coverage

## 📦 インストール

### 1. リポジトリのクローン
```bash
git clone https://github.com/Yujiro-Muraoka/ice-order-system.git
cd ice-order-system
```

### 2. 仮想環境の設定
```bash
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# または
.venv\Scripts\activate     # Windows
```

### 3. 依存関係のインストール
```bash
pip install -r requirements.txt
```

### 4. データベースの設定
```bash
python manage.py migrate
```

### 5. 開発サーバーの起動
```bash
python manage.py runserver
```

## 🖥️ 主要機能

### 📱 Web UI
- **フード注文管理** (http://localhost:8000/food/)
- **アイスクリーム注文管理** (http://localhost:8000/)
- **かき氷注文管理** (http://localhost:8000/shavedice/)

### 🔌 REST API
- **API Root**: http://localhost:8000/api/
- **ヘルスチェック**: http://localhost:8000/api/health/
- **Swagger UI**: http://localhost:8000/api/ (DRF Browsable API)

### 📊 API エンドポイント例
```
GET    /api/food-orders/           # フード注文一覧
POST   /api/food-orders/           # 新規注文作成
GET    /api/food-orders/{id}/      # 注文詳細
POST   /api/food-orders/{id}/complete/  # 注文完了
GET    /api/food-orders/statistics/     # 統計情報
GET    /api/health/                     # ヘルスチェック
```

## 🧪 テスト

### テストの実行
```bash
# 全テスト実行
python manage.py test

# 特定アプリのテスト
python manage.py test food.tests

# 詳細出力
python manage.py test --verbosity=2
```

### カバレッジ測定
```bash
coverage run manage.py test
coverage report
coverage html
```

## 📈 パフォーマンス最適化

### データベースインデックス
- ステータス + 完了フラグ
- クリップ色 + 番号
- タイムスタンプ
- グループID
- メニュー + 完了フラグ

### キャッシュ設定
- **LocMem Cache**: 5分間キャッシュ
- **最大エントリ**: 1000件
- **自動削除**: 満杯時の1/3を削除

## 📊 システム監視

### ヘルスチェック
```bash
curl http://localhost:8000/api/health/
```

### 統計情報
```bash
curl http://localhost:8000/api/food-orders/statistics/
```

## 🚀 デプロイ

### Render.com
1. GitHubリポジトリを接続
2. 環境変数を設定
3. 自動デプロイを有効化

### 環境変数
```
DEBUG=False
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=.onrender.com
```

## 📚 技術資料

詳細な技術資料は `cafeMuji_技術資料/` ディレクトリ内：

- **システム概要説明書**: 全体像と特徴
- **技術仕様書**: 詳細な技術仕様
- **データベース設計書**: テーブル設計とER図
- **API仕様書**: REST API詳細仕様
- **テスト計画書**: テスト戦略と実装
- **デプロイ手順書**: 本番環境構築手順
- **運用マニュアル**: 日常運用とトラブルシューティング

## 🤝 コントリビューション

1. フォークする
2. フィーチャーブランチを作成 (`git checkout -b feature/AmazingFeature`)
3. 変更をコミット (`git commit -m 'Add some AmazingFeature'`)
4. ブランチにプッシュ (`git push origin feature/AmazingFeature`)
5. プルリクエストを作成

## 📄 ライセンス

このプロジェクトは MIT ライセンスの下で公開されています。

## 👨‍💻 開発者

**村岡 優次郎**
- GitHub: [@Yujiro-Muraoka](https://github.com/Yujiro-Muraoka)

## 🔄 バージョン履歴

詳細な更新内容は [`CHANGELOG.md`](./CHANGELOG.md) を参照してください。

| バージョン | 日付 | ハイライト |
| --- | --- | --- |
| v2.0.1 | 2025-10-01 | 互換性パッチ、アクセス制御調整、セッション安定化、psycopg2-binary 2.9.9 |
| v2.0.0 | 2025-09-30 | REST API・テストスイート・パフォーマンス/監視強化 |
| v1.0.0 | 2025-07-25 | 初回リリース、Web UI、Renderデプロイ |
