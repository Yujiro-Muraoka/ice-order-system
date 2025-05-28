from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('ice.urls')),
    path('food/', include('food.urls')),  # ← これだけでOK！
    path('shavedice/', include('shavedice.urls')),
]
