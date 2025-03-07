from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import Usuario, PuntoAtencion, Ticket
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
            # Autenticar manualmente y generar tokens
            data = {}
            refresh = self.get_token(user)
            data['refresh'] = str(refresh)
            data['access'] = str(refresh.access_token)
            data['user'] = {'nombre': user.nombre}
            return data
        else:
            logger.info("Contraseña incorrecta")
            raise serializers.ValidationError('Contraseña incorrecta')

class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ['id', 'cedula', 'email', 'nombre', 'telefono']

class PuntoAtencionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PuntoAtencion
        fields = ['id', 'nombre', 'ubicacion', 'activo']

class TicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ['id', 'usuario', 'punto_atencion', 'numero', 'tipo_cita', 'prioridad', 'descripcion', 'estado', 'fecha']