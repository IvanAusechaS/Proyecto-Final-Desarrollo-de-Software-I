from django.db import models

class Usuario(models.Model):
    cedula = models.CharField(max_length=20, unique=True, blank=True, null=True, default="000000")  # Opcional con valor por defecto
    nombre = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    telefono = models.CharField(max_length=15, blank=True)
    creado = models.DateTimeField(auto_now_add=True)

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
    tipo_cita = models.CharField(max_length=20, choices=TIPO_CITA_CHOICES, default='medica')  # Valor por defecto
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