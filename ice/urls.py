from django.urls import path
from ice import views
from common import views_auth

urlpatterns = [
    path('', views.role_select, name='role_select'),
    path('register/', views.register_view, name='register_view'),
    path('register/', views.register_view, name='register'),  # backward compatibility
    path('register', views.register_view),  # allow access without trailing slash
    path('ice/', views.ice_view, name='ice_view'),
    path('ice/', views.ice_view, name='ice'),  # backward compatibility
    path('ice', views.ice_view),  # allow access without trailing slash
    path('complete/<int:order_id>/', views.complete_order, name='complete_order'),
    path('detail/<int:order_id>/', views.order_detail, name='order_detail'),
    path('login/', views_auth.login_view, name='login'),
    path('logout/', views_auth.logout_view, name='logout'),
    path('add_temp_ice/', views.add_temp_ice, name='add_temp_ice'),
    path('submit_order_group/', views.submit_order_group, name='submit_order_group'),
    path('delete_temp_ice/<int:index>/', views.delete_temp_ice, name='delete_temp_ice'),
    path('complete_group/<str:group_id>/', views.complete_group, name='complete_group'),
    path('delete_group/<str:group_id>/', views.delete_group, name='delete_group'),
    path('deshap/', views.deshap_view, name='deshap'),
    path('update_status/<str:group_id>/<str:new_status>/', views.update_status, name='update_status'),
    path('delete_group_from_deshap/<str:group_id>/', views.delete_group_from_deshap, name='delete_group_from_deshap'),
    path('health/', views.health_check, name='health_check'),
    path('add_temp_pudding/', views.add_temp_pudding, name='add_temp_pudding'),
    path('delete_all_pudding/', views.delete_all_pudding, name='delete_all_pudding'),
    path('api/active_count/', views.api_active_count, name='api_active_count'),
]
