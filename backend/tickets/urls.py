from django.urls import path
from .views import TicketListCreate, PuntoAtencionListCreate, BuscarUsuarioPorCedula, CustomTokenObtainPairView, LogoutView, RegisterView, TurnoList
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('tickets/', TicketListCreate.as_view(), name='ticket-list-create'),
    path('puntos-atencion/', PuntoAtencionListCreate.as_view(), name='punto-atencion-list-create'),
    path('buscar-usuario/<str:cedula>/', BuscarUsuarioPorCedula.as_view(), name='buscar-usuario'),
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('registrarse/', RegisterView.as_view(), name='register'),
    path('turnos/', TurnoList.as_view(), name='turno-list'),
]