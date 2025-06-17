from django.db import models

class ShavedIceOrder(models.Model):
    FLAVOR_CHOICES = [
        ('抹茶', '抹茶'),
        ('いちご', 'いちご'),
        ('ゆず', 'ゆず'),
        ('ほうじ茶', 'ほうじ茶'),
    ]

    flavor = models.CharField(max_length=20, choices=FLAVOR_CHOICES)
    quantity = models.PositiveIntegerField()
    note = models.CharField(max_length=100, blank=True)
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.flavor} x{self.quantity}（{self.note}）"
