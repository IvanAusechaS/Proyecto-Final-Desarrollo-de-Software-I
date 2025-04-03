from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import Usuario, PuntoAtencion, Turno
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = 'email'  # Explicitly set to 'email' to match USERNAME_FIELD

    def validate(self, attrs):
        email = attrs.get('email')  # Usar 'email' directamente
        password = attrs.get('password')

        logger.info(f"Intentando login con email: {email}")

        try:
            user = Usuario.objects.get(email=email)
            logger.info(f"Usuario encontrado: {user.nombre}, Profesional: {user.es_profesional}, Activo: {user.is_active}")
            if not user.check_password(password):
                logger.info("Contraseña incorrecta")
                raise serializers.ValidationError('Contraseña incorrecta')
            if not user.is_active:
                logger.info("Usuario inactivo")
                raise serializers.ValidationError('Usuario inactivo')
        except Usuario.DoesNotExist:
            logger.info(f"No se encontró usuario con email: {email}")
            raise serializers.ValidationError('Usuario no encontrado')

        data = super().validate(attrs)
        logger.info(f"Login exitoso para {user.nombre}")
        data['user'] = {
            'id': user.id,  # self.user ya está seteado por super().validate
            'cedula': user.cedula or '',
            'email': user.email,
            'nombre': user.nombre,
            'es_profesional': user.es_profesional,
            'is_admin': user.is_admin,
            'is_active': user.is_active
        }
        return data

class UsuarioSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = Usuario
        fields = ['id', 'cedula', 'email', 'nombre', 'password', 'es_profesional']
        read_only_fields = ['id']

    def validate_cedula(self, value):
        if not value.isdigit():
            raise serializers.ValidationError('La cédula debe contener solo números.')
        if len(value) < 6 or len(value) > 20:
            raise serializers.ValidationError('La cédula debe tener entre 6 y 20 dígitos.')
        return value

    def create(self, validated_data):
        user = Usuario.objects.create_user(
            cedula=validated_data.get('cedula', None),  # Opcional
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
        write_only=True
    )
    tipo_cita = serializers.CharField()
    prioridad = serializers.ChoiceField(choices=Turno.PRIORIDAD_CHOICES, default='N')
    fecha = serializers.DateField(read_only=True)  # Explicitly define as DateField

    class Meta:
        model = Turno
        fields = ['id', 'numero', 'usuario', 'punto_atencion', 'punto_atencion_id', 'tipo_cita', 'fecha', 'fecha_cita', 'estado', 'prioridad', 'fecha_atencion', 'descripcion']
        read_only_fields = ['id', 'numero', 'usuario', 'fecha', 'fecha_cita', 'fecha_atencion']

    def create(self, validated_data):
        validated_data['usuario'] = self.context['request'].user
        validated_data['fecha'] = timezone.now().date()  # Asegura que fecha sea solo la fecha
        return super().create(validated_data)