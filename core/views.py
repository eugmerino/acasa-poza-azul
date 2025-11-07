from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from .forms import UserLoginForm
from project.models import Project, WaterConnection, Community
from repair.models import Repair
from collection.models import Reading
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth import get_user_model
from django import forms
from django.shortcuts import render
from django.utils import timezone
from django.utils.formats import date_format 
from django.db.models import Q, Count


@login_required(login_url='login')
def inicio(request):
     project = Project.objects.first()
     
     active_partner_count = WaterConnection.objects.values('responsible').distinct().count()

     active_connections_count = WaterConnection.objects.filter(is_active=True).count()

     active_communities_count = Community.objects.count()

     today = timezone.localdate()
     first_day = today.replace(day=1)
     if today.month == 12:
        first_day_next = first_day.replace(year=today.year + 1, month=1)
     else:
        first_day_next = first_day.replace(month=today.month + 1)

     # cobros del mes
     readings_month = Reading.objects.filter(date_reading__gte=first_day,date_reading__lt=first_day_next)
     total_readings_month = readings_month.count()
     paid_readings_month = readings_month.filter(isPaid=True).count()
        # Solo este dato mostramos — EJEMPLO: 30/50
     charges_ratio = f"{paid_readings_month}/{total_readings_month}"

     current_month = date_format(timezone.localtime(), 'F', use_l10n=True).capitalize()

       # KPIs globales
     total_repairs = Repair.objects.count()
     fixed_repairs = Repair.objects.filter(repair_date__isnull=False).count()  # reparadas
     pending_repairs = total_repairs - fixed_repairs

        # Mostrar "reparadas/total"  -> 0/1 en tu ejemplo
     repairs_done_ratio = f"{fixed_repairs}/{total_repairs}" if total_repairs else "0/0"

     return render(request, "home/home.html", {
            "project": project,
            "active_partner_count": active_partner_count,
            "active_connections_count": active_connections_count,
            "active_communities_count": active_communities_count,
            "current_month": current_month,
            "charges_ratio": charges_ratio, 
            "fixed_repairs": fixed_repairs,
            "total_repairs" : total_repairs,
            "total_readings_month": total_readings_month,
            "paid_readings_month" : paid_readings_month
        })



# Diccionario en memoria para rastrear intentos por IP
login_attempts = {}


@never_cache
def login_view(request):
    project = Project.objects.first()
    ip_address = get_client_ip(request)
    now = timezone.now()

    # Si hay registro previo del IP
    if ip_address in login_attempts:
        attempts, last_attempt = login_attempts[ip_address]

        # Si hay más de 5 intentos y el último fue hace menos de 5 minutos
        if attempts >= 5 and now - last_attempt < timedelta(minutes=5):
            remaining_seconds = 300 - (now - last_attempt).seconds
            remaining_minutes = remaining_seconds // 60
            remaining_seconds = remaining_seconds % 60
            messages.error(
                request,
                f"Demasiados intentos fallidos. Espera {remaining_minutes} minutos y {remaining_seconds} segundos antes de intentar nuevamente."
            )
            return render(request, "authentication/login.html", {"project": project})

        # Si ya pasaron más de 5 minutos, reiniciar contador
        if now - last_attempt >= timedelta(minutes=5):
            login_attempts[ip_address] = [0, now]

    if request.method == "POST":
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()

             # Bloquear si no es staff
            if not user.is_staff:
                messages.error(request, "Tu cuenta no tiene permiso para acceder al sistema.")
                return render(request, "authentication/login.html", {"form": form, "project": project})

            auth_login(request, user)
            messages.success(request, "Has iniciado sesión correctamente.")

            # Reiniciar contador al iniciar sesión correctamente
            if ip_address in login_attempts:
                del login_attempts[ip_address]

            return redirect("inicio")

        else:
            # Registrar intento fallido
            if ip_address not in login_attempts:
                login_attempts[ip_address] = [1, now]
            else:
                login_attempts[ip_address][0] += 1
                login_attempts[ip_address][1] = now

            remaining = 5 - login_attempts[ip_address][0]
            if remaining > 0:
                messages.error(request, f"Credenciales inválidas. Te quedan {remaining} intentos antes del bloqueo.")
            else:
                messages.error(request, "Demasiados intentos fallidos. Tu acceso se bloqueará por 5 minutos.")
    else:
        form = UserLoginForm()

    return render(request, "authentication/login.html", {"form": form, "project": project})


def get_client_ip(request):
    """Obtiene la IP del cliente desde el request."""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip


class PasswordResetRequestForm(forms.Form):
    email = forms.EmailField(label="Correo electrónico", widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "Ingrese su correo"}))


def password_reset_request(request):
    project = Project.objects.first()
    if request.method == "POST":
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            User = get_user_model()
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                messages.error(request, "No existe un usuario con ese correo.")
                return render(request, "authentication/password_reset_request.html", {"form": form, "project": project})

            token = default_token_generator.make_token(user)
            reset_url = request.build_absolute_uri(
                f"/reset-password/{user.pk}/{token}/"
            )
            subject = "Restablecimiento de contraseña"
            message = render_to_string("authentication/password_reset_email.html", {
                "user": user,
                "reset_url": reset_url,
                "project": project,
            })
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=False)
            messages.success(request, "Se ha enviado un enlace de restablecimiento a tu correo.")
            return redirect("login")
    else:
        form = PasswordResetRequestForm()
    return render(request, "authentication/password_reset_request.html", {"form": form, "project": project})


def password_reset_confirm(request, uid, token):
    project = Project.objects.first()
    User = get_user_model()
    try:
        user = User.objects.get(pk=uid)
    except User.DoesNotExist:
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if request.method == "POST":
            password1 = request.POST.get("password1")
            password2 = request.POST.get("password2")
            if password1 and password2 and password1 == password2:
                user.set_password(password1)
                user.save()
                messages.success(request, "Contraseña restablecida correctamente. Ahora puedes iniciar sesión.")
                return redirect("login")
            else:
                messages.error(request, "Las contraseñas no coinciden.")
        return render(request, "authentication/password_reset_confirm.html", {"project": project, "validlink": True})
    else:
        messages.error(request, "El enlace de restablecimiento no es válido o ha expirado.")
        return render(request, "authentication/password_reset_confirm.html", {"project": project, "validlink": False})