from django.core.management.base import BaseCommand
from tickets.models import Usuario, PuntoAtencion
from django.utils import timezone

class Command(BaseCommand):
    help = 'Pobla la base de datos con datos de ejemplo'

    def handle(self, *args, **kwargs):
        # Crear Usuarios
        usuarios = [
            {
                'email': 'ivanausecha@gmail.com',
                'nombre': 'Ivan Ausecha',
                'password': 'admin123',
                'cedula': '99999999',
                'es_profesional': False,
                'is_admin': True,
                'is_staff': True,
                'is_superuser': True
            },
            {
                'email': 'juan.perez@example.com',
                'nombre': 'Juan Pérez',
                'password': 'password123',
                'cedula': '12345678',
                'es_profesional': False
            },
            {
                'email': 'maria.lopez@example.com',
                'nombre': 'María López',
                'password': 'password123',
                'cedula': '87654321',
                'es_profesional': True
            }
        ]

        for user_data in usuarios:
            if not Usuario.objects.filter(email=user_data['email']).exists():
                extra_fields = {
                    'is_admin': user_data.get('is_admin', False),
                    'is_staff': user_data.get('is_staff', False),
                    'is_superuser': user_data.get('is_superuser', False)
                }
                user = Usuario.objects.create_user(
                    email=user_data['email'],
                    nombre=user_data['nombre'],
                    password=user_data['password'],
                    cedula=user_data['cedula'],
                    es_profesional=user_data.get('es_profesional', False),
                    **extra_fields
                )
                self.stdout.write(self.style.SUCCESS(f'Usuario {user.email} creado'))

        # Crear Puntos de Atención
        profesional_maria = Usuario.objects.get(email='maria.lopez@example.com')
        puntos_atencion = [
            {
                'nombre': 'Meléndez',
                'ubicacion': 'Calle 123, Meléndez',
                'activo': True,
                'servicios_texto': 'Consulta General\nExámenes Básicos',
                'profesional': profesional_maria
            },
            {
                'nombre': 'Polvorines',
                'ubicacion': 'Avenida 456, Polvorines',
                'activo': True,
                'servicios_texto': 'Consulta Especializada\nRadiografías',
                'profesional': None
            }
        ]

        for punto_data in puntos_atencion:
            if not PuntoAtencion.objects.filter(nombre=punto_data['nombre']).exists():
                PuntoAtencion.objects.create(
                    nombre=punto_data['nombre'],
                    ubicacion=punto_data['ubicacion'],
                    activo=punto_data['activo'],
                    servicios_texto=punto_data['servicios_texto'],
                    profesional=punto_data['profesional']
                )
                self.stdout.write(self.style.SUCCESS(f'Punto de Atención {punto_data["nombre"]} creado'))

        self.stdout.write(self.style.SUCCESS('Base de datos poblada exitosamente'))