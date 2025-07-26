from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.shavedice_register, name='shavedice_register'),
    path('kitchen/', views.shavedice_kitchen, name='shavedice_kitchen'),
    path('add_temp_ice/', views.add_temp_ice, name='add_temp_ice'),
    path('detail/<int:order_id>/', views.order_detail, name='order_detail'),
    path('submit_order_group/', views.submit_order_group, name='submit_order_group'),
    path('complete/<int:order_id>/', views.complete_order, name='complete_order'),
    path('complete_group/<str:group_id>/', views.complete_group, name='complete_group'),
    path('delete_group/<str:group_id>/', views.delete_group, name='delete_group'),
    path('delete_temp_ice/<int:index>/', views.delete_temp_ice, name='delete_temp_ice'),
    path('ice/', views.ice_view, name='ice'),
    path('deshap/', views.shavedice_deshap_view, name='shavedice_deshap'),
    path('update_status/<str:group_id>/<str:new_status>/', views.shavedice_update_status, name='shavedice_update_status'),
    path('waittime/', views.wait_time_view, name='shavedice_wait_time'),
]
