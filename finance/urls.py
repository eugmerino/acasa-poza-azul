from django.urls import path
from . import views

urlpatterns = [
    path('', views.transaction_list, name='transaction_list'),
    path('transactions/all/', views.transaction_list_all, name='transaction_list_all'),
    path("buscar/", views.transaction_search, name="transaction_search"),
    path("buscar/all/", views.transaction_search_all, name="transaction_search_all"),
    path("crear/", views.transaction_create, name="transaction_create"),
    path("editar/<int:pk>/", views.transaction_edit, name="transaction_edit"),
]