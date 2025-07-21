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

# フレーバーの選択肢
FLAVOR_CHOICES = [
    ('jersey', 'ジャージー牛乳'),
    ('ocha', 'お茶'),
    ('mango', 'マンゴー'),
    ('mint', 'チョコミント'),
    ('caramel', 'キャラメル'),
    ('strawberry', 'いちご'),
    ('tachibana', 'たちばな'),
    ('idashio', '井田塩'),
    ('cassis', 'カシス'),
    ('chocolate', 'ショコラ'),
    ('coffee', 'コーヒー'),
    ('lemon', 'レモン'),
]


class Order(models.Model):
    """アイスクリーム注文を管理するモデル"""
    
    group_id = models.CharField(max_length=20)  # グループID
    size = models.CharField(max_length=2, choices=[('S', 'シングル'), ('W', 'ダブル')])  # サイズ
    container = models.CharField(max_length=10, choices=[('cup', 'カップ'), ('cone', 'コーン')])  # 容器
    flavor1 = models.CharField(max_length=50, choices=FLAVOR_CHOICES)  # フレーバー1
    flavor2 = models.CharField(max_length=50, blank=True, null=True, choices=FLAVOR_CHOICES)  # フレーバー2（ダブル用）
    is_completed = models.BooleanField(default=False)  # 完了フラグ
    timestamp = models.DateTimeField(auto_now_add=True)  # 注文受付時刻
    status = models.CharField(max_length=10, choices=ORDER_STATUS_CHOICES, default='ok')  # 注文状態
    clip_color = models.CharField(max_length=10, choices=CLIP_COLOR_CHOICES)  # クリップ色
    clip_number = models.IntegerField()  # クリップ番号
    completed_at = models.DateTimeField(null=True, blank=True)  # 完了時刻
    is_auto_stopped = models.BooleanField(default=False)  # 自動STOPかどうか
    note = models.TextField(blank=True, null=True)  # 備考欄
    is_pudding = models.BooleanField(default=False, verbose_name='アフォガードプリン')  # アフォガードプリンかどうか

    def __str__(self):
        """管理画面等での表示用"""
        return f"{self.group_id} - {self.size} - {self.flavor1}"

    class Meta:
        """メタ情報"""
        verbose_name = "アイスクリーム注文"
        verbose_name_plural = "アイスクリーム注文"
