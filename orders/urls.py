from django.urls import path
from . import views

urlpatterns = [
    path('', views.role_select, name='role_select'),
    path('register/', views.register_view, name='register'),
    path('ice/', views.ice_view, name='ice'),
    path('complete/<int:order_id>/', views.complete_order, name='complete_order'),
    path('detail/<int:order_id>/', views.order_detail, name='order_detail'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('add_temp_ice/', views.add_temp_ice, name='add_temp_ice'),
    path('submit_order_group/', views.submit_order_group, name='submit_order_group'),
    path('delete_temp_ice/<int:index>/', views.delete_temp_ice, name='delete_temp_ice'),
    path('complete_group/<str:group_id>/', views.complete_group, name='complete_group'),
    path('delete_group/<str:group_id>/', views.delete_group, name='delete_group'),


]
