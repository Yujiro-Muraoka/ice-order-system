from django.urls import path
from . import views

urlpatterns = [
    path('register', views.food_register, name='food_register'),
    path('add_temp_food/', views.add_temp_food, name='add_temp_food'),
    path('kitchen', views.food_kitchen, name='food_kitchen'),
    path('complete_group/<str:group_id>/', views.complete_food_group, name='complete_food_group'),
    path('delete_temp_food/<int:index>/', views.delete_temp_food, name='delete_temp_food'),
    path('delete_all_temp_food/', views.delete_all_temp_food, name='delete_all_temp_food'),
    path('submit_order_group/', views.submit_order_group, name='submit_order_group'),



]
