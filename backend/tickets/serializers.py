from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import Usuario, PuntoAtencion, Turno
import logging

logger = logging.getLogger(__name__)

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        login_field = attrs.get(self.username_field)  # 'cedula'
        password = attrs.get('password')

        logger.info(f"Intentando login con cedula: {login_field}")

        data = super().validate(attrs)  # Valida usando el sistema de Django
        data['user'] = {
            'id': self.user.id,
            'nombre': self.user.nombre,
            'es_profesional': self.user.es_profesional
        }
        return data

class UsuarioSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = Usuario
        fields = ['id', 'cedula', 'email', 'nombre', 'telefono', 'password', 'es_profesional']

    def validate_cedula(self, value):
        if not value.isdigit():
            raise serializers.ValidationError('La cédula debe contener solo números.')
        if len(value) < 6 or len(value) > 20:
            raise serializers.ValidationError('La cédula debe tener entre 6 y 20 dígitos.')
        return value

    def create(self, validated_data):
        user = Usuario.objects.create_user(
            cedula=validated_data['cedula'],
            email=validated_data['email'],
            nombre=validated_data['nombre'],
            telefono=validated_data.get('telefono', ''),
            password=validated_data['password'],
            es_profesional=validated_data.get('es_profesional', False)
        )
        return user

class PuntoAtencionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PuntoAtencion
        fields = ['id', 'nombre', 'ubicacion', 'activo', 'servicios']

class TurnoSerializer(serializers.ModelSerializer):
    usuario = UsuarioSerializer(read_only=True)
    punto_atencion = PuntoAtencionSerializer(read_only=True)
    usuario_id = serializers.PrimaryKeyRelatedField(
        queryset=Usuario.objects.all(), source='usuario', write_only=True
    )
    punto_atencion_id = serializers.PrimaryKeyRelatedField(
        queryset=PuntoAtencion.objects.all(), source='punto_atencion', write_only=True
    )

    class Meta:
        model = Turno
        fields = [
            'id', 'usuario', 'punto_atencion', 'numero', 'tipo_cita', 'prioridad', 
            'descripcion', 'estado', 'fecha', 'fecha_asignacion', 'fecha_atencion', 
            'usuario_id', 'punto_atencion_id'
        ]
        read_only_fields = ['numero', 'fecha', 'fecha_asignacion']

    def update(self, instance, validated_data):
        instance.estado = validated_data.get('estado', instance.estado)
        if instance.estado == 'Atendido' and not instance.fecha_atencion:
            from django.utils import timezone
            instance.fecha_atencion = timezone.now()
        instance.save()
        return instance