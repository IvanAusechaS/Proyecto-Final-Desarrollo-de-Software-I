from django.urls import path
from .views import TurnoListCreate, PuntoAtencionListCreate, BuscarUsuarioPorCedula, CustomTokenObtainPairView, LogoutView, RegisterView, TurnoUpdate
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('turnos/', TurnoListCreate.as_view(), name='turno-list-create'),
    path('turnos/<int:id>/', TurnoUpdate.as_view(), name='turno-update'),
    path('puntos-atencion/', PuntoAtencionListCreate.as_view(), name='punto-atencion-list-create'),
    path('buscar-usuario/<str:cedula>/', BuscarUsuarioPorCedula.as_view(), name='buscar-usuario'),
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('registrarse/', RegisterView.as_view(), name='registrarse'),
]