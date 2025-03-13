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

class RegisterView(APIView):
    def post(self, request):
        cedula = request.data.get('cedula')
        nombre = request.data.get('nombre')
        password = request.data.get('password')

        if not all([cedula, nombre, password]):
            return Response({'error': 'Todos los campos son requeridos'}, status=status.HTTP_400_BAD_REQUEST)

        if Usuario.objects.filter(cedula=cedula).exists():
            return Response({'error': 'La cédula ya está registrada'}, status=status.HTTP_400_BAD_REQUEST)

        user = Usuario(
            cedula=cedula,
            nombre=nombre,
            password=make_password(password),  # Hash de la contraseña
            es_profesional=False  # Por defecto, no es profesional
        )
        user.save()

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
        return Response({"detail": "Logout exitoso"}, status=205)

class RegisterView(generics.CreateAPIView):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    permission_classes = [AllowAny]

class BuscarUsuarioPorCedula(APIView):
    def get(self, request, cedula):
        try:
            usuario = Usuario.objects.get(cedula=cedula)
            serializer = UsuarioSerializer(usuario)
            return Response(serializer.data)
        except Usuario.DoesNotExist:
            return Response({"error": "Usuario no encontrado"}, status=404)

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
        return Turno.objects.all()

class TurnoUpdate(generics.UpdateAPIView):
    queryset = Turno.objects.all()
    serializer_class = TurnoSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

class TurnoDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Turno.objects.all()
    serializer_class = TurnoSerializer
    lookup_field = 'id'