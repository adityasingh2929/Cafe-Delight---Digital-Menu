from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('phone/', views.phone_view, name='phone'),  # Added trailing slash
    path('otp/', views.otp_view, name='otp'),  # Added trailing slash
    path('menu/', views.menu, name='menu'),  # Added trailing slash
    path('cart/', views.cart, name='cart'),
    path('update_cart/', views.update_cart, name='update_cart'),
    path('create_razorpay_order/', views.create_razorpay_order, name='create_razorpay_order'),
    path('payment_success/', views.payment_success, name='payment_success'),
]
