from django.urls import path
from .views import (
    login_admin, logout_admin, panel_admin,
    clientes_admin, detalle_cliente_admin, editar_cliente_admin, eliminar_cliente_admin,
    mesas_admin, liberar_mesa,
    facturas_admin, actualizar_factura,
    informes_admin, reporte_clientes_pdf, reporte_reservas_pdf, reporte_mesas_pdf
)

urlpatterns = [
    # Ruta raíz - redirige al login o panel según autenticación
    path('', login_admin, name='admin_home'),
    
    # Autenticación
    path('login/', login_admin, name='login_admin'),
    path('logout/', logout_admin, name='logout_admin'),
    
    # Panel principal
    path('panel/', panel_admin, name='panel_admin'),
    
    # Clientes
    path('clientes/', clientes_admin, name='clientes_admin'),
    path('clientes/<str:cliente_id>/', detalle_cliente_admin, name='detalle_cliente_admin'),
    path('clientes/editar/<str:cliente_id>/', editar_cliente_admin, name='editar_cliente_admin'),
    path('clientes/eliminar/<str:cliente_id>/', eliminar_cliente_admin, name='eliminar_cliente_admin'),
    
    # Mesas
    path('mesas/', mesas_admin, name='mesas_admin'),
    path('mesas/liberar/<str:reserva_id>/', liberar_mesa, name='liberar_mesa'),
    
    # Facturas
    path('facturas/', facturas_admin, name='facturas_admin'),
    path('facturas/actualizar/<str:factura_id>/', actualizar_factura, name='actualizar_factura'),
    
    # Informes
    path('informes/', informes_admin, name='informes_admin'),
    path('informes/clientes/pdf/', reporte_clientes_pdf, name='reporte_clientes_pdf'),
    path('informes/reservas/pdf/', reporte_reservas_pdf, name='reporte_reservas_pdf'),
    path('informes/mesas/pdf/', reporte_mesas_pdf, name='reporte_mesas_pdf'),
]