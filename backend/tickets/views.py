# backend/tickets/views.py
from decouple import config
from django.core.mail import send_mail
from django.conf import settings
from django.utils.crypto import get_random_string
from django.contrib.auth.admin import UserAdmin
import firebase_admin
from rest_framework import viewsets
from firebase_admin import auth, credentials
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomTokenObtainPairSerializer, UsuarioSerializer, PuntoAtencionSerializer, TurnoSerializer
from django.contrib.auth.hashers import make_password
from .models import Usuario, PuntoAtencion, Turno
import logging
from django.utils import timezone
import datetime

logger = logging.getLogger(__name__)

if not firebase_admin._apps:
    cred = credentials.Certificate(config('FIREBASE_CREDENTIALS'))
    firebase_admin.initialize_app(cred)

# Inicializar Firebase Admin SDK (solo una vez)
if not firebase_admin._apps:
    cred = credentials.Certificate('C:/Users/ivana/.vscode/Proyecto DSI/backend/credentials/sistema-atencion-dsi-firebase-adminsdk-fbsvc-d425066aa4.json')
    firebase_admin.initialize_app(cred)

class FirebaseLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        id_token = request.data.get('id_token')
        if not id_token:
            return Response({'error': 'Token de Firebase requerido'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            decoded_token = auth.verify_id_token(id_token)
            email = decoded_token['email']
            name = decoded_token.get('name', 'Usuario Google')
        except Exception as e:
            logger.error(f"Error verificando token de Firebase: {str(e)}")
            return Response({'error': 'Token inválido'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = Usuario.objects.get(email=email)
            needs_cedula = not user.cedula or user.cedula == email.split('@')[0]
        except Usuario.DoesNotExist:
            user = Usuario.objects.create_user(
                cedula=email.split('@')[0],
                email=email,
                nombre=name,
                password=None,
            )
            needs_cedula = True

        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': {
                'id': user.id,
                'nombre': user.nombre,
                'cedula': user.cedula,
                'email': user.email,
                'es_profesional': user.es_profesional,
                'needs_cedula': needs_cedula
            }
        }, status=status.HTTP_200_OK)

class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        logger.debug(f"Datos recibidos: {request.data}")
        cedula = request.data.get('cedula')
        nombre = request.data.get('nombre')
        email = request.data.get('email')
        password = request.data.get('password')

        if not all([cedula, nombre, email, password]):
            logger.error("Faltan campos requeridos")
            return Response({'error': 'Todos los campos son requeridos'}, status=status.HTTP_400_BAD_REQUEST)

        if Usuario.objects.filter(cedula=cedula).exists():
            logger.error(f"Cédula {cedula} ya registrada")
            return Response({'error': 'La cédula ya está registrada'}, status=status.HTTP_400_BAD_REQUEST)
        if Usuario.objects.filter(email=email).exists():
            logger.error(f"Email {email} ya registrado")
            return Response({'error': 'El correo ya está registrado'}, status=status.HTTP_400_BAD_REQUEST)

        user = Usuario(
            cedula=cedula,
            nombre=nombre,
            email=email,
            password=make_password(password),
            es_profesional=False
        )
        user.save()
        logger.info(f"Usuario {cedula} registrado exitosamente")

        refresh = RefreshToken.for_user(user)
        token_data = {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': {
                'id': user.id,
                'cedula': user.cedula,
                'email': user.email,
                'nombre': user.nombre,
                'es_profesional': user.es_profesional
            }
        }
        return Response(token_data, status=status.HTTP_201_CREATED)

class ResetPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({'error': 'Correo electrónico requerido'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = Usuario.objects.get(email=email)
        except Usuario.DoesNotExist:
            return Response({'error': 'No existe un usuario con este correo'}, status=status.HTTP_400_BAD_REQUEST)

        token = get_random_string(length=32)
        user.reset_password_token = token
        user.save()

        reset_link = f"http://localhost:3000/reset-password-confirm?token={token}"
        subject = 'Restablecer tu contraseña'
        message = f'Hola {user.nombre},\n\nHaz clic en este enlace para restablecer tu contraseña: {reset_link}\n\nEste enlace es válido por 1 hora.'
        from_email = settings.EMAIL_HOST_USER
        recipient_list = [email]

        try:
            send_mail(subject, message, from_email, recipient_list, fail_silently=False)
            logger.info(f"Correo de restablecimiento enviado a {email}")
            return Response({'message': 'Se ha enviado un correo para restablecer tu contraseña'}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error al enviar correo: {str(e)}")
            return Response({'error': 'Error al enviar el correo de restablecimiento'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ResetPasswordConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
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

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        return Response({"detail": "Logout exitoso"}, status=status.HTTP_205_RESET_CONTENT)

class BuscarUsuarioPorCedula(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, cedula):
        try:
            usuario = Usuario.objects.get(cedula=cedula)
            serializer = UsuarioSerializer(usuario)
            return Response(serializer.data)
        except Usuario.DoesNotExist:
            return Response({"error": "Usuario no encontrado"}, status=status.HTTP_404_NOT_FOUND)

class CurrentTurnosView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = timezone.now().date()
        melendez = Turno.objects.filter(
            punto_atencion_id=1,
            fecha_cita__date=today,
            estado='En espera'
        ).order_by('numero').first()
        polvorines = Turno.objects.filter(
            punto_atencion_id=2,
            fecha_cita__date=today,
            estado='En espera'
        ).order_by('numero').first()

        melendez_count = Turno.objects.filter(
            punto_atencion_id=1,
            fecha_cita__date=today,
            estado='En espera'
        ).count()
        polvorines_count = Turno.objects.filter(
            punto_atencion_id=2,
            fecha_cita__date=today,
            estado='En espera'
        ).count()

        return Response({
            'melendez': melendez.numero if melendez else 'Ninguno',
            'polvorines': polvorines.numero if polvorines else 'Ninguno',
            'melendezTime': melendez_count * 10,
            'polvorinesTime': polvorines_count * 10,
        })

class TurnoListCreate(generics.ListCreateAPIView):
    queryset = Turno.objects.all()
    serializer_class = TurnoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if not user.is_active:
            return Turno.objects.none()
        if user.is_admin or user.is_superuser:
            return Turno.objects.all()
        elif user.es_profesional:
            return Turno.objects.filter(punto_atencion__profesional=user)
        return Turno.objects.filter(usuario=user)

    def perform_create(self, serializer):
        user = self.request.user
        if not user.is_active:
            raise ValidationError("Usuario inactivo no puede crear turnos")
        punto_atencion = serializer.validated_data['punto_atencion']
        if not punto_atencion.activo:
            raise ValidationError("El punto de atención no está activo")
        if user.es_profesional and punto_atencion.profesional != user:
            raise ValidationError("Solo puedes crear turnos en tu punto de atención")

        today = timezone.now()
        date_str = today.strftime('%d%m%y')  # Ej. 240325
        prefix = f"T{str(punto_atencion.id).zfill(2)}{date_str}"  # Ej. T01240325 (9 caracteres)
        
        last_turno = Turno.objects.filter(
            punto_atencion=punto_atencion,
            fecha_cita__date=today.date(),
            numero__startswith=prefix
        ).order_by('numero').last()
        
        if last_turno:
            last_num = int(last_turno.numero[9:])  # Extrae los últimos 4 dígitos después de T01DDMMYY
            new_num = last_num + 1
        else:
            new_num = 1
        numero = f"{prefix}{new_num:04d}"  # Ej. T012403250001 (13 caracteres)
        
        serializer.save(usuario=user, fecha_cita=today, numero=numero)

class TurnoDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Turno.objects.all()
    serializer_class = TurnoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if not user.is_active:
            return Turno.objects.none()
        if user.is_admin or user.is_superuser:
            return Turno.objects.all()
        elif user.es_profesional:
            return Turno.objects.filter(punto_atencion__profesional=user)
        return Turno.objects.filter(usuario=user)

    def perform_update(self, serializer):
        user = self.request.user
        turno = self.get_object()
        if user.es_profesional and turno.punto_atencion.profesional != user:
            raise ValidationError("No tienes permiso para modificar este turno")
        if not user.is_admin and not user.es_profesional and turno.usuario != user:
            raise ValidationError("No puedes modificar turnos de otros usuarios")

        new_estado = self.request.data.get('estado')
        if new_estado == 'Cancelado' and turno.fecha_cita <= timezone.now():
            raise ValidationError("No puedes cancelar turnos pasados")
        serializer.save()

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

class UpdateCedulaView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
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

class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
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

class PuntoAtencionViewSet(viewsets.ModelViewSet):
    queryset = PuntoAtencion.objects.all()
    serializer_class = PuntoAtencionSerializer
    permission_classes = [IsAuthenticated]

class ContactView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
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

class UpdateProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        user = request.user
        name = request.data.get('name', user.nombre)
        email = request.data.get('email', user.email)

        user.nombre = name
        user.email = email or None
        user.save()

        serializer = UsuarioSerializer(user)
        return Response({'message': 'Perfil actualizado', 'user': serializer.data}, status=status.HTTP_200_OK)

class PuntoProfesionalesView(APIView):
    def get(self, request, pk):
        profesionales = Usuario.objects.filter(puntoatencion__id=pk, es_profesional=True)
        serializer = UsuarioSerializer(profesionales, many=True)
        return Response(serializer.data)

class CheckAvailabilityView(APIView):
    def get(self, request):
        punto = request.query_params.get('punto')
        fecha = request.query_params.get('fecha')
        if not punto or not fecha:
            return Response({'error': 'Faltan parámetros'}, status=400)

        turnos = Turno.objects.filter(punto_atencion_id=punto, fecha_cita__date=fecha)
        occupied_horas = [turno.fecha_cita.strftime('%H:%M') for turno in turnos]
        print(f"Horas ocupadas para {fecha} en punto {punto}: {occupied_horas}")
        return Response({'occupied': occupied_horas})
    
class PuntoAtencionServicesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        puntos = PuntoAtencion.objects.filter(activo=True)
        data = {
            punto.id: {
                'nombre': punto.nombre,
                'servicios': punto.servicios_texto.split('\n') if punto.servicios_texto else []
            }
            for punto in puntos
        }
        return Response(data)