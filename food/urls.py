from django.urls import path
from . import views

urlpatterns = [
    path('register', views.food_register, name='food_register'),
    path('add_temp_food/', views.add_temp_food, name='add_temp_food'),
    path('kitchen', views.food_kitchen, name='food_kitchen'),
    path('complete_group/<str:group_id>/', views.complete_food_group, name='complete_food_group'),
]
