from django.urls import path
from .views import reservar_mesa, mis_reservas, cancelar_reserva, detalle_reserva

urlpatterns = [
    path('reservar/', reservar_mesa, name='reservar_mesa'),
    path('mis-reservas/', mis_reservas, name='mis_reservas'),
    path('cancelar/', cancelar_reserva, name='cancelar_reserva'),
    path('detalle/<str:reserva_id>/', detalle_reserva, name='detalle_reserva'),
]