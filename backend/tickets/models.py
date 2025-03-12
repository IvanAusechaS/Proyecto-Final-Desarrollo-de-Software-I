from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.utils import timezone

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

    USERNAME_FIELD = 'cedula'  # Campo usado para login
    REQUIRED_FIELDS = ['email', 'nombre']  # Campos adicionales para createsuperuser

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
    servicios = models.JSONField(default=list)

    def __str__(self):
        return self.nombre

class Turno(models.Model):
    ESTADO_CHOICES = [
        ('En espera', 'En espera'),
        ('En progreso', 'En progreso'),
        ('Atendido', 'Atendido'),
        ('Cancelado', 'Cancelado'),
    ]

    TIPO_CITA_CHOICES = [
        ('medica', 'Cita Médica'),
        ('odontologica', 'Cita Odontológica'),
    ]

    PRIORIDAD_CHOICES = [
        ('N', 'Normal'),
        ('P', 'Alta'),
    ]

    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    punto_atencion = models.ForeignKey(PuntoAtencion, on_delete=models.CASCADE)
    numero = models.CharField(max_length=10, unique=True, blank=True)
    tipo_cita = models.CharField(max_length=20, choices=TIPO_CITA_CHOICES)
    prioridad = models.CharField(max_length=1, choices=PRIORIDAD_CHOICES, default='N')
    descripcion = models.TextField()
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='En espera')
    fecha = models.DateTimeField(default=timezone.now)
    fecha_asignacion = models.DateTimeField(auto_now_add=True)
    fecha_atencion = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.numero:
            last_turno = Turno.objects.filter(punto_atencion=self.punto_atencion).order_by('-id').first()
            if last_turno:
                last_num = int(last_turno.numero.split('-')[1])
                self.numero = f"N-{last_num + 1:03d}"
            else:
                self.numero = "N-001"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.numero} - {self.usuario.nombre}"