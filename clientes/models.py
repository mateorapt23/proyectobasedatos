from mongoengine import Document, StringField, DateTimeField, BooleanField
from datetime import datetime

class Cliente(Document):
    nombre = StringField(required=True)
    ci = StringField(required=True, unique=True)
    telefono = StringField(required=True)
    email = StringField(required=True, unique=True)
    password = StringField(required=True)
    fecha_registro = DateTimeField(default=datetime.now)


class Actividad(Document):
    """
    Modelo para registrar las actividades del usuario
    """
    cliente_id = StringField(required=True)
    tipo = StringField(required=True)  # "reserva_confirmada", "factura_disponible"
    titulo = StringField(required=True)
    descripcion = StringField()
    icono = StringField(default="fa-info-circle")
    color = StringField(default="primary")
    fecha = DateTimeField(default=datetime.now)
    leida = BooleanField(default=False)
    
    # Referencias opcionales
    reserva_id = StringField()
    factura_id = StringField()
    
    meta = {
        'collection': 'actividades',
        'indexes': ['cliente_id', '-fecha'],
        'ordering': ['-fecha']
    }
    
    @staticmethod
    def crear_actividad_reserva(cliente_id, reserva_id, mesa_numero):
        """Crea una actividad cuando se confirma una reserva"""
        actividad = Actividad(
            cliente_id=cliente_id,
            tipo="reserva_confirmada",
            titulo="Reserva confirmada",
            descripcion=f"Mesa {mesa_numero} reservada exitosamente",
            icono="fa-calendar-check",
            color="success",
            reserva_id=reserva_id
        )
        actividad.save()
        return actividad
    
    @staticmethod
    def crear_actividad_factura(cliente_id, factura_id, numero_factura):
        """Crea una actividad cuando hay una nueva factura disponible"""
        actividad = Actividad(
            cliente_id=cliente_id,
            tipo="factura_disponible",
            titulo="Nueva factura disponible",
            descripcion=f"Factura {numero_factura}",
            icono="fa-file",
            color="info",
            factura_id=factura_id
        )
        actividad.save()
        return actividad
    
    def tiempo_transcurrido(self):
        """Retorna el tiempo transcurrido desde la actividad"""
        ahora = datetime.now()
        diferencia = ahora - self.fecha
        
        segundos = diferencia.total_seconds()
        minutos = segundos / 60
        horas = minutos / 60
        dias = diferencia.days
        
        if segundos < 60:
            return "Hace unos segundos"
        elif minutos < 60:
            mins = int(minutos)
            return f"Hace {mins} min" if mins == 1 else f"Hace {mins} mins"
        elif horas < 24:
            hrs = int(horas)
            return f"Hace {hrs} hora" if hrs == 1 else f"Hace {hrs} horas"
        elif dias < 7:
            return f"Hace {dias} día" if dias == 1 else f"Hace {dias} días"
        elif dias < 30:
            semanas = dias // 7
            return f"Hace {semanas} semana" if semanas == 1 else f"Hace {semanas} semanas"
        elif dias < 365:
            meses = dias // 30
            return f"Hace {meses} mes" if meses == 1 else f"Hace {meses} meses"
        else:
            años = dias // 365
            return f"Hace {años} año" if años == 1 else f"Hace {años} años"