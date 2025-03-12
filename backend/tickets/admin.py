from django.contrib import admin
from .models import Usuario, PuntoAtencion, Turno
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

class UsuarioAdmin(BaseUserAdmin):
    list_display = ('cedula', 'nombre', 'email', 'es_profesional', 'is_active', 'is_admin')
    list_filter = ('es_profesional', 'is_active', 'is_admin')
    fieldsets = (
        (None, {'fields': ('cedula', 'password')}),
        ('Información Personal', {'fields': ('nombre', 'email', 'telefono')}),
        ('Permisos', {'fields': ('es_profesional', 'is_active', 'is_admin')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('cedula', 'email', 'nombre', 'telefono', 'password1', 'password2', 'es_profesional', 'is_active', 'is_admin'),
        }),
    )
    search_fields = ('cedula', 'nombre', 'email')
    ordering = ('cedula',)
    filter_horizontal = ()

admin.site.register(Usuario, UsuarioAdmin)
admin.site.register(PuntoAtencion)
admin.site.register(Turno)