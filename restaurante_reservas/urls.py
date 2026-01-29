from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('django-admin/', admin.site.urls),
    path('', include('core.urls')),
    path('clientes/', include('clientes.urls')),
    path('reservas/', include('reservas.urls')),
    path('facturas/', include('facturas.urls')), 
    path('admin/', include('admin_panel.urls')), 
    path('manuales/', include('manuales.urls')), 
]