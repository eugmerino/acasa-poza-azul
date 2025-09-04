from django.urls import path
from . import views

urlpatterns = [
    path('tarifas/', views.fee_list, name='fee_list'),
]
