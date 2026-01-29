from django.shortcuts import render, redirect
from django.contrib import messages
from datetime import datetime, timedelta
from .models import Reserva, MesaEmbed, ClienteEmbed
from clientes.models import Cliente, Actividad  # ✅ Importar Actividad desde clientes.models
from facturas.models import Factura, ClienteFacturaEmbed, ReservaFacturaEmbed
from mongoengine import connect
from mongoengine.document import Document
from mongoengine.fields import IntField, StringField

# Modelo Mesa
class Mesa(Document):
    numeroMesa = IntField(required=True, unique=True)
    capacidad = IntField(required=True)
    estado = StringField(default="Disponible")

def reservar_mesa(request):
    if 'cliente_id' not in request.session:
        messages.error(request, 'Debes iniciar sesión para hacer una reserva.')
        return redirect('login')

    try:
        # Obtener todas las mesas disponibles
        mesas = Mesa.objects.all()
        
        # Si no hay mesas, crear algunas de ejemplo
        if mesas.count() == 0:
            mesas_default = [
                Mesa(numeroMesa=1, capacidad=2),
                Mesa(numeroMesa=2, capacidad=4),
                Mesa(numeroMesa=3, capacidad=4),
                Mesa(numeroMesa=4, capacidad=6),
                Mesa(numeroMesa=5, capacidad=4),
                Mesa(numeroMesa=6, capacidad=4),
                Mesa(numeroMesa=7, capacidad=2),
                Mesa(numeroMesa=8, capacidad=8),
                Mesa(numeroMesa=9, capacidad=4),
                Mesa(numeroMesa=10, capacidad=2),
                Mesa(numeroMesa=11, capacidad=4),
                Mesa(numeroMesa=12, capacidad=6),
            ]
            for mesa in mesas_default:
                mesa.save()
            mesas = Mesa.objects.all()

        # Procesar filtros
        fecha_filtro = request.GET.get('fecha_filtro')
        hora_filtro = request.GET.get('hora_filtro')
        
        mesas_reservadas = []
        if fecha_filtro and hora_filtro:
            # Convertir fecha a objeto date
            fecha_obj = datetime.strptime(fecha_filtro, "%Y-%m-%d").date()
            
            # Buscar reservas en esa fecha y hora
            reservas_filtradas = Reserva.objects(
                fecha=fecha_obj,
                hora=hora_filtro,
                estado="Reservada"
            )
            
            # Obtener números de mesas reservadas
            mesas_reservadas = [r.mesa.numeroMesa for r in reservas_filtradas]

        if request.method == 'POST':
            mesa_id = request.POST.get('mesa_id')
            fecha_str = request.POST.get('fecha')
            hora = request.POST.get('hora')
            personas = int(request.POST.get('personas', 0))

            # Validaciones
            if not all([mesa_id, fecha_str, hora, personas]):
                messages.error(request, 'Por favor completa todos los campos.')
                return render(request, 'reservar_mesa.html', {
                    'mesas': mesas,
                    'mesas_reservadas': mesas_reservadas
                })

            # Validar fecha (no puede ser en el pasado)
            fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
            if fecha < datetime.now().date():
                messages.error(request, 'No puedes hacer reservas en fechas pasadas.')
                return render(request, 'reservar_mesa.html', {
                    'mesas': mesas,
                    'mesas_reservadas': mesas_reservadas
                })

            # Validar número de personas
            if personas < 1 or personas > 8:
                messages.error(request, 'El número de personas debe estar entre 1 y 8.')
                return render(request, 'reservar_mesa.html', {
                    'mesas': mesas,
                    'mesas_reservadas': mesas_reservadas
                })

            try:
                mesa = Mesa.objects.get(id=mesa_id)
                cliente = Cliente.objects.get(id=request.session['cliente_id'])

                # Verificar si la mesa ya está reservada en ese horario
                existe = Reserva.objects(
                    mesa__numeroMesa=mesa.numeroMesa,
                    fecha=fecha,
                    hora=hora,
                    estado="Reservada"
                ).first()

                if existe:
                    messages.error(request, 'Lo sentimos, esta mesa ya está reservada en ese horario. Por favor selecciona otra mesa u horario.')
                    return render(request, 'reservar_mesa.html', {
                        'mesas': mesas,
                        'mesas_reservadas': mesas_reservadas
                    })

                # Verificar que el número de personas no exceda la capacidad
                if personas > mesa.capacidad:
                    messages.error(request, f'Esta mesa tiene capacidad para {mesa.capacidad} personas. Por favor selecciona una mesa con mayor capacidad.')
                    return render(request, 'reservar_mesa.html', {
                        'mesas': mesas,
                        'mesas_reservadas': mesas_reservadas
                    })

                # Crear la reserva
                reserva = Reserva(
                    cliente=ClienteEmbed(
                        idCliente=str(cliente.id),
                        nombre=cliente.nombre,
                        ci=cliente.ci
                    ),
                    fecha=fecha,
                    hora=hora,
                    numeroPersonas=personas,
                    mesa=MesaEmbed(
                        numeroMesa=mesa.numeroMesa,
                        capacidad=mesa.capacidad
                    ),
                    estado="Reservada"
                )
                reserva.save()
                
                # Crear la factura de garantía ($30)
                numero_factura = Factura.generar_numero()
                factura = Factura(
                    cliente=ClienteFacturaEmbed(
                        idCliente=str(cliente.id),
                        nombre=cliente.nombre,
                        ci=cliente.ci
                    ),
                    reserva=ReservaFacturaEmbed(
                        idReserva=str(reserva.id),
                        numeroMesa=mesa.numeroMesa,
                        fecha=fecha,
                        hora=hora,
                        numeroPersonas=personas
                    ),
                    numero=numero_factura,
                    esGarantia=True,
                    subtotal=30.00,
                    iva=3.60,
                    total=33.60,
                    estado="Pendiente",
                    detallesConsumo="Garantía de Reserva"
                )
                factura.save()
                
                # Crear actividad de reserva confirmada
                Actividad.crear_actividad_reserva(
                    cliente_id=str(cliente.id),
                    reserva_id=str(reserva.id),
                    mesa_numero=mesa.numeroMesa
                )
                
                # Crear actividad de factura disponible
                Actividad.crear_actividad_factura(
                    cliente_id=str(cliente.id),
                    factura_id=str(factura.id),
                    numero_factura=numero_factura
                )

                messages.success(request, f'¡Reserva confirmada! Mesa {mesa.numeroMesa} para {personas} personas el {fecha.strftime("%d/%m/%Y")} a las {hora}. Se ha generado una factura de garantía de $30.00.')
                return redirect('panel_cliente')

            except Mesa.DoesNotExist:
                messages.error(request, 'La mesa seleccionada no existe.')
                return render(request, 'reservar_mesa.html', {
                    'mesas': mesas,
                    'mesas_reservadas': mesas_reservadas
                })
            except Exception as e:
                messages.error(request, f'Error al crear la reserva: {str(e)}')
                return render(request, 'reservar_mesa.html', {
                    'mesas': mesas,
                    'mesas_reservadas': mesas_reservadas
                })

        # Fecha mínima para el input date
        fecha_minima = datetime.now().date().isoformat()
        
        return render(request, 'reservar_mesa.html', {
            'mesas': mesas,
            'fecha_minima': fecha_minima,
            'mesas_reservadas': mesas_reservadas,
            'fecha_filtro': fecha_filtro,
            'hora_filtro': hora_filtro,
        })
        
    except Exception as e:
        messages.error(request, f'Error al cargar las mesas: {str(e)}')
        return redirect('panel_cliente')

def mis_reservas(request):
    if 'cliente_id' not in request.session:
        messages.error(request, 'Debes iniciar sesión para ver tus reservas.')
        return redirect('login')

    try:
        cliente_id = request.session['cliente_id']
        
        # Obtener todas las reservas del cliente
        todas_reservas = list(Reserva.objects(
            cliente__idCliente=cliente_id
        ).order_by('-fecha', '-hora'))
        
        hoy = datetime.now().date()
        
        # Clasificar reservas y añadir tipo
        for reserva in todas_reservas:
            if reserva.fecha >= hoy and reserva.estado == "Reservada":
                reserva.tipo = "proximas"
            else:
                reserva.tipo = "pasadas"
        
        # Contar por categorías
        proximas_count = len([r for r in todas_reservas if r.tipo == "proximas"])
        completadas_count = Reserva.objects(
            cliente__idCliente=cliente_id,
            estado="Completada"
        ).count()
        
        context = {
            'nombre': request.session['cliente_nombre'],
            'reservas': todas_reservas,
            'proximas_count': proximas_count,
            'completadas_count': completadas_count,
        }
        
        return render(request, 'mis_reservas.html', context)
        
    except Exception as e:
        messages.error(request, f'Error al cargar las reservas: {str(e)}')
        return redirect('panel_cliente')

def cancelar_reserva(request):
    """Esta función ya no se usará porque no se permite cancelar"""
    return redirect('mis_reservas')

def detalle_reserva(request, reserva_id):
    if 'cliente_id' not in request.session:
        return redirect('login')
    
    try:
        reserva = Reserva.objects.get(id=reserva_id)
        
        # Verificar que la reserva pertenece al cliente
        if reserva.cliente.idCliente != request.session['cliente_id']:
            messages.error(request, 'No tienes permiso para ver esta reserva.')
            return redirect('mis_reservas')
        
        return render(request, 'detalle_reserva.html', {
            'reserva': reserva,
            'nombre': request.session['cliente_nombre']
        })
        
    except Reserva.DoesNotExist:
        messages.error(request, 'La reserva no existe.')
        return redirect('mis_reservas')
    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
        return redirect('mis_reservas')