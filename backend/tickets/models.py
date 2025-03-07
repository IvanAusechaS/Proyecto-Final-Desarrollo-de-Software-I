from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

class CustomUserManager(BaseUserManager):
    def create_user(self, cedula, email, nombre, password=None, **extra_fields):
        if not cedula or not email:
            raise ValueError('La cédula y el email son obligatorios')
        email = self.normalize_email(email)
        user = self.model(cedula=cedula, email=email, nombre=nombre, **extra_fields)
        user.set_password(password)  # Esto asegura que la contraseña se hashee
        user.save(using=self._db)
        return user

    def create_superuser(self, cedula, email, nombre, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        if extra_fields.get('is_staff') is not True or extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser debe tener is_staff=True y is_superuser=True')
        return self.create_user(cedula, email, nombre, password, **extra_fields)

class Usuario(AbstractBaseUser, PermissionsMixin):
    cedula = models.CharField(max_length=20, unique=True)
    email = models.EmailField(unique=True)
    nombre = models.CharField(max_length=100)
    telefono = models.CharField(max_length=15, blank=True)
    creado = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = 'cedula'
    REQUIRED_FIELDS = ['email', 'nombre']

    def __str__(self):
        return self.nombre

class PuntoAtencion(models.Model):
    nombre = models.CharField(max_length=100)
    ubicacion = models.CharField(max_length=200)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

class Ticket(models.Model):
    PRIORIDAD_ALTA = 'P'
    PRIORIDAD_NORMAL = 'N'
    PRIORIDAD_CHOICES = [
        (PRIORIDAD_ALTA, 'Alta'),
        (PRIORIDAD_NORMAL, 'Normal'),
    ]
    TIPO_CITA_CHOICES = [
        ('medica', 'Cita Médica'),
        ('odontologica', 'Cita Odontológica'),
    ]

    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    punto_atencion = models.ForeignKey(PuntoAtencion, on_delete=models.CASCADE)
    numero = models.CharField(max_length=10, unique=True, blank=True)
    tipo_cita = models.CharField(max_length=20, choices=TIPO_CITA_CHOICES)
    prioridad = models.CharField(max_length=1, choices=PRIORIDAD_CHOICES, default=PRIORIDAD_NORMAL)
    descripcion = models.TextField()
    estado = models.CharField(max_length=20, default="Pendiente")
    fecha = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.numero:
            prefix = self.prioridad
            last_ticket = Ticket.objects.filter(prioridad=self.prioridad).order_by('-id').first()
            number = (int(last_ticket.numero.split('-')[1]) + 1) if last_ticket and last_ticket.numero else 1
            self.numero = f"{prefix}-{number:03d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.numero

class Turno(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE)
    punto_atencion = models.ForeignKey(PuntoAtencion, on_delete=models.CASCADE)
    estado = models.CharField(max_length=20, default="En espera")
    fecha_asignacion = models.DateTimeField(auto_now_add=True)
    fecha_atencion = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Turno {self.ticket.numero} - {self.punto_atencion.nombre}"