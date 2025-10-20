from django.urls import path
from . import views

urlpatterns = [
    path('', views.transaction_list, name='transaction_list'),
    path("buscar/", views.transaction_search, name="transaction_search"),
    path("crear/", views.transaction_create, name="transaction_create"),
    path("editar/<int:pk>/", views.transaction_edit, name="transaction_edit"),
]