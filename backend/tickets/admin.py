from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario, PuntoAtencion, Turno

class UsuarioAdmin(UserAdmin):
    # Campos que se muestran en la lista de usuarios
    list_display = ('email', 'nombre', 'cedula', 'es_profesional', 'is_admin', 'is_active')
    list_filter = ('es_profesional', 'is_admin', 'is_active')
    search_fields = ('email', 'nombre', 'cedula')

    # Campos en el formulario de edición
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Información personal', {'fields': ('nombre', 'cedula')}),
        ('Permisos', {'fields': ('es_profesional', 'is_admin', 'is_staff', 'is_superuser')}),
        ('Estado', {'fields': ('is_active',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'nombre', 'cedula', 'password1', 'password2', 'es_profesional', 'is_admin', 'is_staff', 'is_superuser', 'is_active'),
        }),
    )

    # Configuración específica para el modelo personalizado
    ordering = ('email',)
    filter_horizontal = ()

admin.site.register(Usuario, UsuarioAdmin)
admin.site.register(PuntoAtencion)
admin.site.register(Turno)