from django.contrib import admin
from .models import Usuario, PuntoAtencion, Ticket, Turno

admin.site.register(Usuario)
admin.site.register(PuntoAtencion)
admin.site.register(Ticket)
admin.site.register(Turno)