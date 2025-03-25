# backend/tickets/urls.py
from django.urls import path
from .views import (
    TurnoListCreate,
    TurnoDetailView,
    PuntoAtencionListCreate,
    BuscarUsuarioPorCedula,
    CustomTokenObtainPairView,
    LogoutView,
    RegisterView,
    FirebaseLoginView,
    UpdateCedulaView,
    ChangePasswordView,
    ResetPasswordView,
    ResetPasswordConfirmView,
    ContactView,
    UpdateProfileView,
    PuntoProfesionalesView,
    CheckAvailabilityView,
    CurrentTurnosView,  # Añadido
    PuntoAtencionServicesView,
)
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('turnos/', TurnoListCreate.as_view(), name='turno-list-create'),
    path('turnos/<int:pk>/', TurnoDetailView.as_view(), name='turno-detail'),
    path('puntos-atencion/', PuntoAtencionListCreate.as_view(), name='punto-atencion-list-create'),
    path('buscar-usuario/<str:cedula>/', BuscarUsuarioPorCedula.as_view(), name='buscar-usuario'),
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('register/', RegisterView.as_view(), name='register'),
    path('firebase-login/', FirebaseLoginView.as_view(), name='firebase-login'),
    path('update-cedula/', UpdateCedulaView.as_view(), name='update-cedula'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset-password'),
    path('reset-password-confirm/', ResetPasswordConfirmView.as_view(), name='reset-password-confirm'),
    path('contact/', ContactView.as_view(), name='contact'),
    path('update-profile/', UpdateProfileView.as_view(), name='update-profile'),
    path('puntos-atencion/<int:pk>/profesionales/', PuntoProfesionalesView.as_view(), name='punto-profesionales'),
    path('turnos/check-availability/', CheckAvailabilityView.as_view(), name='check-availability'),
    path('current-turnos/', CurrentTurnosView.as_view(), name='current-turnos'),  # Añadido
    path('puntos-atencion-services/', PuntoAtencionServicesView.as_view(), name='punto-atencion-services'),
]