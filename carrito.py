from flask import Blueprint, render_template, session, redirect, url_for, request, flash

carrito_bp = Blueprint('carrito', __name__)

IVA_RATE = 0.19


def calcular_resumen_carrito(carrito):
    """Calcula el subtotal, el IVA y el total acumulado de los productos en el carrito."""
    subtotal = sum(float(item.get('precio', 0)) * int(item.get('cantidad', 1)) for item in carrito)
    iva = round(subtotal * IVA_RATE, 2)
    total = round(subtotal + iva, 2)
    return {
        'subtotal': round(subtotal, 2),
        'iva': iva,
        'total': total,
    }


@carrito_bp.route('/carrito')
def ver_carrito():
    if 'user_id' not in session:
        return redirect(url_for('login.login'))

    # Restricción: Si es administrador, no puede ver el carrito
    if session.get('rol') in ['admin', 'superadmin']:
        flash('Los administradores no tienen habilitada la función de compra.', 'warning')
        return redirect(request.referrer or url_for('index'))

    carrito = session.get('carrito', [])
    resumen = calcular_resumen_carrito(carrito)

    return render_template(
        'carrito.html',
        carrito=carrito,
        subtotal=resumen['subtotal'],
        iva=resumen['iva'],
        total=resumen['total'],
    )


@carrito_bp.route('/agregar/<int:id_producto>')
def agregar(id_producto):
    if 'user_id' not in session:
        return redirect(url_for('login.login'))

    # BLOQUEO PRINCIPAL: Si es admin, no permite agregar nada al carrito
    if session.get('rol') in ['admin', 'superadmin']:
        flash('Cuenta de Administrador: Las funciones de compra están desactivadas para tu rol.', 'warning')
        return redirect(request.referrer or url_for('index'))

    from app import mysql
    cursor = mysql.connection.cursor()
    
    # Consulta la información del producto verificando si existe alguna oferta activa
    query = """
        SELECT 
            id_productos, 
            nombre, 
            CASE 
                WHEN oferta_fin IS NOT NULL AND oferta_fin > NOW() THEN precio_oferta 
                ELSE precio 
            END AS precio_final
        FROM productos 
        WHERE id_productos = %s
    """
    cursor.execute(query, (id_producto,))
    producto = cursor.fetchone()
    cursor.close()

    if producto:
        item = {
            'id': producto[0],
            'nombre': producto[1],
            'precio': float(producto[2]),
            'cantidad': 1,
        }

        if 'carrito' not in session:
            session['carrito'] = []

        existente = None
        for producto_en_carrito in session['carrito']:
            if producto_en_carrito.get('id') == producto[0]:
                existente = producto_en_carrito
                break

        # Incrementa la cantidad si el producto ya existe en la sesión
        if existente is not None:
            existente['cantidad'] = int(existente.get('cantidad', 1)) + 1
        else:
            session['carrito'].append(item)

        session.modified = True

        flash(f'"{producto[1]}" ¡fue añadido al carrito exitosamente!', 'success')

    return redirect(request.referrer or url_for('index'))


@carrito_bp.route('/eliminar/<int:index>')
def eliminar(index):
    if 'carrito' in session and 0 <= index < len(session['carrito']):
        session['carrito'].pop(index)
        session.modified = True

    return redirect(url_for('carrito.ver_carrito'))


@carrito_bp.route('/actualizar-carrito/<int:index>', methods=['POST'])
def actualizar_carrito(index):
    if 'carrito' in session and 0 <= index < len(session['carrito']):
        cantidad = int(request.form.get('cantidad', 1))
        if cantidad <= 0:
            session['carrito'].pop(index)
        else:
            session['carrito'][index]['cantidad'] = cantidad
        session.modified = True

    return redirect(url_for('carrito.ver_carrito'))


@carrito_bp.route('/finalizar')
def finalizar_compra():
    if 'user_id' not in session:
        return redirect(url_for('login.login'))

    if session.get('rol') in ['admin', 'superadmin']:
        flash('Los administradores no pueden realizar compras.', 'warning')
        return redirect(request.referrer or url_for('index'))

    carrito = session.get('carrito', [])
    if not carrito:
        return redirect(url_for('carrito.ver_carrito'))

    resumen = calcular_resumen_carrito(carrito)
    
    session['checkout'] = {
        'carrito': carrito,
        'subtotal': resumen['subtotal'],
        'iva': resumen['iva'],
        'total': resumen['total'],
    }
    session.modified = True
    return redirect(url_for('carrito.pago'))


@carrito_bp.route('/pago', methods=['GET', 'POST'])
def pago():
    if 'user_id' not in session:
        return redirect(url_for('login.login'))

    if session.get('rol') in ['admin', 'superadmin']:
        flash('Los administradores no pueden acceder a la pasarela de pago.', 'warning')
        return redirect(request.referrer or url_for('index'))

    checkout = session.get('checkout')
    carrito = checkout.get('carrito', []) if checkout else session.get('carrito', [])

    if not carrito:
        flash('Tu carrito está vacío.', 'warning')
        return redirect(url_for('carrito.ver_carrito'))

    resumen = checkout if checkout else calcular_resumen_carrito(carrito)

    if request.method == 'POST':
        telefono = request.form.get('telefono', '').strip()
        metodo_pago = request.form.get('metodo_pago', '').strip()
        numero_tarjeta = request.form.get('numero_tarjeta', '').strip()
        nombre_titular = request.form.get('nombre_titular', '').strip()
        fecha_vencimiento = request.form.get('fecha_vencimiento', '').strip()
        codigo_seguridad = request.form.get('codigo_seguridad', '').strip()

        if not telefono:
            flash('Ingresa tu número de teléfono para continuar.', 'warning')
            return render_template('pago.html', carrito=carrito, subtotal=resumen['subtotal'], iva=resumen['iva'], total=resumen['total'], telefono=telefono, metodo_pago=metodo_pago, numero_tarjeta=numero_tarjeta, nombre_titular=nombre_titular, fecha_vencimiento=fecha_vencimiento, codigo_seguridad=codigo_seguridad)

        if metodo_pago not in {'paypal', 'nequi', 'daviplata', 'debito', 'credito'}:
            flash('Selecciona un método de pago.', 'warning')
            return render_template('pago.html', carrito=carrito, subtotal=resumen['subtotal'], iva=resumen['iva'], total=resumen['total'], telefono=telefono, metodo_pago=metodo_pago, numero_tarjeta=numero_tarjeta, nombre_titular=nombre_titular, fecha_vencimiento=fecha_vencimiento, codigo_seguridad=codigo_seguridad)

        if metodo_pago in {'debito', 'credito'} and (not numero_tarjeta or not nombre_titular or not fecha_vencimiento or not codigo_seguridad):
            flash('Completa los datos de la tarjeta para continuar.', 'warning')
            return render_template('pago.html', carrito=carrito, subtotal=resumen['subtotal'], iva=resumen['iva'], total=resumen['total'], telefono=telefono, metodo_pago=metodo_pago, numero_tarjeta=numero_tarjeta, nombre_titular=nombre_titular, fecha_vencimiento=fecha_vencimiento, codigo_seguridad=codigo_seguridad)

        from app import mysql

        cursor = mysql.connection.cursor()
        for item in carrito:
            precio_linea = float(item.get('precio', 0)) * int(item.get('cantidad', 1))
            cursor.execute("""
                INSERT INTO compras (user_id, producto, precio)
                VALUES (%s, %s, %s)
            """, (session['user_id'], item['nombre'], precio_linea))

        mysql.connection.commit()
        cursor.close()

        session['carrito'] = []
        session.pop('checkout', None)
        session.modified = True

        return render_template(
            'pago.html',
            carrito=[],
            subtotal=0,
            iva=0,
            total=0,
            compra_confirmada=True,
            telefono=telefono,
            metodo_pago=metodo_pago,
            numero_tarjeta=numero_tarjeta if metodo_pago in {'debito', 'credito'} else '',
            nombre_titular=nombre_titular if metodo_pago in {'debito', 'credito'} else '',
            fecha_vencimiento=fecha_vencimiento if metodo_pago in {'debito', 'credito'} else '',
            codigo_seguridad=codigo_seguridad if metodo_pago in {'debito', 'credito'} else '',
        )

    return render_template(
        'pago.html',
        carrito=carrito,
        subtotal=resumen['subtotal'],
        iva=resumen['iva'],
        total=resumen['total'],
        telefono='',
        metodo_pago='',
        numero_tarjeta='',
        nombre_titular='',
        fecha_vencimiento='',
        codigo_seguridad='',
    )