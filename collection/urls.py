from django.urls import path
from . import views

urlpatterns = [
    path('tarifas/', views.fee_list, name='fee_list'),
    path("fees/json/", views.fees_json, name="fees_json"),
    path("fees/activate/<int:pk>/", views.fee_activate, name="fee_activate"),
    path('tarifas/agregar_ta/', views.fee_create_form, name='fee_create_form'),
    path('fees/create/', views.fee_create, name='fee_create'),
    path('tarifas/<int:tarifa_id>/ver/', views.ver_tarifa, name='ver_tarifa'),
    path("tarifas-buscar/", views.fee_search, name="fee_search"),
]
