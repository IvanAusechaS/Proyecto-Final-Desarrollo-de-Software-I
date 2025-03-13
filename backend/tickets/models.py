from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.utils import timezone
from django.core.exceptions import ValidationError

class UsuarioManager(BaseUserManager):
    def create_user(self, cedula, email, nombre, password=None, telefono='', es_profesional=False):
        if not cedula:
            raise ValueError('La cédula es obligatoria')
        if not email:
            raise ValueError('El email es obligatorio')
        if not nombre:
            raise ValueError('El nombre es obligatorio')

        user = self.model(
            cedula=cedula,
            email=self.normalize_email(email),
            nombre=nombre,
            telefono=telefono,
            es_profesional=es_profesional,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, cedula, email, nombre, password=None):
        user = self.create_user(
            cedula=cedula,
            email=email,
            nombre=nombre,
            password=password,
            es_profesional=True,
        )
        user.is_admin = True
        user.save(using=self._db)
        return user

class Usuario(AbstractBaseUser):
    cedula = models.CharField(max_length=20, unique=True)
    email = models.EmailField(unique=True)
    nombre = models.CharField(max_length=255)
    telefono = models.CharField(max_length=15, blank=True)
    es_profesional = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)

    objects = UsuarioManager()

    USERNAME_FIELD = 'cedula'
    REQUIRED_FIELDS = ['email', 'nombre']

    def __str__(self):
        return self.nombre

    def has_perm(self, perm, obj=None):
        return self.is_admin

    def has_module_perms(self, app_label):
        return self.is_admin

    @property
    def is_staff(self):
        return self.is_admin

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
    numero = models.CharField(max_length=10, unique=True)
    usuario = models.ForeignKey('Usuario', on_delete=models.CASCADE)
    punto_atencion = models.ForeignKey('PuntoAtencion', on_delete=models.CASCADE)
    tipo_cita = models.CharField(max_length=50)
    fecha_cita = models.DateTimeField(validators=[validate_turno_time])
    estado = models.CharField(max_length=20, choices=ESTADOS, default='En espera')
    fecha_atencion = models.DateTimeField(null=True, blank=True)
    prioridad = models.CharField(max_length=1, choices=[('N', 'Normal'), ('P', 'Alta')])
    descripcion = models.TextField()

    def save(self, *args, **kwargs):
        if not self.numero:
            last_turno = Turno.objects.order_by('-id').first()
            self.numero = f'T{int(last_turno.numero[1:]) + 1 if last_turno else 1:06d}'
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.numero} - {self.usuario.nombre}"