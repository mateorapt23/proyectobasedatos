from mongoengine import Document, EmbeddedDocument, fields
from datetime import datetime

class ClienteFacturaEmbed(EmbeddedDocument):
    idCliente = fields.StringField(required=True)
    nombre = fields.StringField(required=True)
    ci = fields.StringField(required=True)

class ReservaFacturaEmbed(EmbeddedDocument):
    idReserva = fields.StringField(required=True)
    numeroMesa = fields.IntField(required=True)
    fecha = fields.DateTimeField(required=True)
    hora = fields.StringField(required=True)
    numeroPersonas = fields.IntField(required=True)

class Factura(Document):
    """
    Modelo de Factura
    - Se crea automáticamente cuando el usuario hace una reserva (garantía $30)
    - El admin puede actualizar la factura con el consumo real
    """
    cliente = fields.EmbeddedDocumentField(ClienteFacturaEmbed, required=True)
    reserva = fields.EmbeddedDocumentField(ReservaFacturaEmbed, required=True)
    numero = fields.StringField(required=True, unique=True)  # Formato: 001-XXXXXX
    fechaEmision = fields.DateTimeField(default=datetime.now)
    
    # Montos
    esGarantia = fields.BooleanField(default=True)  # True si solo es garantía, False si ya fue procesada
    subtotal = fields.FloatField(default=30.00)  # Por defecto $30 de garantía
    iva = fields.FloatField(default=3.60)  # 12% del subtotal
    total = fields.FloatField(default=33.60)  # Subtotal + IVA
    
    # Estado
    estado = fields.StringField(default="Pendiente")  # Pendiente, Pagada
    
    # Detalles adicionales (para cuando el admin actualiza)
    detallesConsumo = fields.StringField(default="Garantía de Reserva")
    
    meta = {
        'collection': 'facturas',
        'indexes': ['cliente.idCliente', 'numero', 'fechaEmision']
    }
    
    @staticmethod
    def generar_numero():
        """Genera el siguiente número de factura"""
        ultima = Factura.objects.order_by('-numero').first()
        if ultima:
            # Extraer el número y sumar 1
            num = int(ultima.numero.split('-')[1]) + 1
        else:
            num = 1
        return f"001-{str(num).zfill(6)}"