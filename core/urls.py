from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

urlpatterns = [
    path("", views.login_view, name="login"),
    path("inicio/", views.inicio, name="inicio"),
    path("password-reset/", views.password_reset_request, name="password_reset_request"),
    path("reset-password/<int:uid>/<str:token>/", views.password_reset_confirm, name="password_reset_confirm"),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
]
