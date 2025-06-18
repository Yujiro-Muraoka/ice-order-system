from django.db import models

ORDER_STATUS_CHOICES = [
    ('ok', 'アイス作成OK'),
    ('stop', 'アイス作成STOP'),
    ('hold', '保留（非表示待ち）'),
]

CLIP_COLOR_CHOICES = [
    ('yellow', '黄色'),
    ('white', '白色'),
]

FLAVOR_CHOICES = [
    ('jersey', 'ジャージー牛乳'),
    ('matcha', '抹茶'),
    ('mango', 'マンゴー'),
    ('mint', 'チョコミント'),
    ('blackbean', '黒豆'),
    ('saltcaramel', '塩キャラ'),
    ('strawberry', 'いちご'),
    ('strawmilk', 'いちごミルク'),
    ('idashio', '井田塩'),
    ('cassis', 'カシス'),
    ('chocolat', 'ショコラ'),
    ('sakura', 'さくらもち'),
    ('coffee', 'コーヒー'),
    ('lemon', 'レモン'),
    ('hojicha', 'ほうじ茶'),
    ('yuzu', 'ゆず'),
]

class Order(models.Model):
    group_id = models.CharField(max_length=20)
    size = models.CharField(max_length=2, choices=[('S', 'シングル'), ('W', 'ダブル')])
    container = models.CharField(max_length=10, choices=[('cup', 'カップ'), ('cone', 'コーン')])
    flavor1 = models.CharField(max_length=50, choices=FLAVOR_CHOICES)
    flavor2 = models.CharField(max_length=50, blank=True, null=True, choices=FLAVOR_CHOICES)
    is_completed = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=ORDER_STATUS_CHOICES, default='ok')
    clip_color = models.CharField(max_length=10, choices=CLIP_COLOR_CHOICES)
    clip_number = models.IntegerField()
    completed_at = models.DateTimeField(null=True, blank=True)
    is_auto_stopped = models.BooleanField(default=False)  # ← 自動STOPかどうか
    note = models.TextField(blank=True, null=True)  # ← 備考欄を追加
    is_pudding = models.BooleanField(default=False, verbose_name='アフォガードプリン')
    def __str__(self):
        return f"{self.group_id} - {self.size} - {self.flavor1}"
