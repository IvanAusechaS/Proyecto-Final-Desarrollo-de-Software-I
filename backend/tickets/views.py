from django.core.mail import send_mail
from django.conf import settings
from django.utils.crypto import get_random_string
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib.auth.hashers import make_password
from django.http import JsonResponse
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.decorators import api_view, permission_classes
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomTokenObtainPairSerializer, UsuarioSerializer, PuntoAtencionSerializer, TurnoSerializer, UpdateProfileSerializer
from .models import Usuario, PuntoAtencion, Turno
from django.utils.timezone import localtime
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from django.utils import timezone
from django.db.models import Count
from django.contrib.auth import get_user_model
from .serializers import UsuarioSerializer
from .models import Usuario, PasswordResetCode
from .models import Turno, PuntoAtencion
import logging
import re

logger = logging.getLogger(__name__)
# --- Login ---

@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    email = request.data.get('email')
    password = request.data.get('password')
    user = authenticate(request, username=email, password=password)
    if user:
        logger.debug(f"Usuario autenticado: {email}, es_profesional: {user.es_profesional}, punto_atencion: {user.punto_atencion}")
        token, created = Token.objects.get_or_create(user=user)
        serializer = UsuarioSerializer(user)
        return Response({
            'access': token.key,
            'refresh': token.key,  # Nota: Considera implementar un sistema de refresh token separado
            'user': serializer.data
        })
    return Response({'detail': 'Credenciales incorrectas'}, status=400)
# --- Eliminar punto de atención ---

# --- Actualizar servicios de punto de atención ---
@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def update_punto_servicios_view(request, pk):
    from .models import PuntoAtencion
    servicios = request.data.get('servicios_texto')
    if servicios is None:
        return Response({'error': 'Debe enviar el campo servicios_texto'}, status=400)
    try:
        punto = PuntoAtencion.objects.get(pk=pk)
        punto.servicios_texto = servicios
        punto.save()
        return Response({'message': 'Servicios actualizados correctamente'}, status=200)
    except PuntoAtencion.DoesNotExist:
        return Response({'error': 'Punto de atención no encontrado'}, status=404)


@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def punto_atencion_delete_view(request, pk):
    try:
        punto = PuntoAtencion.objects.get(pk=pk)
        punto.delete()
        return Response({'message': 'Punto de atención eliminado correctamente'}, status=status.HTTP_204_NO_CONTENT)
    except PuntoAtencion.DoesNotExist:
        return Response({'error': 'Punto de atención no encontrado'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def usuario_delete_view(request, id):
    try:
        usuario = Usuario.objects.get(id=id)
        usuario.delete()
        return Response({'message': 'Usuario eliminado correctamente'}, status=status.HTTP_204_NO_CONTENT)
    except Usuario.DoesNotExist:
        return Response({'error': 'Usuario no encontrado'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET', 'POST'])
@permission_classes([IsAdminUser])
def usuarios_list_create_view(request):
    if request.method == 'GET':
        usuarios = Usuario.objects.all()
        serializer = UsuarioSerializer(usuarios, many=True)
        return Response(serializer.data)
    elif request.method == 'POST':
        serializer = UsuarioSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(UsuarioSerializer(user).data, status=201)
        return Response(serializer.errors, status=400)

logger = logging.getLogger(__name__)

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

# Registro de usuarios con email
@api_view(['POST'])
@permission_classes([AllowAny])
def register_view(request):
    logger.debug(f"Datos recibidos: {request.data}")
    serializer = UsuarioSerializer(data=request.data)
    if serializer.is_valid():
        try:
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
        except Exception as e:
            logger.error(f"Error al registrar usuario: {str(e)}")
            return Response({
                'error': 'Error al registrar el usuario',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        logger.debug(f"Errores de validación completos: {serializer.errors}")
        # Verificar si el error es por correo duplicado
        errors = serializer.errors
        if 'email' in errors:
            for error in errors['email']:
                if isinstance(error, dict) and 'Ya existe usuario con este email' in str(error.get('message', '')):
                    logger.warning(f"Correo duplicado detectado: {request.data['email']}")
                    return Response({
                        'error': 'El correo electrónico ya está registrado',
                        'details': 'Por favor, usa otro correo o inicia sesión.'
                    }, status=status.HTTP_400_BAD_REQUEST)
                elif 'Ya existe usuario con este email' in str(error):
                    logger.warning(f"Correo duplicado detectado: {request.data['email']}")
                    return Response({
                        'error': 'El correo electrónico ya está registrado',
                        'details': 'Por favor, usa otro correo o inicia sesión.'
                    }, status=status.HTTP_400_BAD_REQUEST)
        logger.error(f"Errores de validación no manejados: {serializer.errors}")
        return Response({'error': 'Datos inválidos', 'details': serializer.errors}, status=400)

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
    today = localtime(timezone.now()).date()
    turnos_en_progreso = Turno.objects.filter(
        estado='En progreso',
        fecha=today
    ).order_by('prioridad', 'numero')  # Cambiamos fecha_cita por numero

    current_turnos = {}
    estimated_times = {}
    for punto in PuntoAtencion.objects.all():
        turno = turnos_en_progreso.filter(punto_atencion=punto).first()
        current_turnos[punto.id] = turno.numero if turno else 'Ninguno'
        turnos_espera = Turno.objects.filter(
            punto_atencion=punto,
            estado='En espera',
            fecha=today
        ).order_by('prioridad', 'numero').count()
        estimated_times[punto.id] = turnos_espera * 15  # minutos

    return Response({
        'current_turnos': current_turnos,
        'estimated_times': estimated_times
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_turno_view(request):
    user = request.user
    data = request.data.copy()
    
    # Log incoming data for debugging
    logger.debug(f"Datos recibidos del frontend: {data}")

    # Serializar y validar los datos
    serializer = TurnoSerializer(data=data, context={'request': request})
    if serializer.is_valid():
        turno = serializer.save(usuario=user)
        logger.info(f"Turno creado: {turno.numero} para usuario {user.email}, fecha: {turno.fecha}, prioridad: {turno.prioridad}")
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    # Log errors for debugging
    logger.error(f"Error al crear turno: {serializer.errors}")
    return Response({'errors': serializer.errors, 'received_data': data}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_turnos_view(request):
    try:
        turnos = Turno.objects.filter(usuario=request.user)
        serializer = TurnoSerializer(turnos, many=True, context={'request': request})
        logger.debug(f"Turnos listados para usuario {request.user.email}: {len(turnos)} turnos")
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Error al listar turnos: {str(e)}")
        return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

# views.py
class ProfesionalTurnosList(generics.ListAPIView):
    serializer_class = TurnoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        logger.debug(f"Usuario autenticado: {user.email}, es_profesional: {user.es_profesional}, punto_atencion_id: {user.punto_atencion_id}")

        if not user.es_profesional:
            logger.warning(f"Usuario {user.email} no es profesional")
            return Turno.objects.none()

        # Usar punto_atencion_id del usuario en lugar de profesional
        if not user.punto_atencion_id:
            logger.warning(f"Usuario {user.email} no está asignado a un punto de atención")
            return Turno.objects.none()

        today = localtime(timezone.now()).date()
        logger.debug(f"Fecha actual (today): {today}")

        # Filtrar turnos por punto_atencion_id del usuario
        turnos = Turno.objects.filter(
            punto_atencion_id=user.punto_atencion_id,
            fecha=today
        ).order_by('prioridad', 'numero')

        logger.debug(f"Turnos encontrados: {list(turnos)}")
        return turnos

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        ret = serializer.data
        logger.debug(f"Serializer data: {ret}")
        return Response(ret)
from .models import Turno, PuntoAtencion

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_turnos_colas(request):
    today = timezone.now().date()
    punto_atencion_id = request.query_params.get('punto_atencion_id')
    fecha = request.query_params.get('fecha', today)  # Usar fecha proporcionada o la actual
    if not punto_atencion_id or not punto_atencion_id.isdigit():
        return Response({'error': 'Se requiere un punto_atencion_id válido'}, status=400)

    try:
        punto_atencion_id = int(punto_atencion_id)
        punto = PuntoAtencion.objects.get(id=punto_atencion_id, activo=True)
        user = request.user
        logger.debug(f"Usuario: {user.email}, es_profesional: {user.es_profesional}, punto_atencion_id: {user.punto_atencion_id}")

        if user.es_profesional:
            if user.punto_atencion_id is None:
                logger.warning(f"Profesional {user.email} no tiene punto_atencion_id asignado")
                return Response({'error': 'No estás asignado a un punto de atención'}, status=403)
            if user.punto_atencion_id != punto_atencion_id:
                logger.warning(f"Profesional {user.email} intenta acceder a punto_atencion_id {punto_atencion_id} pero está asignado a {user.punto_atencion_id}")
                return Response({'error': 'No estás autorizado para este punto de atención'}, status=403)
        else:
            if not Turno.objects.filter(usuario=user, punto_atencion_id=punto_atencion_id, fecha=fecha).exists():
                logger.warning(f"Usuario {user.email} no tiene turnos en punto_atencion_id {punto_atencion_id} para fecha {fecha}")
                return Response({'error': 'No tienes turnos en este punto de atención para la fecha indicada'}, status=403)

    except PuntoAtencion.DoesNotExist:
        logger.error(f"Punto de atención {punto_atencion_id} no encontrado o inactivo")
        return Response({'error': 'Punto de atención no encontrado o inactivo'}, status=400)
    except ValueError:
        logger.error(f"punto_atencion_id {punto_atencion_id} no es un número válido")
        return Response({'error': 'punto_atencion_id debe ser un número válido'}, status=400)

    # Obtener TODOS los turnos para la fecha especificada (sin filtrar por estado)
    turnos = Turno.objects.filter(
        punto_atencion_id=punto_atencion_id,
        fecha=fecha
    ).select_related('usuario', 'punto_atencion').order_by('numero')

    # Reordenar solo los turnos en espera para mantener la lógica existente
    turno_en_progreso = turnos.filter(estado='En progreso').first()
    turnos_en_espera = turnos.filter(estado='En espera').order_by('prioridad', 'numero')
    turnos_prioritarios = [t for t in turnos_en_espera if t.prioridad == 'P']
    turnos_normales = [t for t in turnos_en_espera if t.prioridad == 'N']

    turnos_ordenados = []
    if turno_en_progreso:
        turnos_ordenados.append(turno_en_progreso)

    i, j = 0, 0
    while i < len(turnos_prioritarios) or j < len(turnos_normales):
        if i < len(turnos_prioritarios):
            turnos_ordenados.append(turnos_prioritarios[i])
            i += 1
        if j < len(turnos_normales):
            turnos_ordenados.append(turnos_normales[j])
            j += 1
            if j < len(turnos_normales):
                turnos_ordenados.append(turnos_normales[j])
                j += 1

    # Añadir los turnos no en espera (Atendido, Cancelado, etc.) al final
    turnos_restantes = turnos.exclude(id__in=[t.id for t in turnos_ordenados])
    turnos_ordenados.extend(turnos_restantes)

    serializer = TurnoSerializer(turnos_ordenados, many=True)
    logger.debug(f"Turnos devueltos para punto_atencion_id {punto_atencion_id} y fecha {fecha}: {serializer.data}")
    return Response({'turnos': serializer.data}, status=200)

class TurnoDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Turno.objects.all()
    serializer_class = TurnoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if not user.es_profesional:
            logger.warning(f"Usuario {user.email} no es profesional")
            return Turno.objects.none()
        punto_atencion_id = getattr(user, 'punto_atencion_id', None)
        if not punto_atencion_id:
            logger.warning(f"Usuario {user.email} no tiene punto_atencion_id asignado")
            return Turno.objects.none()
        logger.debug(f"Filtrando turnos para punto_atencion_id: {punto_atencion_id}")
        return Turno.objects.filter(punto_atencion_id=punto_atencion_id)

    def get_object(self):
        queryset = self.get_queryset()
        obj = generics.get_object_or_404(queryset, id=self.kwargs['pk'])
        return obj

    def perform_update(self, serializer):
        if 'estado' in self.request.data:
            serializer.save()
        else:
            raise ValidationError("Solo se permite actualizar el estado del turno.")

    def update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        try:
            logger.debug(f"Datos recibidos para actualizar turno {kwargs.get('pk')}: {request.data}")
            response = super().update(request, *args, **kwargs)
            logger.debug(f"Turno {kwargs.get('pk')} actualizado exitosamente: {response.data}")
            return response
        except ValidationError as e:
            logger.error(f"Error al actualizar turno {kwargs.get('pk')}: {str(e)}")
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except ObjectDoesNotExist:
            logger.error(f"Turno {kwargs.get('pk')} no encontrado")
            return Response({'detail': 'Turno no encontrado'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error inesperado al actualizar turno {kwargs.get('pk')}: {str(e)}")
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def destroy(self, request, *args, **kwargs):
        try:
            logger.debug(f"Eliminando turno {kwargs.get('pk')}")
            response = super().destroy(request, *args, **kwargs)
            logger.debug(f"Turno {kwargs.get('pk')} eliminado exitosamente")
            return response
        except ObjectDoesNotExist:
            logger.error(f"Turno {kwargs.get('pk')} no encontrado para eliminar")
            return Response({'detail': 'Turno no encontrado'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error inesperado al eliminar turno {kwargs.get('pk')}: {str(e)}")
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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

# Solicitar codigo de restablecimiento
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

    # Invalidar códigos anteriores
    PasswordResetCode.objects.filter(user=user, is_used=False).update(is_used=True)

    # Generar nuevo código
    reset_code = PasswordResetCode.objects.create(
        user=user,
        code=PasswordResetCode.generate_code()
    )

    # Enviar código por correo
    subject = 'Código para restablecer tu contraseña'
    message = f"""Hola {user.nombre},

Has solicitado restablecer tu contraseña.

Tu código de verificación es: {reset_code.code}

Este código expira en 15 minutos.

Si no solicitaste este cambio, ignora este correo.

Saludos,
Equipo de Soporte"""

    from_email = settings.EMAIL_HOST_USER
    recipient_list = [email]

    try:
        send_mail(subject, message, from_email, recipient_list, fail_silently=False)
        logger.info(f"Código de restablecimiento enviado a {email}")
        return Response({
            'message': 'Se ha enviado un código de verificación a tu correo electrónico'
        }, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Error al enviar correo: {str(e)}")
        return Response({
            'error': 'Error al enviar el correo de restablecimiento'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
# Verificar código de restablecimiento
@api_view(['POST'])
@permission_classes([AllowAny])
def verify_reset_code_view(request):
    email = request.data.get('email')
    code = request.data.get('code')

    if not email or not code:
        return Response({'error': 'Email y código son requeridos'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = Usuario.objects.get(email=email)
        reset_code = PasswordResetCode.objects.get(
            user=user,
            code=code,
            is_used=False
        )

        if reset_code.is_expired():
            return Response({'error': 'El código ha expirado'}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'message': 'Código verificado correctamente',
            'valid': True
        }, status=status.HTTP_200_OK)

    except Usuario.DoesNotExist:
        return Response({'error': 'Usuario no encontrado'}, status=status.HTTP_400_BAD_REQUEST)
    except PasswordResetCode.DoesNotExist:
        return Response({'error': 'Código inválido'}, status=status.HTTP_400_BAD_REQUEST)

# Confirmar restablecimiento de contraseña
@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password_confirm_view(request):
    email = request.data.get('email')
    code = request.data.get('code')
    new_password = request.data.get('new_password')

    if not email or not code or not new_password:
        return Response({
            'error': 'Email, código y nueva contraseña son requeridos'
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = Usuario.objects.get(email=email)
        reset_code = PasswordResetCode.objects.get(
            user=user,
            code=code,
            is_used=False
        )

        if reset_code.is_expired():
            return Response({'error': 'El código ha expirado'}, status=status.HTTP_400_BAD_REQUEST)

        # Actualizar contraseña
        user.set_password(new_password)
        user.save()

        # Marcar código como usado
        reset_code.is_used = True
        reset_code.save()

        logger.info(f"Contraseña restablecida para {email}")
        return Response({
            'message': 'Contraseña actualizada correctamente'
        }, status=status.HTTP_200_OK)

    except Usuario.DoesNotExist:
        return Response({'error': 'Usuario no encontrado'}, status=status.HTTP_400_BAD_REQUEST)
    except PasswordResetCode.DoesNotExist:
        return Response({'error': 'Código inválido'}, status=status.HTTP_400_BAD_REQUEST)


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
    recipient_list = ['sitema.atenciondsi@gmail.com']  

    try:
        logger.info(f"Intentando enviar email desde {from_email} hacia {recipient_list}")
        logger.info(f"Asunto: {subject}")
        
        result = send_mail(
            subject, 
            body, 
            from_email, 
            recipient_list, 
            fail_silently=False
        )
        
        logger.info(f"send_mail devolvió: {result}")
        return Response({'message': 'Mensaje enviado exitosamente'}, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error al enviar correo: {str(e)}")
        return Response({'error': 'Error al enviar el mensaje'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Actualizar perfil
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_profile_view(request):
    user = request.user
    serializer = UpdateProfileSerializer(user, data={'nombre': request.data.get('name'), 'email': request.data.get('email')}, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response({'message': 'Perfil actualizado', 'user': serializer.data}, status=200)
    return Response(serializer.errors, status=400)

# Profesionales por punto de atención
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def punto_profesionales_view(request, pk):
    profesionales = Usuario.objects.filter(puntoatencion__id=pk, es_profesional=True)
    serializer = UsuarioSerializer(profesionales, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profesional_stats_view(request):
    user = request.user
    if not user.es_profesional:
        logger.warning(f"Usuario {user.email} no es profesional")
        return Response({'error': 'Acceso denegado'}, status=403)

    today = localtime(timezone.now()).date()
    punto = PuntoAtencion.objects.filter(profesional=user).first()
    if not punto:
        logger.warning(f"Usuario {user.email} no está asignado a un punto de atención")
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

    # Turnos por punto de atención (en espera o en progreso)
    turnos_por_punto = Turno.objects.filter(
        punto_atencion=punto,
        fecha=today,
        estado__in=['En espera', 'En progreso']
    ).count()

    # Distribución por prioridad
    turnos_por_prioridad = Turno.objects.filter(
        punto_atencion=punto,
        fecha=today
    ).values('prioridad').annotate(total=Count('id'))

    prioridad_data = {'Prioritario': 0, 'Normal': 0}
    for item in turnos_por_prioridad:
        key = 'Prioritario' if item['prioridad'] == 'P' else 'Normal'
        prioridad_data[key] = item['total']

    # Obtener todos los turnos del punto de atención para el día actual
    turnos = Turno.objects.filter(
    punto_atencion=punto,
    fecha=today
    ).order_by('prioridad', 'numero')


    return Response({
        'pacientes_atendidos': pacientes_atendidos,
        'citas_mas_pedidas': list(citas_mas_pedidas),
        'turnos_por_punto': turnos_por_punto,
        'prioridad_data': prioridad_data,
        'turnos': turnos_serializer.data  # Añadimos los turnos completos
    })

# Verificar disponibilidad
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_availability_view(request):
    punto = request.query_params.get('punto')
    fecha = request.query_params.get('fecha')
    if not punto or not fecha:
        return Response({'error': 'Faltan parámetros'}, status=status.HTTP_400_BAD_REQUEST)

    turnos = Turno.objects.filter(punto_atencion_id=punto, fecha=fecha)
    occupied_horas = [turno.numero for turno in turnos]  # Cambiamos a numero como identificador
    logger.debug(f"Turnos ocupados para {fecha} en punto {punto}: {occupied_horas}")
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

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def pending_turnos_by_service(request):
    puntos = PuntoAtencion.objects.filter(activo=True)
    hoy =  localtime(timezone.now()).date()
    mañana = hoy + timezone.timedelta(days=1)
    resultados = []

    for punto in puntos:
        turnos_prioritarios = Turno.objects.filter(
            punto_atencion=punto,
            prioridad='P',
            estado='En espera',
            fecha_cita__gte=hoy,
            fecha_cita__lt=mañana
        ).order_by('fecha_cita')

        turnos_normales = Turno.objects.filter(
            punto_atencion=punto,
            prioridad='N',
            estado='En espera',
            fecha_cita__gte=hoy,
            fecha_cita__lt=mañana
        ).order_by('fecha_cita')

        cola_prioritarios = []
        for turno in turnos_prioritarios:
            cola_prioritarios.append({
                'id': turno.id,
                'codigo_turno': turno.numero,
                'fecha_creacion': turno.fecha_cita
            })

        cola_normales = []
        for turno in turnos_normales:
            cola_normales.append({
                'id': turno.id,
                'codigo_turno': turno.numero,
                'fecha_creacion': turno.fecha_cita
            })

        resultados.append({
            'punto_atencion_id': punto.id,
            'punto_atencion_nombre': punto.nombre,
            'cola_prioritarios': cola_prioritarios,
            'cola_normales': cola_normales
        })

    return Response(resultados)

User = get_user_model()

@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def cambiar_rol_usuario(request, id):
    try:
        usuario = Usuario.objects.get(id=id)
    except Usuario.DoesNotExist:
        return Response(
            {"error": "Usuario no encontrado"},
            status=status.HTTP_404_NOT_FOUND
        )

    nuevo_rol = request.data.get('rol')
    roles_validos = ['usuario', 'profesional', 'admin']

    if not nuevo_rol or nuevo_rol not in roles_validos:
        return Response(
            {"error": f"Rol no válido. Debe ser uno de: {', '.join(roles_validos)}"},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Limpiar todos los roles primero
    usuario.rol = nuevo_rol
    usuario.es_profesional = False
    usuario.is_admin = False
    usuario.is_staff = False
    usuario.is_superuser = False

    # Asignar el nuevo rol con flags
    if nuevo_rol == 'admin':
        usuario.is_admin = True
        usuario.is_staff = True
        usuario.is_superuser = True
    elif nuevo_rol == 'profesional':
        usuario.es_profesional = True
    # 'usuario' no necesita más cambios

    usuario.save()

    return Response(
        {"mensaje": f"Rol actualizado a {nuevo_rol} correctamente"},
        status=status.HTTP_200_OK
)

# --- Asignar punto de atención a profesional ---
@api_view(['POST'])
@permission_classes([IsAdminUser])
def asignar_punto_a_profesional(request):
    profesional_id = request.data.get('profesional_id')
    punto_atencion_id = request.data.get('punto_atencion_id')
    if not profesional_id:
        return Response({'error': 'Se requiere profesional_id'}, status=400)
    try:
        profesional = Usuario.objects.get(id=profesional_id, es_profesional=True)
    except Usuario.DoesNotExist:
        return Response({'error': 'Profesional no encontrado'}, status=404)
    punto = None
    if punto_atencion_id:
        try:
            punto = PuntoAtencion.objects.get(id=punto_atencion_id)
        except PuntoAtencion.DoesNotExist:
            return Response({'error': 'Punto de atención no encontrado'}, status=404)
    profesional.punto_atencion = punto
    profesional.save()
    return Response({'message': 'Punto de atención asignado correctamente'}, status=200)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_turno(request, turno_id):
    try:
        turno = Turno.objects.get(id=turno_id)
        serializer = TurnoSerializer(turno, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Turno.DoesNotExist:
        return Response({'error': 'Turno no encontrado'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@api_view(['GET'])
def get_all_turnos(request, punto_atencion_id, fecha):
    try:
        turnos = Turno.objects.filter(
            punto_atencion_id=punto_atencion_id,
            fecha=fecha
        ).select_related('usuario', 'punto_atencion')
        serializer = TurnoSerializer(turnos, many=True)
        return JsonResponse(serializer.data, safe=False, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
