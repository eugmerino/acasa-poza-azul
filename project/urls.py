from django.urls import path
from . import views

urlpatterns = [
    path('project/', views.project_info_view, name='project_info'),
    path('comunidades/', views.community_list, name='community_list'),
    path('comunidades/buscar/', views.community_search, name='community_search'),
    path('comunidades/crear/', views.community_create, name='community_create'),
    path('comunidades/editar/<int:pk>/', views.community_edit, name='community_edit'),
]
