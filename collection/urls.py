from django.urls import path
from . import views

urlpatterns = [
    path('tarifas/', views.fee_list, name='fee_list'),
    path("fees/json/", views.fees_json, name="fees_json"),

    path('tarifas/agregar_ta/', views.fee_create_form, name='fee_create_form'),
]
