from django.db import models


CLIP_COLOR_CHOICES = [
    ('yellow', '黄色'),
    ('white', '白色'),
]

class ShavedIceOrder(models.Model):
    FLAVOR_CHOICES = [
        ('抹茶', '抹茶'),
        ('いちご', 'いちご'),
        ('ゆず', 'ゆず'),
        ('ほうじ茶', 'ほうじ茶'),
    ]
    flavor = models.CharField(max_length=50, choices=FLAVOR_CHOICES)
    is_completed = models.BooleanField(default=False)
    clip_color = models.CharField(
        max_length=10,
        choices=CLIP_COLOR_CHOICES,
        default='white'  # 🟢 例：デフォルトで白色
    )
    clip_number = models.IntegerField(default=0)  # 🟢 例：未指定時は0番に
    timestamp = models.DateTimeField(auto_now_add=True)  # 🟢 これは auto_now_add でOK
    completed_at = models.DateTimeField(null=True, blank=True)
    note = models.TextField(blank=True, null=True)  # ← 備考欄を追加
    def __str__(self):
        return f"{self.flavor}（{self.note}）"
