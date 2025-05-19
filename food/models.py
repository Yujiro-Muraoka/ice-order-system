from django.db import models

class FoodOrder(models.Model):
    menu = models.CharField(max_length=20)  # "からあげ丼" or "ルーロー飯"
    quantity = models.PositiveIntegerField(default=1)
    clip_color = models.CharField(max_length=10)
    clip_number = models.IntegerField()
    group_id = models.CharField(max_length=50)
    status = models.CharField(max_length=10, default='ok')
    is_completed = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    note = models.TextField(blank=True, default="")

    def __str__(self):
        return f"{self.menu} ×{self.quantity} [{self.group_id}]"
