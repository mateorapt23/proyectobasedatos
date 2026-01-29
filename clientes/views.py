from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password
from .models import Cliente, Actividad  # Actividad está en el mismo archivo models.py
from .validators import validar_email, validar_telefono, validar_cedula
from reservas.models import Reserva
from datetime import datetime

def registro(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip().upper()
        ci = request.POST.get('ci', '').strip()
        telefono = request.POST.get('telefono', '').strip()
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')

        # Validaciones
        if not validar_cedula(ci):
            messages.error(request, 'Cédula inválida. Debe tener 10 dígitos numéricos.')
            return render(request, 'registro.html')

        if not validar_telefono(telefono):
            messages.error(request, 'Teléfono inválido. Debe tener 10 dígitos numéricos.')
            return render(request, 'registro.html')

        if not validar_email(email):
            messages.error(request, 'Correo electrónico inválido.')
            return render(request, 'registro.html')

        # Verificar si ya existe
        if Cliente.objects(ci=ci).first():
            messages.error(request, 'Ya existe un cliente registrado con esta cédula.')
            return render(request, 'registro.html')

        if Cliente.objects(email=email).first():
            messages.error(request, 'Ya existe un cliente registrado con este correo electrónico.')
            return render(request, 'registro.html')

        # Crear cliente
        try:
            Cliente(
                nombre=nombre,
                ci=ci,
                telefono=telefono,
                email=email,
                password=make_password(password)
            ).save()

            messages.success(request, 'Registro exitoso. Por favor inicia sesión.')
            return redirect('login')
        except Exception as e:
            messages.error(request, f'Error al registrar: {str(e)}')
            return render(request, 'registro.html')

    return render(request, 'registro.html')

def login_cliente(request):
    # Si ya está logueado, redirigir al panel
    if 'cliente_id' in request.session:
        return redirect('panel_cliente')

    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')

        try:
            cliente = Cliente.objects.get(email=email)
        except Cliente.DoesNotExist:
            return render(request, 'login.html', {
                'error': 'Credenciales incorrectas. Por favor verifica tu correo y contraseña.'
            })

        if not check_password(password, cliente.password):
            return render(request, 'login.html', {
                'error': 'Credenciales incorrectas. Por favor verifica tu correo y contraseña.'
            })

        # Crear sesión
        request.session['cliente_id'] = str(cliente.id)
        request.session['cliente_nombre'] = cliente.nombre
        request.session['cliente_email'] = cliente.email

        return redirect('panel_cliente')

    return render(request, 'login.html')

def panel_cliente(request):
    if 'cliente_id' not in request.session:
        return redirect('login')

    try:
        from facturas.models import Factura
        
        cliente_id = request.session['cliente_id']
        cliente = Cliente.objects.get(id=cliente_id)
        
        # Obtener estadísticas
        todas_reservas = Reserva.objects(cliente__idCliente=cliente_id)
        reservas_activas = todas_reservas.filter(
            fecha__gte=datetime.now().date(),
            estado="Reservada"
        ).count()
        
        total_reservas = todas_reservas.count()
        
        # Próximas reservas (máximo 3)
        proximas_reservas = list(todas_reservas.filter(
            fecha__gte=datetime.now().date(),
            estado="Reservada"
        ).order_by('fecha', 'hora')[:3])
        
        # Total de facturas
        total_facturas = Factura.objects(cliente__idCliente=cliente_id).count()
        
        # Actividades recientes (últimas 5)
        actividades_recientes = list(Actividad.objects(
            cliente_id=cliente_id
        ).order_by('-fecha')[:5])
        
        context = {
            'nombre': request.session['cliente_nombre'],
            'reservas_activas': reservas_activas,
            'total_reservas': total_reservas,
            'proximas_reservas': proximas_reservas,
            'total_facturas': total_facturas,
            'puntos': total_reservas * 10,  # 10 puntos por reserva
            'actividades_recientes': actividades_recientes,
        }
        
        return render(request, 'panel_cliente.html', context)
    except Exception as e:
        messages.error(request, f'Error al cargar el panel: {str(e)}')
        return redirect('login')

def logout_cliente(request):
    request.session.flush()
    messages.success(request, 'Has cerrado sesión exitosamente.')
    return redirect('landing')

def perfil_cliente(request):
    if 'cliente_id' not in request.session:
        return redirect('login')
    
    try:
        cliente = Cliente.objects.get(id=request.session['cliente_id'])
        
        if request.method == 'POST':
            # Actualizar perfil
            nombre = request.POST.get('nombre', '').strip().upper()
            telefono = request.POST.get('telefono', '').strip()
            
            if validar_telefono(telefono):
                cliente.nombre = nombre
                cliente.telefono = telefono
                cliente.save()
                
                request.session['cliente_nombre'] = nombre
                messages.success(request, 'Perfil actualizado exitosamente.')
            else:
                messages.error(request, 'Teléfono inválido.')
        
        return render(request, 'perfil.html', {
            'cliente': cliente,
            'nombre': request.session['cliente_nombre']
        })
    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
        return redirect('panel_cliente')