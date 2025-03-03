from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Ticket, Usuario, PuntoAtencion
from .serializers import TicketSerializer, UsuarioSerializer, PuntoAtencionSerializer

class TicketListCreate(generics.ListCreateAPIView):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer

class PuntoAtencionListCreate(generics.ListCreateAPIView):
    queryset = PuntoAtencion.objects.all()
    serializer_class = PuntoAtencionSerializer

class BuscarUsuarioPorCedula(APIView):
    def get(self, request, cedula):
        try:
            usuario = Usuario.objects.get(cedula=cedula)
            serializer = UsuarioSerializer(usuario)
            return Response(serializer.data)
        except Usuario.DoesNotExist:
            return Response({'error': 'Usuario no encontrado'}, status=404)