from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import Usuario, PuntoAtencion, Turno, validate_turno_time
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = 'email'

    def validate(self, attrs):
        email = attrs.get('email')
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
        data['user_id'] = user.id  # Añadir user_id directamente
        data['user'] = {
            'id': user.id,
            'cedula': user.cedula or '',
            'email': user.email,
            'nombre': user.nombre,
            'es_profesional': user.es_profesional,
            'is_active': user.is_active
        }
        return data

class UsuarioSerializer(serializers.ModelSerializer):
    usuario = serializers.PrimaryKeyRelatedField(queryset=Usuario.objects.all(), required=False)  # Make optional
    punto_atencion = serializers.SerializerMethodField()
    punto_atencion_id_read = serializers.IntegerField(source='punto_atencion.id', read_only=True)
    password = serializers.CharField(write_only=True)

    class Meta:
        model = Usuario
        fields = [
            'id', 'cedula', 'email', 'nombre', 'password', 'es_profesional',
            'punto_atencion', 'punto_atencion_id_read',
            'usuario'
        ]
        read_only_fields = ['id']

    def get_punto_atencion(self, obj):
        punto = obj.punto_atencion
        logger.debug(f"Serializando punto_atencion para usuario {obj.email}: {punto.nombre if punto else 'Ninguno'}")
        return {
            'id': punto.id,
            'nombre': punto.nombre,
            'ubicacion': punto.ubicacion,
            'activo': punto.activo
        } if punto else None

    def validate_cedula(self, value):
        if not value.isdigit():
            raise serializers.ValidationError('La cédula debe contener solo números.')
        if len(value) < 6 or len(value) > 20:
            raise serializers.ValidationError('La cédula debe tener entre 6 y 20 dígitos.')
        return value
    
    def validate_email(self, value):
        if Usuario.objects.filter(email=value).exists():
            raise serializers.ValidationError('Ya existe un usuario con este correo electrónico.')
        return value

    def validate(self, data):
        logger.debug(f"Datos validados en UsuarioSerializer: {data}")
        return data

    def create(self, validated_data):
        user = Usuario.objects.create_user(
            cedula=validated_data.get('cedula', None),
            email=validated_data['email'],
            nombre=validated_data['nombre'],
            password=validated_data['password'],
            es_profesional=validated_data.get('es_profesional', False)
        )
        logger.debug(f"Usuario creado: {user.email}, Profesional: {user.es_profesional}")
        return user

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        logger.debug(f"Serializer data para usuario {instance.id}: {ret}")
        return ret

class PuntoAtencionSerializer(serializers.ModelSerializer):
    profesional = UsuarioSerializer(read_only=True)

    class Meta:
        model = PuntoAtencion
        fields = ('id', 'nombre', 'ubicacion', 'activo', 'servicios_texto', 'profesional')
        read_only_fields = ('id', 'profesional')

class TurnoSerializer(serializers.ModelSerializer):
    usuario = serializers.SerializerMethodField()
    punto_atencion = serializers.SerializerMethodField()
    punto_atencion_id = serializers.PrimaryKeyRelatedField(
        queryset=PuntoAtencion.objects.all(),
        source='punto_atencion',
        write_only=True
    )
    punto_atencion_id_read = serializers.IntegerField(source='punto_atencion.id', read_only=True)
    tipo_cita = serializers.CharField()
    prioridad = serializers.ChoiceField(choices=Turno.PRIORIDAD_CHOICES, default='N')
    fecha = serializers.DateField(read_only=True)
    fecha_cita = serializers.DateTimeField(
        format='%Y-%m-%dT%H:%M:%S.%fZ',
        required=False
    )

    class Meta:
        model = Turno
        fields = [
            'id', 'numero', 'usuario', 'punto_atencion', 'punto_atencion_id', 'punto_atencion_id_read',
            'tipo_cita', 'fecha', 'fecha_cita', 'estado', 'prioridad', 'fecha_atencion', 'descripcion'
        ]
        read_only_fields = ['id', 'numero', 'fecha', 'fecha_atencion']

    def get_usuario(self, obj):
        usuario = obj.usuario
        logger.debug(f"Serializando usuario: {usuario.email if usuario else 'Ninguno'}")
        return {
            'id': usuario.id,
            'email': usuario.email,
            'nombre': usuario.nombre,
            'es_profesional': usuario.es_profesional
        } if usuario else None

    def get_punto_atencion(self, obj):
        punto = obj.punto_atencion
        logger.debug(f"Serializando punto_atencion: {punto.nombre if punto else 'Ninguno'}")
        return {
            'id': punto.id,
            'nombre': punto.nombre,
            'ubicacion': punto.ubicacion,
            'activo': punto.activo
        } if punto else None

    def validate_prioridad(self, value):
        # Validar que el valor de prioridad esté en las opciones permitidas
        valid_choices = [choice[0] for choice in Turno.PRIORIDAD_CHOICES]
        if value not in valid_choices:
            logger.error(f"Valor de prioridad inválido: {value}. Opciones válidas: {valid_choices}")
            raise serializers.ValidationError(f"Prioridad debe ser uno de {valid_choices}")
        logger.debug(f"Prioridad validada: {value}")
        return value

    def validate(self, data):
        logger.debug(f"Datos recibidos para validar: {data}")
        if 'fecha_cita' in data:
            fecha_cita = data['fecha_cita']
            # Convert to local time for validation, but don't modify the original fecha_cita
            local_time = fecha_cita.astimezone(timezone.get_default_timezone())
            validate_turno_time(local_time)
        return data

    def create(self, validated_data):
        validated_data['fecha'] = timezone.now().date()
        logger.debug(f"Creando turno con datos validados: {validated_data}")
        return super().create(validated_data)

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        logger.debug(f"Serializer data para turno {instance.id}: {ret}")
        return ret