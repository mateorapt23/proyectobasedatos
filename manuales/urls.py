from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('manual-usuario/', views.manual_usuario, name='manual_usuario'),
    path('manual-instalacion/', views.manual_instalacion, name='manual_instalacion'),
]