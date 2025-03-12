from django.contrib import admin
from .models import Usuario, PuntoAtencion, Turno

admin.site.register(Usuario)
admin.site.register(PuntoAtencion)
admin.site.register(Turno)