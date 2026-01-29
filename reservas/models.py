from mongoengine import Document, EmbeddedDocument, EmbeddedDocumentField
from mongoengine import StringField, IntField, DateField

class Mesa(Document):
    numeroMesa = IntField(required=True, unique=True)
    capacidad = IntField(required=True)
    estado = StringField(default="Disponible")

class ClienteEmbed(EmbeddedDocument):
    idCliente = StringField()
    nombre = StringField()
    ci = StringField()

class MesaEmbed(EmbeddedDocument):
    numeroMesa = IntField()
    capacidad = IntField()

class Reserva(Document):
    cliente = EmbeddedDocumentField(ClienteEmbed)
    fecha = DateField(required=True)
    hora = StringField(required=True)
    numeroPersonas = IntField(required=True)
    mesa = EmbeddedDocumentField(MesaEmbed)
    estado = StringField(default="Reservada")
