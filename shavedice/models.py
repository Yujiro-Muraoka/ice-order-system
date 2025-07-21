from django.db import models

# 注文状態の選択肢
ORDER_STATUS_CHOICES = [
    ('ok', 'アイス作成OK'),
    ('stop', 'アイス作成STOP'),
    ('hold', '保留（非表示待ち）'),
]

# クリップ色の選択肢
CLIP_COLOR_CHOICES = [
    ('yellow', '黄色'),
    ('white', '白色'),
]


class ShavedIceOrder(models.Model):
    """かき氷注文を管理するモデル"""
    
    FLAVOR_CHOICES = [
        ('抹茶', '抹茶'),
        ('いちご', 'いちご'),
        ('ゆず', 'ゆず'),
    ]
    
    flavor = models.CharField(max_length=50, choices=FLAVOR_CHOICES)  # フレーバー
    group_id = models.CharField(max_length=50, default='')  # グループID
    is_completed = models.BooleanField(default=False)  # 完了フラグ
    clip_color = models.CharField(
        max_length=10,
        choices=CLIP_COLOR_CHOICES,
        default='white'  # デフォルトで白色
    )  # クリップ色
    clip_number = models.IntegerField(default=0)  # クリップ番号（未指定時は0番）
    timestamp = models.DateTimeField(auto_now_add=True)  # 注文受付時刻
    completed_at = models.DateTimeField(null=True, blank=True)  # 完了時刻
    status = models.CharField(max_length=10, choices=ORDER_STATUS_CHOICES, default='ok')  # 注文状態
    is_auto_stopped = models.BooleanField(default=False)  # 自動STOPかどうか
    note = models.TextField(blank=True, null=True)  # 備考欄
    
    def __str__(self):
        """管理画面等での表示用"""
        return f"{self.flavor}（{self.note}）"

    class Meta:
        """メタ情報"""
        verbose_name = "かき氷注文"
        verbose_name_plural = "かき氷注文"
