from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import Usuario, PuntoAtencion, Ticket, Turno
import logging

logger = logging.getLogger(__name__)

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = 'login_field'

    def validate(self, attrs):
        login_field = attrs.get('login_field')
        password = attrs.get('password')

        logger.info(f"Intentando login con login_field: {login_field}, password: {password}")

        user = None
        try:
            if '@' in login_field:
                user = Usuario.objects.get(email=login_field)
            else:
                user = Usuario.objects.get(cedula=login_field)
            logger.info(f"Usuario encontrado: {user}")
        except Usuario.DoesNotExist:
            logger.info(f"No se encontró usuario con login_field: {login_field}")
            raise serializers.ValidationError('Usuario no encontrado')

        if user.check_password(password):
            logger.info("Contraseña correcta")
            data = {}
            refresh = self.get_token(user)
            data['refresh'] = str(refresh)
            data['access'] = str(refresh.access_token)
            data['user'] = {'nombre': user.nombre, 'es_profesional': user.es_profesional}
            return data
        else:
            logger.info("Contraseña incorrecta")
            raise serializers.ValidationError('Contraseña incorrecta')

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

class TicketSerializer(serializers.ModelSerializer):
    usuario = UsuarioSerializer(read_only=True)
    punto_atencion = PuntoAtencionSerializer(read_only=True)

    class Meta:
        model = Ticket
        fields = ['id', 'usuario', 'punto_atencion', 'numero', 'tipo_cita', 'prioridad', 'descripcion', 'estado', 'fecha']

class TurnoSerializer(serializers.ModelSerializer):
    ticket = TicketSerializer(read_only=True)
    punto_atencion = PuntoAtencionSerializer(read_only=True)

    class Meta:
        model = Turno
        fields = ['id', 'ticket', 'punto_atencion', 'estado', 'fecha_asignacion', 'fecha_atencion']