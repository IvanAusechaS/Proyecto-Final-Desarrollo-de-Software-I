from django.urls import path
from .views import (
    TurnoListCreate,
    TurnoDetailView,
    PuntoAtencionListCreate,
    buscar_usuario_por_cedula,  # Importar como función
    CustomTokenObtainPairView,
    logout_view,  # Importar como función
    register_view,  # Importar como función
    update_cedula_view,  # Importar como función
    change_password_view,  # Importar como función
    reset_password_view,  # Importar como función
    reset_password_confirm_view,  # Importar como función
    contact_view,  # Importar como función
    update_profile_view,  # Importar como función
    punto_profesionales_view,  # Importar como función
    check_availability_view,  # Importar como función
    current_turnos_view,  # Importar como función
    punto_atencion_services_view,  # Importar como función
    ProfesionalTurnosList,
)
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('turnos/', TurnoListCreate.as_view(), name='turno-list-create'),
    path('turnos/<int:pk>/', TurnoDetailView.as_view(), name='turno-detail'),
    path('puntos-atencion/', PuntoAtencionListCreate.as_view(), name='punto-atencion-list-create'),
    path('buscar-usuario/<str:cedula>/', buscar_usuario_por_cedula, name='buscar-usuario'),
    path('profesional-turnos/', ProfesionalTurnosList.as_view(), name='profesional-turnos'),
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', logout_view, name='logout'),
    path('register/', register_view, name='register'),
    path('update-cedula/', update_cedula_view, name='update-cedula'),
    path('change-password/', change_password_view, name='change-password'),
    path('reset-password/', reset_password_view, name='reset-password'),
    path('reset-password-confirm/', reset_password_confirm_view, name='reset-password-confirm'),
    path('contact/', contact_view, name='contact'),
    path('update-profile/', update_profile_view, name='update-profile'),
    path('puntos-atencion/<int:pk>/profesionales/', punto_profesionales_view, name='punto-profesionales'),
    path('turnos/check-availability/', check_availability_view, name='check-availability'),
    path('current-turnos/', current_turnos_view, name='current-turnos'),
    path('puntos-atencion-services/', punto_atencion_services_view, name='punto-atencion-services'),
]