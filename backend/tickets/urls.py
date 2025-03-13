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
)
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('turnos/', TurnoListCreate.as_view(), name='turno-list-create'),  # Listar y crear turnos
    path('turnos/<int:id>/', TurnoDetailView.as_view(), name='turno-detail'),  # Detalle, actualización y eliminación de turnos
    path('puntos-atencion/', PuntoAtencionListCreate.as_view(), name='punto-atencion-list-create'),  # Listar y crear puntos de atención
    path('buscar-usuario/<str:cedula>/', BuscarUsuarioPorCedula.as_view(), name='buscar-usuario'),  # Buscar usuario por cédula
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),  # Login con JWT
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),  # Refrescar token
    path('logout/', LogoutView.as_view(), name='logout'),  # Logout
    path('register/', RegisterView.as_view(), name='register'),  # Registro de usuarios
]