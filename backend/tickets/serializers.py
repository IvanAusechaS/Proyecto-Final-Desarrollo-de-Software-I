# backend/tickets/serializers.py
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

        try:
            user = Usuario.objects.get(cedula=login_field)
            logger.info(f"Usuario encontrado: {user.nombre}, Profesional: {user.es_profesional}, Activo: {user.is_active}")
            if not user.check_password(password):
                logger.info("Contraseña incorrecta")
                raise serializers.ValidationError('Contraseña incorrecta')
            if not user.is_active:
                logger.info("Usuario inactivo")
                raise serializers.ValidationError('Usuario inactivo')
        except Usuario.DoesNotExist:
            logger.info(f"No se encontró usuario con cedula: {login_field}")
            raise serializers.ValidationError('Usuario no encontrado')

        data = super().validate(attrs)
        logger.info(f"Login exitoso para {user.nombre}")
        data['user'] = {
            'id': self.user.id,
            'cedula': self.user.cedula,  # Añadido
            'email': self.user.email,    # Añadido
            'nombre': self.user.nombre,
            'es_profesional': self.user.es_profesional,
            'is_admin': self.user.is_admin,  # Añadido para reflejar permisos
            'is_active': self.user.is_active  # Añadido para reflejar estado
        }
        return data

class UsuarioSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = Usuario
        fields = ['id', 'cedula', 'email', 'nombre', 'password', 'es_profesional']  # Eliminado 'telefono'
        read_only_fields = ['id']  # Solo 'id' como read-only por ahora

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
            password=validated_data['password'],
            es_profesional=validated_data.get('es_profesional', False)
        )
        return user

class PuntoAtencionSerializer(serializers.ModelSerializer):
    profesional = UsuarioSerializer(read_only=True)

    class Meta:
        model = PuntoAtencion
        fields = ('id', 'nombre', 'ubicacion', 'activo', 'servicios_texto', 'profesional')
        read_only_fields = ('id', 'profesional')

class TurnoSerializer(serializers.ModelSerializer):
    usuario = serializers.StringRelatedField(read_only=True)
    punto_atencion = serializers.StringRelatedField(read_only=True)
    punto_atencion_id = serializers.PrimaryKeyRelatedField(
        queryset=PuntoAtencion.objects.all(),
        source='punto_atencion',
        write_only=True,
        required=False  # No requerido en actualizaciones
    )
    tipo_cita = serializers.CharField(required=False)  # No requerido en actualizaciones


    class Meta:
        model = Turno
        fields = ['id', 'numero', 'usuario', 'punto_atencion', 'punto_atencion_id', 'tipo_cita', 'fecha_cita', 'estado', 'fecha_atencion', 'prioridad', 'descripcion']
        read_only_fields = ['id', 'numero', 'usuario', 'fecha_cita', 'fecha_atencion']

    def update(self, instance, validated_data):
        instance.estado = validated_data.get('estado', instance.estado)
        if instance.estado == 'Atendido' and not instance.fecha_atencion:
            from django.utils import timezone
            instance.fecha_atencion = timezone.now()
        instance.save()
        return instance