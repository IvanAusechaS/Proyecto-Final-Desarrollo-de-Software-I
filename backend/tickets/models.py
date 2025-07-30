from django.db import models, connection
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.utils.timezone import localtime
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import timedelta
import logging
import random
import string

logger = logging.getLogger(__name__)

class UsuarioManager(BaseUserManager):
    def update_id_sequence(self):
        """
        Update the tickets_usuario_id_seq sequence to the next available ID
        based on the maximum id in the usuario table.
        """
        with connection.cursor() as cursor:
            # Get the maximum id from the usuario table
            cursor.execute("SELECT MAX(id) FROM tickets_usuario")
            max_id = cursor.fetchone()[0] or 0  # Default to 0 if table is empty
            next_id = max_id + 1
            # Update the sequence to the next available id
            cursor.execute("SELECT setval('tickets_usuario_id_seq', %s)", [max_id])
            logger.info(f"Updated tickets_usuario_id_seq to next available id: {next_id}")

    def create_user(self, email, nombre, password=None, cedula=None, es_profesional=False, **extra_fields):
        if not email:
            raise ValueError('El correo electrónico es obligatorio')
        email = self.normalize_email(email)

        # Update the sequence before creating the user
        self.update_id_sequence()

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
    rol = models.CharField(max_length=20, default='usuario')
    punto_atencion = models.ForeignKey('PuntoAtencion', null=True, blank=True, on_delete=models.SET_NULL)

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
    # Validar que la hora esté entre las 8:00 AM (8) y las 10:00 PM (22)
    if not (0 <= hour < 24):
        raise ValidationError('Los turnos solo pueden ser entre 8:00 y 22:00.')

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

    numero = models.CharField(max_length=4, unique=False)  # Ej: N001 o P001
    usuario = models.ForeignKey('Usuario', on_delete=models.CASCADE)
    punto_atencion = models.ForeignKey('PuntoAtencion', on_delete=models.CASCADE)
    tipo_cita = models.CharField(max_length=50)
    fecha = models.DateField(default=timezone.now)  # Solo fecha, sin hora
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='En espera')
    prioridad = models.CharField(max_length=1, choices=PRIORIDAD_CHOICES, default='N')
    fecha_atencion = models.DateTimeField(null=True, blank=True)
    descripcion = models.TextField(null=True, blank=True)

    class Meta:
        unique_together = ('punto_atencion', 'numero', 'fecha')  # Unicidad por día y punto

    def save(self, *args, **kwargs):
        if not self.numero:
            today = localtime(timezone.now()).date()
            last_turno = Turno.objects.filter(
                punto_atencion=self.punto_atencion,
                fecha=today,
                prioridad=self.prioridad
            ).order_by('numero').last()
            if last_turno and last_turno.numero.startswith(self.prioridad):
                last_num = int(last_turno.numero[1:])
                new_num = last_num + 1
            else:
                new_num = 1
            self.numero = f"{self.prioridad}{new_num:03d}"
            logger.debug(f"Generado número de turno: {self.numero} para punto_atencion: {self.punto_atencion}, fecha: {today}, prioridad: {self.prioridad}")

        super().save(*args, **kwargs)
        logger.debug(f"Turno guardado: {self.numero}, fecha: {self.fecha}")

    def __str__(self):
        return f"{self.numero} - {self.punto_atencion.nombre}"
    
class PasswordResetCode(models.Model):
    user = models.ForeignKey('Usuario', on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=15)  # Expira en 15 minutos
        super().save(*args, **kwargs)

    def is_expired(self):
        return timezone.now() > self.expires_at

    @classmethod
    def generate_code(cls):
        return ''.join(random.choices(string.digits, k=6))

    def __str__(self):
        return f"Reset code for {self.user.email}"