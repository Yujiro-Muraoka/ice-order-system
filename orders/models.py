from django.db import models
import uuid

class IceOrder(models.Model):
    SIZE_CHOICES = [('S', 'シングル'), ('W', 'ダブル')]
    CONTAINER_CHOICES = [('cup', 'カップ'), ('cone', 'コーン')]
    FLAVOR_CHOICES = [
        ('jersey', 'ジャージー牛乳'),
        ('matcha', '抹茶'),
        ('mango', 'マンゴー'),
    ]

    size = models.CharField(max_length=1, choices=SIZE_CHOICES)
    container = models.CharField(max_length=10, choices=CONTAINER_CHOICES)
    flavor1 = models.CharField(max_length=20, choices=FLAVOR_CHOICES)
    flavor2 = models.CharField(max_length=20, blank=True, null=True, choices=FLAVOR_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    order_group = models.CharField(max_length=36, default=uuid.uuid4, editable=False)

    def __str__(self):
        return f"{self.get_size_display()} {self.get_container_display()} - {self.get_flavor1_display()} / {self.get_flavor2_display() or 'なし'}"
