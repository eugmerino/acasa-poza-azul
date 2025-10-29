from django.urls import path
from . import views

urlpatterns = [
    path('reporte/', views.report_repair_list, name='report_repair_list'),
    path('reporte/buscar/', views.report_repair_search, name='report_repair_search'),
    path('reporte/crear/', views.report_repair_create, name='report_repair_create'),
    path('reporte/editar/<int:pk>/', views.report_repair_edit, name='report_repair_edit'),
    path('reporte/eliminar/<int:pk>/', views.report_repair_delete, name='report_repair_delete'),
    path('reporte/ver/<int:pk>/', views.report_repair_view, name='report_repair_view'),
    path('', views.repair_list, name='repair_list'),
    path('registro/<int:pk>/', views.repair_edit, name='repair_edit'),
    path('buscar/', views.repair_search, name='repair_search'),
    path('pago/', views.repair_pay_list, name='repair_pay_list'),
    path('pago/buscar/', views.repair_pay_search, name='repair_pay_search'),
    path('pago/registrar/<int:pk>/', views.repair_pay_edit, name='repair_pay_edit'),
]
