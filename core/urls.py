from django.urls import path
from . import views

urlpatterns = [
    path("", views.login_view, name="login"),
    path("inicio/", views.inicio, name="inicio"),
    path("password-reset/", views.password_reset_request, name="password_reset_request"),
    path("reset-password/<int:uid>/<str:token>/", views.password_reset_confirm, name="password_reset_confirm"),
    path("logout/", views.CustomLogoutView.as_view(), name="logout"),
]
