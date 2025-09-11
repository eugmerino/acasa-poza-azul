from django.urls import path
from . import views

urlpatterns = [
    path('project/', views.project_info_view, name='project_info'),
    path("communitys/", views.community_list, name="community_list"),
    path("community-search/", views.community_search, name="community_search"),
]    