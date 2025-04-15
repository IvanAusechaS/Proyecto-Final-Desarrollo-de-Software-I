from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.utils import timezone
from django.core.exceptions import ValidationError
import logging

logger = logging.getLogger(__name__)

class UsuarioManager(BaseUserManager):
    def create_user(self, email, nombre, password=None, cedula=None, es_profesional=False, **extra_fields):
        if not email:
            raise ValueError('El correo electrónico es obligatorio')
        email = self.normalize_email(email)
        user = self.model(
            email=email,
            nombre=nombre,
            cedula=cedula,
            es_profesional=es_profesional,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, nombre, password=None, cedula=None, es_profesional=False, **extra_fields):
        extra_fields.setdefault('is_admin', True)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_admin') is not True:
            raise ValueError('Superuser debe tener is_admin=True.')
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser debe tener is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser debe tener is_superuser=True.')

        return self.create_user(email, nombre, password, cedula, es_profesional, **extra_fields)

class Usuario(AbstractBaseUser):
    email = models.EmailField(unique=True)
    nombre = models.CharField(max_length=100)
    cedula = models.CharField(max_length=20, unique=True, null=True, blank=True)
    es_profesional = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    objects = UsuarioManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nombre']

    def __str__(self):
        return self.email

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
    # Asegurarse de que el datetime tenga una zona horaria
    if timezone.is_naive(value):
        value = timezone.make_aware(value, timezone.get_default_timezone())
    # Convertir a la zona horaria local del servidor
    local_time = value.astimezone(timezone.get_default_timezone())
    hour = local_time.hour
    if not (8 <= hour < 12 or 14 <= hour < 16):
        raise ValidationError('Los turnos solo pueden ser entre 8:00-12:00 o 14:00-16:00.')

class Turno(models.Model):
    ESTADO_CHOICES = [
        ('En espera', 'En espera'),
        ('En progreso', 'En progreso'),
        ('Atendido', 'Atendido'),
        ('Cancelado', 'Cancelado'),
    ]
    PRIORIDAD_CHOICES = [
        ('N', 'Normal'),
        ('P', 'Prioritario'),
    ]

    numero = models.CharField(max_length=4, unique=False)  # Ej: N001
    usuario = models.ForeignKey('Usuario', on_delete=models.CASCADE)
    punto_atencion = models.ForeignKey('PuntoAtencion', on_delete=models.CASCADE)
    tipo_cita = models.CharField(max_length=50)
    fecha = models.DateField()  # Quitamos el default para setearlo manualmente
    fecha_cita = models.DateTimeField(validators=[validate_turno_time])  # Añadimos el validador
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='En espera')
    prioridad = models.CharField(max_length=1, choices=PRIORIDAD_CHOICES, default='N')
    fecha_atencion = models.DateTimeField(null=True, blank=True)
    descripcion = models.TextField(null=True, blank=True)

    class Meta:
        unique_together = ('punto_atencion', 'numero', 'fecha')  # Unicidad por día y punto

    def save(self, *args, **kwargs):
        # Generar el número del turno
        if not self.numero:
            today = timezone.now().date()
            last_turno = Turno.objects.filter(
                punto_atencion=self.punto_atencion,
                fecha=today
            ).order_by('numero').last()
            if last_turno and last_turno.numero.startswith('N'):
                last_num = int(last_turno.numero[1:])  # Extrae el número después de 'N'
                new_num = last_num + 1
            else:
                new_num = 1
            self.numero = f"N{new_num:03d}"  # Ej: N001
            logger.debug(f"Generado número de turno: {self.numero} para punto_atencion: {self.punto_atencion}, fecha: {today}")

        # Asegurarse de que fecha_cita tenga una zona horaria
        if self.fecha_cita and timezone.is_naive(self.fecha_cita):
            self.fecha_cita = timezone.make_aware(self.fecha_cita)
            logger.debug(f"fecha_cita convertida a aware: {self.fecha_cita}")

        # Setear fecha a partir de fecha_cita
        if not self.fecha:
            fecha_cita_local = timezone.localtime(self.fecha_cita)  # Convertir a la zona horaria local (America/Bogota)
            self.fecha = fecha_cita_local.date()
            logger.debug(f"Seteando fecha: {self.fecha} a partir de fecha_cita: {self.fecha_cita}")

        # Validar manualmente el horario de fecha_cita
        validate_turno_time(self.fecha_cita)

        super().save(*args, **kwargs)
        logger.debug(f"Turno guardado: {self.numero}, fecha: {self.fecha}, fecha_cita: {self.fecha_cita}")

    def __str__(self):
        return f"{self.numero} - {self.punto_atencion.nombre}"