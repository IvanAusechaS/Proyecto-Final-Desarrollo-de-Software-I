# backend/tickets/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario, PuntoAtencion, Turno

class UsuarioAdmin(UserAdmin):
    # Campos que se muestran en la lista de usuarios
    list_display = ('cedula', 'nombre', 'email', 'es_profesional', 'is_admin', 'is_active')
    list_filter = ('es_profesional', 'is_admin', 'is_active')
    search_fields = ('cedula', 'nombre', 'email')

    # Campos en el formulario de edición
    fieldsets = (
        (None, {'fields': ('cedula', 'password')}),
        ('Información personal', {'fields': ('nombre', 'email')}),
        ('Permisos', {'fields': ('es_profesional', 'is_admin', 'is_staff', 'is_superuser')}),
        ('Estado', {'fields': ('is_active',)}),
        ('Restablecimiento', {'fields': ('reset_password_token',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('cedula', 'nombre', 'email', 'password1', 'password2', 'es_profesional', 'is_admin', 'is_active'),
        }),
    )

    # Configuración específica para el modelo personalizado
    ordering = ('cedula',)
    filter_horizontal = ()

admin.site.register(Usuario, UsuarioAdmin)
admin.site.register(PuntoAtencion)
admin.site.register(Turno)