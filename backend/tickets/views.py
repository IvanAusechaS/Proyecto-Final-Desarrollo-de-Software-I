from django.core.mail import send_mail
from django.conf import settings
from django.utils.crypto import get_random_string
from django.contrib.auth.hashers import make_password
from rest_framework import generics, viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.decorators import api_view, permission_classes
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomTokenObtainPairSerializer, UsuarioSerializer, PuntoAtencionSerializer, TurnoSerializer
from .models import Usuario, PuntoAtencion, Turno
import logging
from django.utils import timezone
from django.db.models import Count

logger = logging.getLogger(__name__)

# Login con email y JWT
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [AllowAny]

# Registro de usuarios con email
@api_view(['POST'])
@permission_classes([AllowAny])
def register_view(request):
    logger.debug(f"Datos recibidos: {request.data}")
    serializer = UsuarioSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        logger.info(f"Usuario {user.email} registrado exitosamente")
        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': {
                'id': user.id,
                'email': user.email,
                'nombre': user.nombre,
                'cedula': user.cedula,
                'es_profesional': user.es_profesional
            }
        }, status=201)
    logger.error(f"Errores de validación: {serializer.errors}")
    return Response({'error': serializer.errors}, status=400)

# Logout
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    return Response({"detail": "Logout exitoso"}, status=status.HTTP_205_RESET_CONTENT)

# Restablecer contraseña
@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password_view(request):
    email = request.data.get('email')
    if not email:
        return Response({'error': 'Correo electrónico requerido'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = Usuario.objects.get(email=email)
    except Usuario.DoesNotExist:
        return Response({'error': 'No existe un usuario con este correo'}, status=status.HTTP_400_BAD_REQUEST)

    token = get_random_string(length=32)
    # Aquí podrías usar un campo temporal en memoria o un modelo separado, pero por simplicidad usamos email
    reset_link = f"http://localhost:3000/reset-password-confirm?token={token}"
    subject = 'Restablecer tu contraseña'
    message = f'Hola {user.nombre},\n\nHaz clic en este enlace para restablecer tu contraseña: {reset_link}\n\nVálido por 1 hora.'
    from_email = settings.EMAIL_HOST_USER
    recipient_list = [email]

    try:
        send_mail(subject, message, from_email, recipient_list, fail_silently=False)
        logger.info(f"Correo de restablecimiento enviado a {email}")
        # Guardar token temporalmente (puedes usar un modelo ResetToken si prefieres)
        user.reset_password_token = token  # Añadir este campo al modelo si decides usarlo
        user.save()
        return Response({'message': 'Se ha enviado un correo para restablecer tu contraseña'}, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Error al enviar correo: {str(e)}")
        return Response({'error': 'Error al enviar el correo de restablecimiento'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Confirmar restablecimiento de contraseña
@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password_confirm_view(request):
    token = request.data.get('token')
    new_password = request.data.get('new_password')

    if not token or not new_password:
        return Response({'error': 'Token y nueva contraseña son requeridos'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = Usuario.objects.get(reset_password_token=token)
    except Usuario.DoesNotExist:
        return Response({'error': 'Token inválido o expirado'}, status=status.HTTP_400_BAD_REQUEST)

    user.set_password(new_password)
    user.reset_password_token = None
    user.save()
    return Response({'message': 'Contraseña actualizada correctamente'}, status=status.HTTP_200_OK)

# Buscar usuario por cédula (opcional)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def buscar_usuario_por_cedula(request, cedula):
    try:
        usuario = Usuario.objects.get(cedula=cedula)
        serializer = UsuarioSerializer(usuario)
        return Response(serializer.data)
    except Usuario.DoesNotExist:
        return Response({"error": "Usuario no encontrado"}, status=status.HTTP_404_NOT_FOUND)

# Turnos actuales
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_turnos_view(request):
    current_time = timezone.now()
    today = current_time.date()
    turnos_en_progreso = Turno.objects.filter(
        estado='En progreso',
        fecha=today  # Usamos el nuevo campo fecha
    ).order_by('prioridad', 'fecha_cita')  # Prioridad 'P' antes que 'N'

    current_turnos = {}
    estimated_times = {}
    for punto in PuntoAtencion.objects.all():
        turno = turnos_en_progreso.filter(punto_atencion=punto).first()
        current_turnos[punto.id] = turno.numero if turno else 'Ninguno'
        turnos_espera = Turno.objects.filter(
            punto_atencion=punto,
            estado='En espera',
            fecha=today
        ).order_by('prioridad', 'fecha_cita').count()
        estimated_times[punto.id] = turnos_espera * 15

    return Response({
        'current_turnos': current_turnos,
        'estimated_times': estimated_times
    })

# Listar y crear turnos
class TurnoListCreate(generics.ListCreateAPIView):
    queryset = Turno.objects.all()
    serializer_class = TurnoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Turno.objects.filter(usuario=self.request.user)

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)

class ProfesionalTurnosList(generics.ListAPIView):
    serializer_class = TurnoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if not user.es_profesional:
            return Turno.objects.none()  # No turnos si no es profesional
        today = timezone.now().date()
        # Filtra turnos del punto de atención del profesional para el día actual
        return Turno.objects.filter(
            punto_atencion__profesional=user,
            fecha=today
        ).order_by('prioridad', 'fecha_cita')  # Prioridad 'P' primero

class TurnoDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Turno.objects.all()
    serializer_class = TurnoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if not user.es_profesional:
            return Turno.objects.none()
        return Turno.objects.filter(punto_atencion__profesional=user)

# Listar y crear puntos de atención
class PuntoAtencionListCreate(generics.ListCreateAPIView):
    queryset = PuntoAtencion.objects.all()
    serializer_class = PuntoAtencionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if not user.is_active:
            return PuntoAtencion.objects.none()
        if user.is_admin or user.is_superuser:
            return PuntoAtencion.objects.all()
        elif user.es_profesional:
            return PuntoAtencion.objects.filter(profesional=user)
        return PuntoAtencion.objects.filter(activo=True)

    def perform_create(self, serializer):
        user = self.request.user
        if not (user.is_admin or user.is_superuser):
            raise ValidationError("Solo administradores pueden crear puntos de atención")
        serializer.save()

# Actualizar cédula
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_cedula_view(request):
    user = request.user
    cedula = request.data.get('cedula')
    if not cedula:
        return Response({'error': 'Cédula requerida'}, status=status.HTTP_400_BAD_REQUEST)

    if Usuario.objects.filter(cedula=cedula).exclude(id=user.id).exists():
        return Response({'error': 'La cédula ya está registrada'}, status=status.HTTP_400_BAD_REQUEST)

    if not cedula.isdigit() or len(cedula) < 6 or len(cedula) > 20:
        return Response({'error': 'La cédula debe ser numérica y tener entre 6 y 20 dígitos'}, status=status.HTTP_400_BAD_REQUEST)

    user.cedula = cedula
    user.save()
    return Response({
        'user': {'id': user.id, 'nombre': user.nombre, 'es_profesional': user.es_profesional, 'cedula': user.cedula}
    }, status=status.HTTP_200_OK)

# Cambiar contraseña
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password_view(request):
    user = request.user
    current_password = request.data.get('current_password')
    new_password = request.data.get('new_password')

    if not current_password or not new_password:
        return Response({'error': 'Se requieren la contraseña actual y la nueva'}, status=status.HTTP_400_BAD_REQUEST)

    if not user.check_password(current_password):
        return Response({'error': 'Contraseña actual incorrecta'}, status=status.HTTP_400_BAD_REQUEST)

    user.set_password(new_password)
    user.save()
    return Response({'message': 'Contraseña actualizada correctamente'}, status=status.HTTP_200_OK)

# Contacto
@api_view(['POST'])
@permission_classes([AllowAny])
def contact_view(request):
    name = request.data.get('name')
    email = request.data.get('email')
    message = request.data.get('message')

    if not all([name, email, message]):
        return Response({'error': 'Todos los campos son requeridos'}, status=status.HTTP_400_BAD_REQUEST)

    subject = f'Nuevo mensaje de contacto de {name}'
    body = f'Nombre: {name}\nCorreo: {email}\nMensaje:\n{message}'
    from_email = settings.EMAIL_HOST_USER
    recipient_list = ['sistema.atenciondsi@gmail.com']

    try:
        send_mail(subject, body, from_email, recipient_list, fail_silently=False)
        return Response({'message': 'Mensaje enviado exitosamente'}, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Error al enviar correo: {str(e)}")
        return Response({'error': 'Error al enviar el mensaje'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Actualizar perfil
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_profile_view(request):
    user = request.user
    name = request.data.get('name', user.nombre)
    email = request.data.get('email', user.email)

    if Usuario.objects.filter(email=email).exclude(id=user.id).exists():
        return Response({'error': 'El correo ya está registrado'}, status=status.HTTP_400_BAD_REQUEST)

    user.nombre = name
    user.email = email
    user.save()

    serializer = UsuarioSerializer(user)
    return Response({'message': 'Perfil actualizado', 'user': serializer.data}, status=status.HTTP_200_OK)

# Profesionales por punto de atención
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def punto_profesionales_view(request, pk):
    profesionales = Usuario.objects.filter(puntoatencion__id=pk, es_profesional=True)
    serializer = UsuarioSerializer(profesionales, many=True)
    return Response(serializer.data)

from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Count
from .models import Turno, PuntoAtencion

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profesional_stats_view(request):
    user = request.user
    if not user.es_profesional:
        return Response({'error': 'Acceso denegado'}, status=403)

    today = timezone.now().date()
    punto = PuntoAtencion.objects.filter(profesional=user).first()
    if not punto:
        return Response({'error': 'No asignado a un punto de atención'}, status=400)

    # Pacientes atendidos
    pacientes_atendidos = Turno.objects.filter(
        punto_atencion=punto,
        estado='Atendido',
        fecha=today
    ).count()

    # Citas más pedidas
    citas_mas_pedidas = Turno.objects.filter(
        punto_atencion=punto,
        fecha=today
    ).values('tipo_cita').annotate(total=Count('id')).order_by('-total')[:5]

    # Turnos por punto de atención
    turnos_por_punto = Turno.objects.filter(
        punto_atencion=punto,
        fecha=today,
        estado__in=['En espera', 'En progreso']
    ).count()

    return Response({
        'pacientes_atendidos': pacientes_atendidos,
        'citas_mas_pedidas': list(citas_mas_pedidas),
        'turnos_por_punto': turnos_por_punto
    })

# Verificar disponibilidad
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_availability_view(request):
    punto = request.query_params.get('punto')
    fecha = request.query_params.get('fecha')
    if not punto or not fecha:
        return Response({'error': 'Faltan parámetros'}, status=status.HTTP_400_BAD_REQUEST)

    turnos = Turno.objects.filter(punto_atencion_id=punto, fecha_cita__date=fecha)
    occupied_horas = [turno.fecha_cita.strftime('%H:%M') for turno in turnos]
    logger.debug(f"Horas ocupadas para {fecha} en punto {punto}: {occupied_horas}")
    return Response({'occupied': occupied_horas})

# Servicios por punto de atención
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def punto_atencion_services_view(request):
    puntos = PuntoAtencion.objects.filter(activo=True)
    data = {
        punto.id: {
            'nombre': punto.nombre,
            'servicios': punto.servicios_texto.split('\n') if punto.servicios_texto else []
        }
        for punto in puntos
    }
    return Response(data)