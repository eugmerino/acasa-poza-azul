from django.urls import path
from . import views

urlpatterns = [
    path("logs/", views.logs_list, name="logs_list"),
    path("logs/search/", views.logs_search, name="logs_search"),
]
