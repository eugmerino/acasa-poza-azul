from django.urls import path
from . import views

urlpatterns = [
    path('', views.meet_list, name='meet_list'),
    path("buscar/", views.meet_search, name="meet_search"),
    path("crear/", views.meet_create, name="meet_create"),
    path("editar/<int:pk>/", views.meet_edit, name="meet_edit"),
]