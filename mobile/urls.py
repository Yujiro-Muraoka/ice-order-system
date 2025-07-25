from django.urls import path
from . import views

urlpatterns = [
    path('', views.mobile_order_entry, name='mobile_order'),
    path('order/', views.mobile_order_entry, name='mobile_order_entry'),
    path('submit/', views.submit_mobile_order, name='submit_mobile_order'),
    path('complete/', views.mobile_order_complete, name='mobile_order_complete'),
] 