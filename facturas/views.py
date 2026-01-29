from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse
from .models import Factura
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.units import inch
import io

def mis_facturas(request):
    if 'cliente_id' not in request.session:
        messages.error(request, 'Debes iniciar sesión para ver tus facturas.')
        return redirect('login')

    try:
        cliente_id = request.session['cliente_id']
        
        # Obtener todas las facturas del cliente
        todas_facturas = list(Factura.objects(
            cliente__idCliente=cliente_id
        ).order_by('-fechaEmision'))
        
        # Calcular totales
        total_gastado = sum(f.total for f in todas_facturas)
        mes_actual_total = sum(
            f.total for f in todas_facturas 
            if f.fechaEmision.month == datetime.now().month 
            and f.fechaEmision.year == datetime.now().year
        )
        
        # Preparar facturas para la vista
        facturas = []
        for factura in todas_facturas:
            facturas.append({
                'id': str(factura.id),
                'numero': factura.numero,
                'fecha': factura.fechaEmision,
                'reserva': factura.reserva,
                'monto': f'{factura.total:.2f}',
                'subtotal': f'{factura.subtotal:.2f}',
                'iva': f'{factura.iva:.2f}',
                'estado': factura.estado,
                'esGarantia': factura.esGarantia,
                'detallesConsumo': factura.detallesConsumo
            })
        
        context = {
            'nombre': request.session['cliente_nombre'],
            'facturas': facturas,
            'total_facturas': len(facturas),
            'total_gastado': f'{total_gastado:.2f}',
            'mes_actual': f'{mes_actual_total:.2f}',
            'total_descargas': len(facturas) * 2,  # Simulado
        }
        
        return render(request, 'mis_facturas.html', context)
        
    except Exception as e:
        messages.error(request, f'Error al cargar las facturas: {str(e)}')
        return redirect('panel_cliente')

def descargar_factura(request, factura_id):
    if 'cliente_id' not in request.session:
        return redirect('login')
    
    try:
        # Obtener la factura
        factura = Factura.objects.get(id=factura_id)
        
        # Verificar que pertenece al cliente
        if factura.cliente.idCliente != request.session['cliente_id']:
            messages.error(request, 'No tienes permiso para descargar esta factura.')
            return redirect('mis_facturas')
        
        # Crear el PDF
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()
        
        # Título
        title = Paragraph("<b>FACTURA</b>", styles['Title'])
        elements.append(title)
        elements.append(Spacer(1, 0.3*inch))
        
        # Información del restaurante
        restaurant_info = Paragraph(
            "<b>Restaurante Abad/Rod</b><br/>"
            "Calle Principal #123<br/>"
            "Quito, Ecuador<br/>"
            "Tel: (02) 234-5678<br/>"
            "RUC: 1234567890001",
            styles['Normal']
        )
        elements.append(restaurant_info)
        elements.append(Spacer(1, 0.3*inch))
        
        # Información de la factura
        fecha_emision = factura.fechaEmision.strftime("%d/%m/%Y")
        
        factura_info = Paragraph(
            f"<b>Factura N°:</b> {factura.numero}<br/>"
            f"<b>Fecha de Emisión:</b> {fecha_emision}<br/>"
            f"<b>Cliente:</b> {factura.cliente.nombre}<br/>"
            f"<b>Cédula:</b> {factura.cliente.ci}",
            styles['Normal']
        )
        elements.append(factura_info)
        elements.append(Spacer(1, 0.5*inch))
        
        # Detalles de la factura
        data = [
            ['Descripción', 'Cantidad', 'Precio Unit.', 'Total'],
        ]
        
        if factura.esGarantia:
            # Factura de garantía
            data.append([
                f'Garantía de Reserva - Mesa {factura.reserva.numeroMesa}',
                1,
                f'${factura.subtotal:.2f}',
                f'${factura.subtotal:.2f}'
            ])
        else:
            # Factura procesada con consumo
            data.append([
                factura.detallesConsumo,
                factura.reserva.numeroPersonas,
                f'${factura.subtotal / factura.reserva.numeroPersonas:.2f}',
                f'${factura.subtotal:.2f}'
            ])
        
        data.append([
            f'Fecha: {factura.reserva.fecha.strftime("%d/%m/%Y")}',
            '', '', ''
        ])
        data.append([
            f'Hora: {factura.reserva.hora}',
            '', '', ''
        ])
        
        table = Table(data, colWidths=[3*inch, 1*inch, 1.5*inch, 1.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Totales
        totales_data = [
            ['', '', 'Subtotal:', f'${factura.subtotal:.2f}'],
            ['', '', 'IVA (12%):', f'${factura.iva:.2f}'],
            ['', '', 'TOTAL:', f'${factura.total:.2f}'],
        ]
        
        totales_table = Table(totales_data, colWidths=[3*inch, 1*inch, 1.5*inch, 1.5*inch])
        totales_table.setStyle(TableStyle([
            ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (2, 2), (-1, 2), 'Helvetica-Bold'),
            ('FONTSIZE', (2, 2), (-1, 2), 14),
            ('LINEABOVE', (2, 2), (-1, 2), 2, colors.black),
        ]))
        
        elements.append(totales_table)
        elements.append(Spacer(1, 0.5*inch))
        
        # Nota sobre garantía
        if factura.esGarantia:
            nota = Paragraph(
                "<b>NOTA IMPORTANTE:</b><br/>"
                "Esta es una factura de garantía de reserva por $30.00. "
                "Este monto será descontado de su consumo total cuando asista al restaurante. "
                "Si no asiste a su reserva, este monto no será reembolsado.",
                styles['Normal']
            )
            elements.append(nota)
            elements.append(Spacer(1, 0.3*inch))
        
        # Pie de página
        footer = Paragraph(
            "<i>Gracias por su preferencia</i><br/>"
            "Esta factura es un documento válido para efectos tributarios",
            styles['Normal']
        )
        elements.append(footer)
        
        # Construir PDF
        doc.build(elements)
        
        # Preparar respuesta
        buffer.seek(0)
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="factura_{factura.numero}.pdf"'
        
        return response
        
    except Factura.DoesNotExist:
        messages.error(request, 'La factura no existe.')
        return redirect('mis_facturas')
    except Exception as e:
        messages.error(request, f'Error al generar la factura: {str(e)}')
        return redirect('mis_facturas')

def imprimir_factura(request, factura_id):
    # Similar a descargar pero con Content-Disposition: inline
    if 'cliente_id' not in request.session:
        return redirect('login')
    
    try:
        factura = Factura.objects.get(id=factura_id)
        
        if factura.cliente.idCliente != request.session['cliente_id']:
            messages.error(request, 'No tienes permiso para imprimir esta factura.')
            return redirect('mis_facturas')
        
        # Reutilizar la lógica de descargar pero cambiar disposición
        response = descargar_factura(request, factura_id)
        response['Content-Disposition'] = f'inline; filename="factura_{factura.numero}.pdf"'
        
        return response
        
    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
        return redirect('mis_facturas')

def ver_factura(request, factura_id):
    """Vista para obtener detalles de factura para el modal"""
    if 'cliente_id' not in request.session:
        return redirect('login')
    
    try:
        from django.http import JsonResponse
        
        factura = Factura.objects.get(id=factura_id)
        
        if factura.cliente.idCliente != request.session['cliente_id']:
            return JsonResponse({'error': 'No autorizado'}, status=403)
        
        data = {
            'numero': factura.numero,
            'fecha': factura.fechaEmision.strftime("%d/%m/%Y"),
            'monto': f'{factura.total:.2f}',
            'subtotal': f'{factura.subtotal:.2f}',
            'iva': f'{factura.iva:.2f}',
            'mesa': factura.reserva.numeroMesa,
            'personas': factura.reserva.numeroPersonas,
            'reservaFecha': factura.reserva.fecha.strftime("%d/%m/%Y"),
            'reservaHora': factura.reserva.hora,
            'estado': factura.estado,
            'esGarantia': factura.esGarantia,
            'detalles': factura.detallesConsumo
        }
        
        return JsonResponse(data)
        
    except Factura.DoesNotExist:
        return JsonResponse({'error': 'Factura no encontrada'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)