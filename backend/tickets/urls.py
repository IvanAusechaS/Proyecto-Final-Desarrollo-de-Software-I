from django.urls import path
from .views import TicketListCreate, PuntoAtencionListCreate, BuscarUsuarioPorCedula

urlpatterns = [
    path('tickets/', TicketListCreate.as_view(), name='ticket-list-create'),
    path('puntos-atencion/', PuntoAtencionListCreate.as_view(), name='punto-atencion-list-create'),
    path('buscar-usuario/<str:cedula>/', BuscarUsuarioPorCedula.as_view(), name='buscar-usuario'),
]