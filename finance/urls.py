from django.urls import path
from . import views

urlpatterns = [
    path('', views.transaction_list, name='transaction_list'),
    path('transactions/all/', views.transaction_list_all, name='transaction_list_all'),
    path("buscar/", views.transaction_search, name="transaction_search"),
    path("buscar/all/", views.transaction_search_all, name="transaction_search_all"),
    path("crear/", views.transaction_create, name="transaction_create"),
    path("editar/<int:pk>/", views.transaction_edit, name="transaction_edit"),
    path('pagos/', views.payment_list, name='payment_list'),
    path('pagos/listar/', views.payment_list_view, name='payment_list_view'),
    path('buscar/', views.payment_search, name="payment_search"),
    path('buscar/listar/', views.payment_search_view, name="payment_search_view"),
    path('crear/', views.payment_create, name="payment_create"),
    path('pagos/crear/', views.payment_create, name="payment_create"),
    path('pagos/buscar-acometida/', views.payment_connection_search, name="payment_connection_search"),
    path('payment/create/success/', views.payment_create_success, name='payment_create_success'),
    path('transacciones/pdf/', views.transaction_pdf, name='transaction_pdf'),
    path('informe/', views.informe_view, name='informe_view'),
    path('informe/pdf/', views.informe_mensual_pdf, name='informe_mensual_pdf'),
]