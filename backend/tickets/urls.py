from django.urls import path
from .views import CustomTokenObtainPairView
from .views import (
    update_punto_servicios_view,
    list_turnos_view,
    usuarios_list_create_view,
    create_turno_view,
    TurnoDetailView,
    PuntoAtencionListCreate,
    buscar_usuario_por_cedula,  # Importar como función
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
    pending_turnos_by_service,  # Importar como función
    ProfesionalTurnosList,
    profesional_stats_view,
    CustomTokenObtainPairView,
    get_turnos_colas,
    reset_password_view,
    reset_password_confirm_view,
    verify_reset_code_view,
)
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    path('turnos/list/', list_turnos_view, name='list_turnos'),  
    path('turnos/create/', create_turno_view, name='create_turno'), 
    path('turnos/colas/', get_turnos_colas, name='get_turnos_colas'), 
    path('turnos/<int:pk>/', TurnoDetailView.as_view(), name='turno_detail'),
    path('profesional-turnos/<int:pk>/', TurnoDetailView.as_view(), name='profesional_turno_detail'),
    path('puntos-atencion/', PuntoAtencionListCreate.as_view(), name='punto-atencion-list-create'),
    path('puntos-atencion/<int:pk>/', views.punto_atencion_delete_view, name='punto-atencion-delete'),
    path('puntos-atencion/<int:pk>/servicios/', update_punto_servicios_view, name='punto-atencion-servicios-update'),
    path('buscar-usuario/<str:cedula>/', buscar_usuario_por_cedula, name='buscar-usuario'),
    path('profesional-turnos/', ProfesionalTurnosList.as_view(), name='profesional-turnos'),
    path('profesional-stats/', profesional_stats_view, name='profesional-stats'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('logout/', logout_view, name='logout'),
    path('register/', register_view, name='register'),
    path('update-cedula/', update_cedula_view, name='update-cedula'),
    path('change-password/', change_password_view, name='change-password'),
    path('reset-password/', reset_password_view, name='reset-password'),
    path('reset-password-confirm/', reset_password_confirm_view, name='reset-password-confirm'),
    path('contact/', contact_view, name='contact'),
    path('update-profile/', update_profile_view, name='update-profile'),
    path('usuarios/', views.usuarios_list_create_view, name='usuarios-list-create'),
    path('usuarios/<int:id>/', views.usuario_delete_view, name='usuario-delete'),
    path('puntos-atencion/<int:pk>/profesionales/', punto_profesionales_view, name='punto-profesionales'),
    path('turnos/check-availability/', check_availability_view, name='check-availability'),
    path('current-turnos/', current_turnos_view, name='current-turnos'),
    path('puntos-atencion-services/', punto_atencion_services_view, name='punto-atencion-services'),
    path('pending-turnos-by-service/', pending_turnos_by_service, name='pending-turnos-by-service'),
    path('usuarios/<int:id>/rol/', views.cambiar_rol_usuario, name='cambiar-rol-usuario'),
    path('asignar-punto/', views.asignar_punto_a_profesional, name='asignar-punto'),
    path('reset-password/', views.reset_password_view, name='reset_password'),
    path('reset-password-confirm/', views.reset_password_confirm_view, name='reset_password_confirm'),
    path('verify-reset-code/', views.verify_reset_code_view, name='verify_reset_code'),
    ]