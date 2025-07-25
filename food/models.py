"""
cafeMuji - フード注文管理システム
データベースモデル定義

このファイルは、フード注文に関するデータベーステーブルの構造を定義します。
FoodOrderモデルは、カフェでのフード注文（からあげ丼、ルーロー飯など）の
受注から完了までの全プロセスを管理します。

主な機能：
- 注文内容の保存（メニュー、数量、店内/テイクアウト）
- クリップ情報の管理（色、番号）
- 注文グループの管理（複数商品の一括注文）
- 注文状態の追跡（受注→作成中→完了）
- 完了時刻の記録
"""

from django.db import models


class FoodOrder(models.Model):
    """
    フード注文を管理するデータベースモデル
    
    このモデルは、カフェでのフード注文の全情報を保存します。
    注文から完了まで、キッチンでの作業管理に必要な情報を
    包括的に管理します。
    """
    
    # ==================== 注文内容 ====================
    
    menu = models.CharField(
        max_length=20,
        verbose_name="メニュー名",
        help_text="注文されたフードのメニュー名（例：からあげ丼、ルーロー飯）"
    )  # 注文されたメニュー名を保存
    
    quantity = models.PositiveIntegerField(
        default=1,
        verbose_name="数量",
        help_text="注文数量（1以上の整数）"
    )  # 注文の数量を保存
    
    eat_in = models.BooleanField(
        default=True,
        verbose_name="店内飲食",
        help_text="True=店内飲食、False=テイクアウト"
    )  # 店内飲食かテイクアウトかを判別
    
    # ==================== クリップ情報 ====================
    
    clip_color = models.CharField(
        max_length=10,
        verbose_name="クリップ色",
        help_text="オーダー表のクリップの色（yellow, white等）"
    )  # クリップの色を保存
    
    clip_number = models.IntegerField(
        verbose_name="クリップ番号",
        help_text="オーダー表のクリップの番号（1-16等）"
    )  # クリップの番号を保存
    
    # ==================== 注文管理 ====================
    
    group_id = models.CharField(
        max_length=50,
        verbose_name="グループID",
        help_text="同一注文グループを識別するID（複数商品の一括注文用）"
    )  # 複数商品をまとめるグループID
    
    status = models.CharField(
        max_length=10,
        default='ok',
        verbose_name="注文状態",
        help_text="注文の現在の状態（ok=作成OK、stop=STOP中）"
    )  # 注文の進行状況を管理
    
    is_completed = models.BooleanField(
        default=False,
        verbose_name="完了フラグ",
        help_text="注文が完了したかどうかのフラグ"
    )  # 注文が完了したかどうか
    
    # ==================== 時刻管理 ====================
    
    timestamp = models.DateTimeField(
        auto_now_add=True,
        verbose_name="受注時刻",
        help_text="注文を受けた時刻（自動設定）"
    )  # 注文を受けた時刻（自動記録）
    
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="完了時刻",
        help_text="注文が完了した時刻（完了時に設定）"
    )  # 注文が完了した時刻
    
    # ==================== その他 ====================
    
    note = models.TextField(
        blank=True,
        default="",
        verbose_name="備考",
        help_text="注文に関する特記事項や要望"
    )  # 備考欄（特記事項や要望など）

    def __str__(self):
        """
        管理画面やデバッグ時の表示用文字列
        
        Returns:
            str: "メニュー名 ×数量 [グループID]" の形式
        """
        return f"{self.menu} ×{self.quantity} [{self.group_id}]"

    class Meta:
        """
        モデルのメタ情報設定
        - 管理画面での表示名やデフォルトの並び順を指定
        """
        verbose_name = "フード注文"           # 管理画面での単数表示名
        verbose_name_plural = "フード注文"    # 管理画面での複数表示名
        ordering = ['-timestamp']            # デフォルトの並び順（新しい順）
