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
    path('lecturas/', views.readings_list, name='readings_list'),
    path('lecturas/buscar', views.reading_search, name='reading_search'),
    path('lecturas/crear/<int:pk>/', views.reading_create, name='reading_create'),
    path('lecturas/editar/<int:pk>/', views.reading_edit, name='reading_edit'),
    path('reading/search/<int:pk>/<str:mode>/', views.search_connection_reading, name='search_connection_reading'),
    path('reading/details/', views.reading_details, name='reading_details'),
    path('cobros/', views.collection_list, name='collection_list'),
    path('cobros/buscar', views.collection_search, name='collection_search'),
    path('cobros/cobrar/<int:pk>/', views.charge_collected, name='charge_collected'),
    path('cobros/historicos', views.collection_list_historical, name='collection_list_historical'),
    path('cobros/detalle/<int:pk>/', views.collection_details, name='collection_details'),
]
