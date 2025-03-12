from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomTokenObtainPairSerializer, UsuarioSerializer, PuntoAtencionSerializer, TurnoSerializer
from .models import Usuario, PuntoAtencion, Turno

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