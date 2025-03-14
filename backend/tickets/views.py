# backend/tickets/views.py
from decouple import config
import firebase_admin
from firebase_admin import auth, credentials
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomTokenObtainPairSerializer, UsuarioSerializer, PuntoAtencionSerializer, TurnoSerializer
from django.contrib.auth.hashers import make_password
from .models import Usuario, PuntoAtencion, Turno
import logging
import os

logger = logging.getLogger(__name__)

if not firebase_admin._apps:
    cred = credentials.Certificate(config('FIREBASE_CREDENTIALS'))
    firebase_admin.initialize_app(cred)

# Inicializar Firebase Admin SDK (solo una vez)
if not firebase_admin._apps:
    cred = credentials.Certificate('C:/Users/ivana/.vscode/Proyecto DSI/backend/credentials/sistema-atencion-dsi-firebase-adminsdk-fbsvc-d425066aa4.json')
    firebase_admin.initialize_app(cred)

# Otras vistas (RegisterView, CustomTokenObtainPairView, etc.) sin cambios...

class FirebaseLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        id_token = request.data.get('id_token')
        if not id_token:
            return Response({'error': 'Token de Firebase requerido'}, status=status.HTTP_400_BAD_REQUEST)

        # Verificar el token con Firebase Admin SDK
        try:
            decoded_token = auth.verify_id_token(id_token)
            email = decoded_token['email']
            name = decoded_token.get('name', 'Usuario Google')
        except Exception as e:
            logger.error(f"Error verificando token de Firebase: {str(e)}")
            return Response({'error': 'Token inválido'}, status=status.HTTP_400_BAD_REQUEST)

        # Buscar o crear usuario en la base de datos
        try:
            user = Usuario.objects.get(email=email)
            needs_cedula = not user.cedula or user.cedula == email.split('@')[0]
        except Usuario.DoesNotExist:
            user = Usuario.objects.create_user(
                cedula=email.split('@')[0],  # Cédula temporal
                email=email,
                nombre=name,
                password=None,
            )
            needs_cedula = True

        # Generar tokens JWT
        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': {
                'id': user.id,
                'nombre': user.nombre,
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
        password = request.data.get('password')

        if not all([cedula, nombre, password]):
            logger.error("Faltan campos requeridos")
            return Response({'error': 'Todos los campos son requeridos'}, status=status.HTTP_400_BAD_REQUEST)

        if Usuario.objects.filter(cedula=cedula).exists():
            logger.error(f"Cédula {cedula} ya registrada")
            return Response({'error': 'La cédula ya está registrada'}, status=status.HTTP_400_BAD_REQUEST)

        user = Usuario(
            cedula=cedula,
            nombre=nombre,
            password=make_password(password),
            es_profesional=False
        )
        user.save()
        logger.info(f"Usuario {cedula} registrado exitosamente")

        refresh = RefreshToken.for_user(user)
        token_data = {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': {'id': user.id, 'nombre': user.nombre, 'es_profesional': user.es_profesional}
        }
        return Response(token_data, status=status.HTTP_201_CREATED)

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

class PuntoAtencionListCreate(generics.ListCreateAPIView):
    queryset = PuntoAtencion.objects.all()
    serializer_class = PuntoAtencionSerializer
    permission_classes = [AllowAny]

class TurnoListCreate(generics.ListCreateAPIView):
    serializer_class = TurnoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.es_profesional:
            return Turno.objects.filter(punto_atencion__profesional=user)
        return Turno.objects.filter(usuario=user)

    def perform_create(self, serializer):
        logger.debug(f"Datos recibidos para crear turno: {self.request.data}")
        serializer.save(usuario=self.request.user)

class TurnoDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Turno.objects.all()
    serializer_class = TurnoSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'
    http_method_names = ['get', 'put', 'patch', 'delete']

class UpdateCedulaView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        cedula = request.data.get('cedula')
        if not cedula:
            return Response({'error': 'Cédula requerida'}, status=status.HTTP_400_BAD_REQUEST)
        
        if Usuario.objects.filter(cedula=cedula).exclude(id=user.id).exists():
            return Response({'error': 'La cédula ya está registrada'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Validación básica de cédula (solo números, 6-20 dígitos)
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