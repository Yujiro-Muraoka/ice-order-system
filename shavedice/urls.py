from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.shavedice_register, name='shavedice_register'),
    path('kitchen/', views.shavedice_kitchen, name='shavedice_kitchen'),
]
