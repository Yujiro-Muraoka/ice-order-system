from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.shavedice_register, name='shavedice_register'),
    path('kitchen/', views.shavedice_kitchen, name='shavedice_kitchen'),
    path('add_temp_ice/', views.add_temp_ice, name='add_temp_ice'),
    path('detail/<int:order_id>/', views.order_detail, name='order_detail'),
    path('submit_order_group/', views.submit_order_group, name='submit_order_group'),

]
