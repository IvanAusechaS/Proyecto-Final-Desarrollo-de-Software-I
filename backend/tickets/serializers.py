from rest_framework import serializers
from .models import Ticket, Usuario, PuntoAtencion

class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ['id', 'cedula', 'nombre', 'email', 'telefono']

class PuntoAtencionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PuntoAtencion
        fields = ['id', 'nombre', 'ubicacion']

class TicketSerializer(serializers.ModelSerializer):
    usuario = serializers.PrimaryKeyRelatedField(queryset=Usuario.objects.all())
    punto_atencion = serializers.PrimaryKeyRelatedField(queryset=PuntoAtencion.objects.all())

    class Meta:
        model = Ticket
        fields = ['id', 'usuario', 'punto_atencion', 'numero', 'tipo_cita', 'prioridad', 'descripcion', 'estado', 'fecha']