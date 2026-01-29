from django.urls import path
from .views import registro, login_cliente, panel_cliente, logout_cliente, perfil_cliente

urlpatterns = [
    path('registro/', registro, name='registro'),
    path('login/', login_cliente, name='login'),
    path('panel/', panel_cliente, name='panel_cliente'),
    path('logout/', logout_cliente, name='logout'),
    path('perfil/', perfil_cliente, name='perfil_cliente'),
]