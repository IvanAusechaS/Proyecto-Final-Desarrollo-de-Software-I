# backend/tickets/models.py
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.utils import timezone
from django.core.exceptions import ValidationError

class UsuarioManager(BaseUserManager):
    def create_user(self, cedula, nombre, email, password=None):
        if not cedula:
            raise ValueError('La cédula es obligatoria')
        user = self.model(cedula=cedula, nombre=nombre, email=email)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, cedula, nombre, email, password=None):
        user = self.create_user(cedula, nombre, email, password)
        user.is_admin = True
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user

class Usuario(AbstractBaseUser):
    cedula = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=100)
    email = models.EmailField(unique=True, null=True, blank=True)
    es_profesional = models.BooleanField(default=False)
    password = models.CharField(max_length=128, null=True, blank=True)
    reset_password_token = models.CharField(max_length=32, null=True, blank=True)
    
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    objects = UsuarioManager()

    USERNAME_FIELD = 'cedula'
    REQUIRED_FIELDS = ['nombre', 'email']

    def __str__(self):
        return self.cedula

    def has_perm(self, perm, obj=None):
        return self.is_admin or self.is_superuser

    def has_module_perms(self, app_label):
        return self.is_admin or self.is_superuser

class PuntoAtencion(models.Model):
    nombre = models.CharField(max_length=255)
    ubicacion = models.CharField(max_length=255)
    activo = models.BooleanField(default=True)
    servicios_texto = models.TextField(blank=True, default="")
    profesional = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True, limit_choices_to={'es_profesional': True})

    def __str__(self):
        return self.nombre
    
def validate_turno_time(value):
    hour = value.hour
    if not (8 <= hour < 12 or 14 <= hour < 16):
        raise ValidationError('Los turnos solo pueden ser entre 8:00-12:00 o 14:00-16:00.')

class Turno(models.Model):
    ESTADOS = (
        ('En espera', 'En espera'),
        ('En progreso', 'En progreso'),
        ('Atendido', 'Atendido'),
        ('Cancelado', 'Cancelado'),
    )
    numero = models.CharField(max_length=14, unique=True)
    usuario = models.ForeignKey('Usuario', on_delete=models.CASCADE)
    punto_atencion = models.ForeignKey('PuntoAtencion', on_delete=models.CASCADE)
    tipo_cita = models.CharField(max_length=50)
    fecha_cita = models.DateTimeField()  # Quitamos el validador
    estado = models.CharField(max_length=20, choices=ESTADOS, default='En espera')
    fecha_atencion = models.DateTimeField(null=True, blank=True)
    prioridad = models.CharField(max_length=1, choices=[('N', 'Normal'), ('P', 'Alta')], default='N')
    descripcion = models.TextField(blank=True, null=True)


    def __str__(self):
        return f"{self.numero} - {self.usuario.nombre}"