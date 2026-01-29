from django.shortcuts import render
from django.http import JsonResponse

def manual_usuario(request):
    """Vista para el manual de usuario"""
    return render(request, 'manuales/manual_usuario.html')

def manual_instalacion(request):
    """Vista para el manual de instalación"""
    return render(request, 'manuales/manual_instalacion.html')

def index(request):
    """Vista principal de ejemplo - puedes adaptar esto a tu página principal"""
    return render(request, 'manuales/index.html')