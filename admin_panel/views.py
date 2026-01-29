from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse
from django.contrib.auth.models import User
from clientes.models import Cliente, Actividad
from reservas.models import Reserva
from facturas.models import Factura
from datetime import datetime, timedelta
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import io

# Modelo Mesa (importado desde reservas)
from mongoengine.document import Document
from mongoengine.fields import IntField, StringField

class Mesa(Document):
    numeroMesa = IntField(required=True, unique=True)
    capacidad = IntField(required=True)
    estado = StringField(default="Disponible")


# ==================== AUTENTICACIÓN ====================

def login_admin(request):
    """Login para administradores usando superuser de Django"""
    # CASO 1: Usuario autenticado y ES superuser → ir al panel
    if request.user.is_authenticated and request.user.is_superuser:
        return redirect('panel_admin')
    
    # CASO 2: Usuario autenticado pero NO es superuser → cerrar sesión y mostrar error
    if request.user.is_authenticated and not request.user.is_superuser:
        logout(request)
        messages.error(request, 'No tienes permisos de administrador. Tu sesión ha sido cerrada.')
        return render(request, 'admin_panel/login_admin.html')
    
    # CASO 3: No autenticado y hace POST (intento de login)
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None and user.is_superuser:
            login(request, user)
            messages.success(request, f'¡Bienvenido, {user.username}!')
            return redirect('panel_admin')
        else:
            messages.error(request, 'Credenciales inválidas o no tienes permisos de administrador.')
    
    # CASO 4: No autenticado y hace GET → mostrar formulario
    return render(request, 'admin_panel/login_admin.html')


def logout_admin(request):
    """Cerrar sesión del administrador"""
    logout(request)
    messages.success(request, 'Has cerrado sesión exitosamente.')
    return redirect('login_admin')


# ==================== PANEL PRINCIPAL ====================

def panel_admin(request):
    """Panel principal del administrador con estadísticas"""
    if not request.user.is_authenticated or not request.user.is_superuser:
        messages.error(request, 'Debes iniciar sesión como administrador.')
        return redirect('login_admin')
    
    try:
        # Estadísticas generales
        total_clientes = Cliente.objects.count()
        total_reservas = Reserva.objects.count()
        total_mesas = Mesa.objects.count()
        total_facturas = Factura.objects.count()
        
        # Reservas de hoy
        hoy = datetime.now().date()
        reservas_hoy = Reserva.objects(
            fecha=hoy,
            estado="Reservada"
        ).count()
        
        # Facturas pendientes (garantías)
        facturas_pendientes = Factura.objects(
            estado="Pendiente",
            esGarantia=True
        ).count()
        
        # Últimas reservas (5)
        ultimas_reservas = list(Reserva.objects.order_by('-fecha', '-hora')[:5])
        
        # Clientes recientes (5)
        clientes_recientes = list(Cliente.objects.order_by('-fecha_registro')[:5])
        
        context = {
            'username': request.user.username,
            'total_clientes': total_clientes,
            'total_reservas': total_reservas,
            'total_mesas': total_mesas,
            'total_facturas': total_facturas,
            'reservas_hoy': reservas_hoy,
            'facturas_pendientes': facturas_pendientes,
            'ultimas_reservas': ultimas_reservas,
            'clientes_recientes': clientes_recientes,
        }
        
        return render(request, 'admin_panel/panel_admin.html', context)
        
    except Exception as e:
        messages.error(request, f'Error al cargar el panel: {str(e)}')
        return redirect('login_admin')


# ==================== GESTIÓN DE CLIENTES ====================

def clientes_admin(request):
    """Listado de todos los clientes"""
    if not request.user.is_authenticated or not request.user.is_superuser:
        return redirect('login_admin')
    
    try:
        # Obtener todos los clientes
        clientes = list(Cliente.objects.order_by('-fecha_registro'))
        
        # Agregar estadísticas a cada cliente
        for cliente in clientes:
            cliente.total_reservas = Reserva.objects(
                cliente__idCliente=str(cliente.id)
            ).count()
            cliente.total_facturas = Factura.objects(
                cliente__idCliente=str(cliente.id)
            ).count()
        
        context = {
            'username': request.user.username,
            'clientes': clientes,
        }
        
        return render(request, 'admin_panel/clientes_admin.html', context)
        
    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
        return redirect('panel_admin')


def detalle_cliente_admin(request, cliente_id):
    """Ver detalles de un cliente específico"""
    if not request.user.is_authenticated or not request.user.is_superuser:
        return redirect('login_admin')
    
    try:
        cliente = Cliente.objects.get(id=cliente_id)
        
        # Reservas del cliente
        reservas = list(Reserva.objects(
            cliente__idCliente=str(cliente.id)
        ).order_by('-fecha', '-hora'))
        
        # Facturas del cliente
        facturas = list(Factura.objects(
            cliente__idCliente=str(cliente.id)
        ).order_by('-fechaEmision'))
        
        context = {
            'username': request.user.username,
            'cliente': cliente,
            'reservas': reservas,
            'facturas': facturas,
        }
        
        return render(request, 'admin_panel/detalle_cliente.html', context)
        
    except Cliente.DoesNotExist:
        messages.error(request, 'Cliente no encontrado.')
        return redirect('clientes_admin')
    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
        return redirect('clientes_admin')


# ==================== GESTIÓN DE MESAS ====================

def mesas_admin(request):
    """Gestión de mesas con filtro por fecha/hora"""
    if not request.user.is_authenticated or not request.user.is_superuser:
        return redirect('login_admin')
    
    try:
        # Obtener todas las mesas
        mesas = list(Mesa.objects.order_by('numeroMesa'))
        
        # Procesar filtros
        fecha_filtro = request.GET.get('fecha')
        hora_filtro = request.GET.get('hora')
        
        reservas_por_mesa = {}
        
        if fecha_filtro and hora_filtro:
            # Convertir fecha
            fecha_obj = datetime.strptime(fecha_filtro, "%Y-%m-%d").date()
            
            # Buscar reservas
            reservas_filtradas = Reserva.objects(
                fecha=fecha_obj,
                hora=hora_filtro,
                estado="Reservada"
            )
            
            # Crear diccionario de reservas por mesa
            for reserva in reservas_filtradas:
                reservas_por_mesa[reserva.mesa.numeroMesa] = reserva
        
        # Agregar información de estado a cada mesa
        for mesa in mesas:
            if mesa.numeroMesa in reservas_por_mesa:
                mesa.reserva_actual = reservas_por_mesa[mesa.numeroMesa]
                mesa.estado_filtrado = "Ocupada"
            else:
                mesa.reserva_actual = None
                mesa.estado_filtrado = "Disponible"
        
        context = {
            'username': request.user.username,
            'mesas': mesas,
            'fecha_filtro': fecha_filtro,
            'hora_filtro': hora_filtro,
        }
        
        return render(request, 'admin_panel/mesas_admin.html', context)
        
    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
        return redirect('panel_admin')


def liberar_mesa(request, reserva_id):
    """Liberar una mesa (marcar reserva como completada)"""
    if not request.user.is_authenticated or not request.user.is_superuser:
        return redirect('login_admin')
    
    if request.method == 'POST':
        try:
            reserva = Reserva.objects.get(id=reserva_id)
            reserva.estado = "Completada"
            reserva.save()
            
            messages.success(request, f'Mesa {reserva.mesa.numeroMesa} liberada exitosamente.')
            return redirect('mesas_admin')
            
        except Reserva.DoesNotExist:
            messages.error(request, 'Reserva no encontrada.')
            return redirect('mesas_admin')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
            return redirect('mesas_admin')
    
    return redirect('mesas_admin')


# ==================== GESTIÓN DE FACTURAS ====================

def facturas_admin(request):
    """Gestión de facturas con filtros"""
    if not request.user.is_authenticated or not request.user.is_superuser:
        return redirect('login_admin')
    
    try:
        # Procesar filtro
        filtro = request.GET.get('filtro', 'todas')
        
        if filtro == 'pendientes':
            facturas = list(Factura.objects(estado="Pendiente").order_by('-fechaEmision'))
        elif filtro == 'pagadas':
            facturas = list(Factura.objects(estado="Pagada").order_by('-fechaEmision'))
        else:
            facturas = list(Factura.objects.order_by('-fechaEmision'))
        
        context = {
            'username': request.user.username,
            'facturas': facturas,
            'filtro': filtro,
        }
        
        return render(request, 'admin_panel/facturas_admin.html', context)
        
    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
        return redirect('panel_admin')


def actualizar_factura(request, factura_id):
    """Actualizar factura de garantía con consumo real"""
    if not request.user.is_authenticated or not request.user.is_superuser:
        return redirect('login_admin')
    
    if request.method == 'POST':
        try:
            factura = Factura.objects.get(id=factura_id)
            
            # Validar que sea una factura de garantía pendiente
            if not factura.esGarantia or factura.estado != "Pendiente":
                messages.error(request, 'Esta factura no puede ser actualizada.')
                return redirect('facturas_admin')
            
            # Obtener datos del formulario
            detalles_consumo = request.POST.get('detalles_consumo', '').strip()
            subtotal_consumo = float(request.POST.get('subtotal_consumo', 0))
            
            # Validar
            if not detalles_consumo or subtotal_consumo <= 0:
                messages.error(request, 'Debes completar todos los campos correctamente.')
                return redirect('facturas_admin')
            
            # Calcular total final
            garantia = 30.00
            subtotal_final = max(0, subtotal_consumo - garantia)
            iva = subtotal_final * 0.12
            total_final = subtotal_final + iva
            
            # Actualizar factura
            factura.detalles = detalles_consumo
            factura.subtotal = subtotal_final
            factura.iva = iva
            factura.total = total_final
            factura.estado = "Pagada"
            factura.save()
            
            messages.success(request, f'Factura {factura.numero} actualizada exitosamente.')
            return redirect('facturas_admin')
            
        except Factura.DoesNotExist:
            messages.error(request, 'Factura no encontrada.')
            return redirect('facturas_admin')
        except ValueError:
            messages.error(request, 'Valores numéricos inválidos.')
            return redirect('facturas_admin')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
            return redirect('facturas_admin')
    
    return redirect('facturas_admin')


# ==================== INFORMES ====================

def informes_admin(request):
    """Página de informes y reportes"""
    if not request.user.is_authenticated or not request.user.is_superuser:
        return redirect('login_admin')
    
    context = {
        'username': request.user.username,
    }
    
    return render(request, 'admin_panel/informes_admin.html', context)


def reporte_clientes_pdf(request):
    """Generar PDF con listado de clientes"""
    if not request.user.is_authenticated or not request.user.is_superuser:
        return redirect('login_admin')
    
    try:
        # Obtener clientes
        clientes = list(Cliente.objects.order_by('-fecha_registro'))
        
        # Crear PDF
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()
        
        # Título
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        title = Paragraph("<b>REPORTE DE CLIENTES REGISTRADOS</b>", title_style)
        elements.append(title)
        
        # Info
        info_p = Paragraph(f"<b>Fecha de generación:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal'])
        elements.append(info_p)
        elements.append(Spacer(1, 0.2*inch))
        
        # Total
        total_p = Paragraph(f"<b>Total de clientes:</b> {len(clientes)}", styles['Normal'])
        elements.append(total_p)
        elements.append(Spacer(1, 0.3*inch))
        
        # Tabla
        data = [['#', 'Nombre', 'Cédula', 'Email', 'Teléfono', 'F. Registro']]
        
        for idx, cliente in enumerate(clientes, 1):
            data.append([
                str(idx),
                cliente.nombre[:25],
                cliente.ci,
                cliente.email[:25],
                cliente.telefono,
                cliente.fecha_registro.strftime("%d/%m/%Y")
            ])
        
        table = Table(data, colWidths=[0.5*inch, 2*inch, 1*inch, 2*inch, 1*inch, 1*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
        ]))
        
        elements.append(table)
        
        # Construir PDF
        doc.build(elements)
        
        # Respuesta
        buffer.seek(0)
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="reporte_clientes_{datetime.now().strftime("%Y%m%d")}.pdf"'
        
        return response
        
    except Exception as e:
        messages.error(request, f'Error al generar reporte: {str(e)}')
        return redirect('informes_admin')


def reporte_reservas_pdf(request):
    """Generar PDF con reporte de reservas"""
    if not request.user.is_authenticated or not request.user.is_superuser:
        return redirect('login_admin')
    
    try:
        # Obtener filtros
        fecha_desde = request.GET.get('fecha_desde')
        fecha_hasta = request.GET.get('fecha_hasta')
        
        # Query base
        query = {}
        
        if fecha_desde and fecha_hasta:
            fecha_desde_obj = datetime.strptime(fecha_desde, "%Y-%m-%d").date()
            fecha_hasta_obj = datetime.strptime(fecha_hasta, "%Y-%m-%d").date()
            reservas = list(Reserva.objects(
                fecha__gte=fecha_desde_obj,
                fecha__lte=fecha_hasta_obj
            ).order_by('-fecha'))
            titulo_rango = f"Del {fecha_desde_obj.strftime('%d/%m/%Y')} al {fecha_hasta_obj.strftime('%d/%m/%Y')}"
        else:
            reservas = list(Reserva.objects.order_by('-fecha')[:50])
            titulo_rango = "Últimas 50 reservas"
        
        # Crear PDF
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()
        
        # Título
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        title = Paragraph("<b>REPORTE DE RESERVAS</b>", title_style)
        elements.append(title)
        
        # Rango
        rango_p = Paragraph(f"<b>{titulo_rango}</b>", styles['Heading2'])
        elements.append(rango_p)
        elements.append(Spacer(1, 0.2*inch))
        
        # Total
        total_p = Paragraph(f"<b>Total de reservas:</b> {len(reservas)}", styles['Normal'])
        elements.append(total_p)
        elements.append(Spacer(1, 0.3*inch))
        
        # Tabla
        data = [['#', 'Cliente', 'Mesa', 'Fecha', 'Hora', 'Personas', 'Estado']]
        
        for idx, reserva in enumerate(reservas, 1):
            data.append([
                str(idx),
                reserva.cliente.nombre[:20],
                str(reserva.mesa.numeroMesa),
                reserva.fecha.strftime("%d/%m/%Y"),
                reserva.hora,
                str(reserva.numeroPersonas),
                reserva.estado
            ])
        
        table = Table(data, colWidths=[0.5*inch, 2*inch, 0.7*inch, 1*inch, 0.8*inch, 0.8*inch, 1*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e74c3c')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
        ]))
        
        elements.append(table)
        
        # Construir
        doc.build(elements)
        
        buffer.seek(0)
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="reporte_reservas_{datetime.now().strftime("%Y%m%d")}.pdf"'
        
        return response
        
    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
        return redirect('informes_admin')


def reporte_mesas_pdf(request):
    """Generar PDF con estado de mesas por fecha/hora"""
    if not request.user.is_authenticated or not request.user.is_superuser:
        return redirect('login_admin')
    
    try:
        # Obtener filtros
        fecha = request.GET.get('fecha')
        hora = request.GET.get('hora')
        
        if not fecha or not hora:
            messages.error(request, 'Debes seleccionar fecha y hora.')
            return redirect('informes_admin')
        
        fecha_obj = datetime.strptime(fecha, "%Y-%m-%d").date()
        
        # Obtener mesas
        mesas = list(Mesa.objects.order_by('numeroMesa'))
        
        # Obtener reservas
        reservas = Reserva.objects(
            fecha=fecha_obj,
            hora=hora,
            estado="Reservada"
        )
        
        mesas_ocupadas = {r.mesa.numeroMesa: r for r in reservas}
        
        # Crear PDF
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        title = Paragraph("<b>REPORTE DE ESTADO DE MESAS</b>", title_style)
        elements.append(title)
        
        info_p = Paragraph(f"<b>Fecha:</b> {fecha_obj.strftime('%d/%m/%Y')} | <b>Hora:</b> {hora}", styles['Heading2'])
        elements.append(info_p)
        elements.append(Spacer(1, 0.3*inch))
        
        # Estadísticas
        ocupadas = len(mesas_ocupadas)
        disponibles = len(mesas) - ocupadas
        
        stats_p = Paragraph(f"<b>Mesas Ocupadas:</b> {ocupadas} | <b>Mesas Disponibles:</b> {disponibles}", styles['Normal'])
        elements.append(stats_p)
        elements.append(Spacer(1, 0.3*inch))
        
        # Tabla
        data = [['Mesa', 'Capacidad', 'Estado', 'Cliente', 'Personas']]
        
        for mesa in mesas:
            if mesa.numeroMesa in mesas_ocupadas:
                reserva = mesas_ocupadas[mesa.numeroMesa]
                data.append([
                    str(mesa.numeroMesa),
                    str(mesa.capacidad),
                    'OCUPADA',
                    reserva.cliente.nombre[:20],
                    str(reserva.numeroPersonas)
                ])
            else:
                data.append([
                    str(mesa.numeroMesa),
                    str(mesa.capacidad),
                    'DISPONIBLE',
                    '-',
                    '-'
                ])
        
        table = Table(data, colWidths=[1*inch, 1.2*inch, 1.2*inch, 2.5*inch, 1.2*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#27ae60')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
        ]))
        
        elements.append(table)
        
        doc.build(elements)
        
        buffer.seek(0)
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="reporte_mesas_{fecha}_{hora.replace(":", "")}.pdf"'
        
        return response
        
    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
        return redirect('informes_admin')
    
def editar_cliente_admin(request, cliente_id):
    """Editar información de un cliente"""
    if not request.user.is_authenticated or not request.user.is_superuser:
        return redirect('login_admin')
    
    if request.method == 'POST':
        try:
            cliente = Cliente.objects.get(id=cliente_id)
            
            # Obtener datos del formulario
            nombre = request.POST.get('nombre', '').strip()
            ci = request.POST.get('ci', '').strip()
            email = request.POST.get('email', '').strip()
            telefono = request.POST.get('telefono', '').strip()
            
            # Validaciones
            if not all([nombre, ci, email, telefono]):
                messages.error(request, 'Todos los campos son obligatorios.')
                return redirect('clientes_admin')
            
            # Verificar si la cédula ya existe en otro cliente
            cliente_existente = Cliente.objects(ci=ci, id__ne=cliente_id).first()
            if cliente_existente:
                messages.error(request, f'Ya existe un cliente con la cédula {ci}.')
                return redirect('clientes_admin')
            
            # Actualizar datos
            cliente.nombre = nombre
            cliente.ci = ci
            cliente.email = email
            cliente.telefono = telefono
            cliente.save()
            
            # Registrar actividad
            actividad = Actividad(
                descripcion=f"Información actualizada por administrador {request.user.username}",
                fecha=datetime.now()
            )
            actividad.save()
            
            cliente.actividad.append(actividad)
            cliente.save()
            
            messages.success(request, f'Cliente {nombre} actualizado exitosamente.')
            return redirect('clientes_admin')
            
        except Cliente.DoesNotExist:
            messages.error(request, 'Cliente no encontrado.')
            return redirect('clientes_admin')
        except Exception as e:
            messages.error(request, f'Error al actualizar: {str(e)}')
            return redirect('clientes_admin')
    
    return redirect('clientes_admin')


def eliminar_cliente_admin(request, cliente_id):
    """Eliminar un cliente del sistema"""
    if not request.user.is_authenticated or not request.user.is_superuser:
        return redirect('login_admin')
    
    if request.method == 'POST':
        try:
            cliente = Cliente.objects.get(id=cliente_id)
            
            # Verificar si tiene reservas activas
            reservas_activas = Reserva.objects(
                cliente__idCliente=str(cliente.id),
                estado="Reservada"
            ).count()
            
            if reservas_activas > 0:
                messages.error(request, f'No se puede eliminar. El cliente tiene {reservas_activas} reserva(s) activa(s).')
                return redirect('clientes_admin')
            
            # Guardar nombre antes de eliminar
            nombre_cliente = cliente.nombre
            
            # Eliminar el cliente
            cliente.delete()
            
            messages.success(request, f'Cliente {nombre_cliente} eliminado exitosamente.')
            return redirect('clientes_admin')
            
        except Cliente.DoesNotExist:
            messages.error(request, 'Cliente no encontrado.')
            return redirect('clientes_admin')
        except Exception as e:
            messages.error(request, f'Error al eliminar: {str(e)}')
            return redirect('clientes_admin')
    
    return redirect('clientes_admin')