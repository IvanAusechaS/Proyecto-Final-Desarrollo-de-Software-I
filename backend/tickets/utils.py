# utils.py
from itertools import zip_longest
from .models import Turno
from django.utils import timezone

def get_intercalated_turnos_by_punto(punto):
    hoy = timezone.now().date()
    mañana = hoy + timezone.timedelta(days=1)

    turnos_prioritarios = Turno.objects.filter(
        punto_atencion=punto,
        prioridad='P',
        estado='En espera',
        fecha_cita__gte=hoy,
        fecha_cita__lt=mañana
    ).order_by('fecha_cita')

    turnos_normales = Turno.objects.filter(
        punto_atencion=punto,
        prioridad='N',
        estado='En espera',
        fecha_cita__gte=hoy,
        fecha_cita__lt=mañana
    ).order_by('fecha_cita')

    intercalados = []
    for p, n in zip_longest(turnos_prioritarios, turnos_normales):
        if p:
            intercalados.append(p)
        if n:
            intercalados.append(n)

    return intercalados
