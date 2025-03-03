from django.http import HttpResponse

def home(request):
    return HttpResponse("Bienvenido al Sistema de Manejo de Atención a Usuarios")