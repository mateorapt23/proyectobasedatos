from django.urls import path
from .views import mis_facturas, descargar_factura, imprimir_factura

urlpatterns = [
    path('mis-facturas/', mis_facturas, name='mis_facturas'),
    path('descargar/<str:factura_id>/', descargar_factura, name='descargar_factura'),
    path('imprimir/<str:factura_id>/', imprimir_factura, name='imprimir_factura'),
]