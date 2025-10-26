from django.urls import path
from . import views

urlpatterns = [
    path('pagos/', views.payment_list, name='payment_list'),
    path('pagos/listar/', views.payment_list_view, name='payment_list_view'),
    path('buscar/', views.payment_search, name="payment_search"),
    path('buscar/listar/', views.payment_search_view, name="payment_search_view"),
    path('crear/', views.payment_create, name="payment_create"),
    path('pagos/crear/', views.payment_create, name="payment_create"),
    path('pagos/buscar-acometida/', views.payment_connection_search, name="payment_connection_search"),
    path('payment/create/success/', views.payment_create_success, name='payment_create_success'),
]
