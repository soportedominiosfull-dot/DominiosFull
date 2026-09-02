from flask import Blueprint, render_template, session, redirect, url_for, current_app, request, flash, send_file
from flask_mail import Message
import os
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from datetime import datetime
import subprocess

# Inicializa el Blueprint encargado de la gestión de servicios, facturación y productos.
servicios_bp = Blueprint('servicios', __name__)

# GESTIÓN DE ROLES Y SOLICITUDES

@servicios_bp.route('/solicitar-cambio-rol', methods=['POST'])
def solicitar_cambio_rol():
    # Valida el acceso exclusivo para administradores
    if 'rol' in session and session['rol'] in ['admin', 'superadmin']:
        usuario_id = request.form.get('usuario_id')
        nuevo_rol = request.form.get('nuevo_rol', '').strip().lower()

        mysql = current_app.extensions['mysql']
        mail = current_app.extensions['mail']
        cur = mysql.connection.cursor()

        # Obtiene nombre, email y rol actual del cliente
        cur.execute("SELECT nombre, email, rol FROM usuarios WHERE id = %s", (usuario_id,))
        usuario = cur.fetchone()

        if usuario:
            nombre_cliente, email_cliente = usuario[0], usuario[1]
            rol_actual = str(usuario[2]).strip().lower()

            # Validación: si ya posee el mismo rol que se intenta asignar
            if rol_actual == nuevo_rol:
                cur.close()
                rol_texto = "Administrador" if rol_actual == 'admin' else ("Super Admin" if rol_actual == 'superadmin' else "Cliente")
                flash(f"El usuario {nombre_cliente} ya tiene el rol de {rol_texto}.", "info")
                return redirect(url_for('servicios.admin_clientes'))

            # Consulta todos los correos de Super Admins en la Base de Datos
            cur.execute("SELECT email FROM usuarios WHERE LOWER(rol) = 'superadmin'")
            superadmins = cur.fetchall()
            cur.close()

            # Extrae la lista de emails y asegura la inclusión estática de Samuel
            destinatarios = [row[0] for row in superadmins if row[0]]
            correo_samuel = "samuel_chaconst@gfc.edu.co"
            if correo_samuel not in destinatarios:
                destinatarios.append(correo_samuel)

            # ELIMINAR al usuario sancionado/modificado de la lista de destinatarios
            if email_cliente in destinatarios:
                destinatarios.remove(email_cliente)

            if str(usuario_id) == str(session.get('user_id')) or str(usuario_id) == '1':
                flash("❌ Acción denegada: No puedes modificar tu propio rol ni el del Super Admin Principal.", "danger")
                return redirect(url_for('servicios.admin_clientes'))

            # Genera un token firmado con los datos de la solicitud (validez de 24 hrs)
            serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
            token = serializer.dumps({'usuario_id': usuario_id, 'nuevo_rol': nuevo_rol}, salt='cambio-rol-salt')

            # Genera los enlaces de Aprobación / Rechazo
            url_aprobar = url_for('servicios.procesar_solicitud_rol', token=token, accion='aprobar', _external=True)
            url_rechazar = url_for('servicios.procesar_solicitud_rol', token=token, accion='rechazar', _external=True)

            try:
                msg = Message(
                    "Solicitud de Aprobación: Cambio de Rol de Usuario",
                    sender="soporte.dominiosfull@gmail.com",
                    recipients=destinatarios
                )
                msg.body = f"""Hola Super Administrador,

                    Un administrador ha solicitado cambiar el rol del siguiente usuario:

                    - ID Usuario: {usuario_id}
                    - Nombre: {nombre_cliente}
                    - Correo: {email_cliente}
                    - Nuevo Rol Solicitado: {nuevo_rol.upper()}

                    Haz clic en una opción para responder (el enlace expira en 24 horas):   

                    ✅ APROBAR CAMBIO DE ROL:
                    {url_aprobar}

                    ❌ RECHAZAR SOLICITUD:
                    {url_rechazar}      

                    ---
                    Mensaje automático de DominiosFull.
                    """
                mail.send(msg)
                flash(f"Solicitud enviada a los Super Administradores para cambiar el rol de {nombre_cliente}.", "success")
            except Exception as mail_error:
                flash(f"Error al enviar la solicitud por correo: {str(mail_error)}", "danger")
        else:
            cur.close()
            flash("El usuario no existe.", "warning")

        return redirect(url_for('servicios.admin_clientes'))
    else:
        return redirect(url_for('login.login'))


@servicios_bp.route('/procesar-solicitud-rol/<token>/<accion>')
def procesar_solicitud_rol(token, accion):
    if 'rol' in session and session['rol'] in ['admin', 'superadmin']:
        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])

        try:
            # Descifra el token (expira en 24 horas)
            datos = serializer.loads(token, salt='cambio-rol-salt', max_age=86400)
            usuario_id = datos['usuario_id']
            nuevo_rol = datos['nuevo_rol']
        except SignatureExpired:
            flash("El enlace de autorización ha expirado (válido por 24 horas). Vuelve a realizar la solicitud.", "warning")
            return redirect(url_for('servicios.admin_clientes'))
        except BadSignature:
            flash("Enlace de autorización inválido o alterado.", "danger")
            return redirect(url_for('servicios.admin_clientes'))

        mysql = current_app.extensions['mysql']
        cur = mysql.connection.cursor()

        if accion == 'aprobar':
            cur.execute("UPDATE usuarios SET rol = %s WHERE id = %s", (nuevo_rol, usuario_id))
            mysql.connection.commit()
            cur.close()
            flash(f"✅ Cambio de rol a '{nuevo_rol.upper()}' APROBADO para el usuario ID {usuario_id}.", "success")
        elif accion == 'rechazar':
            cur.close()
            flash(f"❌ Solicitud RECHAZADA. El usuario ID {usuario_id} conserva su rol actual.", "info")

        return redirect(url_for('servicios.admin_clientes'))
    else:
        flash("Debes iniciar sesión con una cuenta de Administrador para procesar solicitudes.", "warning")
        return redirect(url_for('login.login'))

# ADMINISTRACIÓN DE CLIENTES Y SUSPENSIÓN

@servicios_bp.route('/admin-clientes.servicios')
def admin_clientes():
    if 'rol' in session and session['rol'] in ['admin', 'superadmin']:
        mysql = current_app.extensions['mysql']
        cur = mysql.connection.cursor()
        
        cur.execute("SELECT id, nombre, email, estado, rol FROM usuarios")
        clientes = cur.fetchall()
        
        # Se agrega DATE_ADD(c.fecha, INTERVAL 1 YEAR) PARA EL TIEMPO DE RENOVAR FACTURA
        cur.execute("""
            SELECT 
                c.id, 
                COALESCE(u.nombre, 'Usuario Eliminado'), 
                c.producto, 
                c.precio, 
                c.fecha, 
                c.factura_enviada,
                f.estado AS estado_factura,
                c.factura_id,
                DATE_ADD(c.fecha, INTERVAL 1 YEAR) AS fecha_expiracion
            FROM compras c
            LEFT JOIN usuarios u ON c.user_id = u.id
            LEFT JOIN facturas f ON c.factura_id = f.id
            ORDER BY c.fecha DESC
        """)
        compras = cur.fetchall()
        cur.close()
        
        # Pasamos 'ahora' a la plantilla HTML
        ahora = datetime.now()
        return render_template('admin-clientes.servicios.html', clientes=clientes, compras=compras, ahora=ahora)
    else:
        return redirect(url_for('login.login'))

@servicios_bp.route('/suspender-cliente/<int:id>', methods=['POST'])
def suspender_cliente(id):
    if 'rol' in session and session['rol'] in ['admin', 'superadmin']:
        # Protección estricta: Nadie puede suspender al Super Admin Principal (ID 1)
        if id == 1:
            flash("❌ Acción denegada: No es posible suspender al Super Administrador Principal.", "danger")
            return redirect(url_for('servicios.admin_clientes'))

        justificacion = request.form.get('justificacion', '').strip()
        
        mysql = current_app.extensions['mysql']
        mail = current_app.extensions['mail']
        cur = mysql.connection.cursor()
        
        # Obtiene datos y rol del usuario a suspender
        cur.execute("SELECT email, nombre, rol FROM usuarios WHERE id = %s", (id,))
        usuario = cur.fetchone()
        
        if not usuario:
            cur.close()
            flash("Usuario no encontrado.", "warning")
            return redirect(url_for('servicios.admin_clientes'))

        email_cliente, nombre_cliente, rol_cliente = usuario[0], usuario[1], str(usuario[2]).strip().lower()

        # CASO 1: Si el objetivo es un ADMINISTRADOR o SUPERADMIN -> Requiere aprobación por correo de los Super Admins
        if rol_cliente in ['admin', 'superadmin']:
            # Obtiene correos de los Super Admins registrados en la BD
            cur.execute("SELECT email FROM usuarios WHERE LOWER(rol) = 'superadmin'")
            superadmins = cur.fetchall()
            cur.close()

            # Construye lista de destinatarios asegurando a Samuel Chacón
            destinatarios = [row[0] for row in superadmins if row[0]]
            correo_samuel = "samuel_chaconst@gfc.edu.co"
            if correo_samuel not in destinatarios:
                destinatarios.append(correo_samuel)

            # 🔒 ELIMINAR al usuario sancionado/modificado de la lista de destinatarios
            if email_cliente in destinatarios:
                destinatarios.remove(email_cliente)

            serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
            token = serializer.dumps({'usuario_id': id, 'justificacion': justificacion}, salt='suspension-admin-salt')

            url_aprobar = url_for('servicios.procesar_suspension_admin', token=token, accion='aprobar', _external=True)
            url_rechazar = url_for('servicios.procesar_suspension_admin', token=token, accion='rechazar', _external=True)

            try:
                msg = Message(
                    "Solicitud de Aprobación: Suspensión de Administrador",
                    sender="soporte.dominiosfull@gmail.com",
                    recipients=destinatarios
                )
                msg.body = f"""Hola Super Administrador,

Un administrador ha solicitado suspender la cuenta de otro Administrador/Super Admin:

- ID Admin: {id}
- Nombre: {nombre_cliente}
- Correo: {email_cliente}
- Rol actual: {rol_cliente.upper()}
- Motivo expuesto: {justificacion}

Haz clic en una opción para autorizar la suspensión (Válido por 24 horas):

✅ APROBAR SUSPENSIÓN DE ADMIN:
{url_aprobar}

❌ RECHAZAR SUSPENSIÓN:
{url_rechazar}

---
Mensaje automático de DominiosFull.
"""
                mail.send(msg)
                flash(f"Solicitud de suspensión enviada a los Super Administradores para el usuario {nombre_cliente}.", "success")
            except Exception as mail_error:
                flash(f"Error al enviar la solicitud de suspensión: {str(mail_error)}", "danger")
            
            return redirect(url_for('servicios.admin_clientes'))

        # CASO 2: Si el objetivo es un CLIENTE -> Suspensión inmediata
        cur.execute("UPDATE usuarios SET estado = 'suspendido' WHERE id = %s", (id,))
        mysql.connection.commit()
        cur.close()

        try:
            msg = Message(
                "Tu cuenta ha sido suspendida - DominiosFull",
                sender="soporte.dominiosfull@gmail.com",
                recipients=[email_cliente]
            )
            msg.body = f"Hola {nombre_cliente},\n\nTe informamos que tu cuenta en DominiosFull ha sido suspendida por el administrador.\n\nMotivo del baneo:\n{justificacion}\n\nSi crees que esto es un error, por favor ponte en contacto con soporte."
            mail.send(msg)
            flash(f"Cliente {nombre_cliente} suspendido con éxito y correo notificado.", "success")
        except Exception as mail_error:
            flash(f"Cliente suspendido, pero falló el envío del correo: {str(mail_error)}", "warning")

        return redirect(url_for('servicios.admin_clientes'))
    else:
        return redirect(url_for('login.login'))


@servicios_bp.route('/procesar-suspension-admin/<token>/<accion>')
def procesar_suspension_admin(token, accion):
    if 'rol' in session and session['rol'] in ['admin', 'superadmin']:
        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])

        try:
            datos = serializer.loads(token, salt='suspension-admin-salt', max_age=86400)
            usuario_id = datos['usuario_id']
            justificacion = datos['justificacion']
        except SignatureExpired:
            flash("El enlace de aprobación ha expirado (válido por 24 horas).", "warning")
            return redirect(url_for('servicios.admin_clientes'))
        except BadSignature:
            flash("Enlace de autorización inválido o alterado.", "danger")
            return redirect(url_for('servicios.admin_clientes'))

        mysql = current_app.extensions['mysql']
        mail = current_app.extensions['mail']
        cur = mysql.connection.cursor()

        if accion == 'aprobar':
            cur.execute("SELECT email, nombre FROM usuarios WHERE id = %s", (usuario_id,))
            usuario = cur.fetchone()

            if usuario:
                email_admin, nombre_admin = usuario[0], usuario[1]

                cur.execute("UPDATE usuarios SET estado = 'suspendido' WHERE id = %s", (usuario_id,))
                mysql.connection.commit()

                try:
                    msg = Message(
                        "Notificación de Suspensión de Cuenta Administradora - DominiosFull",
                        sender="soporte.dominiosfull@gmail.com",
                        recipients=[email_admin]
                    )
                    msg.body = f"Hola {nombre_admin},\n\nTu cuenta administrativa en DominiosFull ha sido suspendida tras la revisión y aprobación de la administración principal.\n\nMotivo de la suspensión:\n{justificacion}\n\nSi consideras que hay un desacuerdo, comunícate directamente con la dirección general."
                    mail.send(msg)
                    flash(f"✅ Suspensión del Administrador ID {usuario_id} APROBADA y notificada por correo.", "success")
                except Exception as mail_error:
                    flash(f"Admin suspendido, pero falló la notificación por correo: {str(mail_error)}", "warning")
            else:
                flash("El usuario ya no existe.", "warning")

        elif accion == 'rechazar':
            flash(f"❌ Solicitud RECHAZADA. El Administrador ID {usuario_id} sigue activo.", "info")

        cur.close()
        return redirect(url_for('servicios.admin_clientes'))
    else:
        flash("Debes iniciar sesión como Administrador para procesar esta solicitud.", "warning")
        return redirect(url_for('login.login'))

@servicios_bp.route('/reactivar-cliente/<int:id>', methods=['POST'])
def reactivar_cliente(id):
    if 'rol' in session and session['rol'] in ['admin', 'superadmin']:
        mysql = current_app.extensions['mysql']
        cur = mysql.connection.cursor()
        
        cur.execute("SELECT rol FROM usuarios WHERE id = %s", (id,))
        usuario = cur.fetchone()
        
        rol_nombre = "Administrador" if usuario and str(usuario[0]).strip().lower() in ['admin', 'superadmin'] else "Cliente"

        cur.execute("UPDATE usuarios SET estado = 'activo' WHERE id = %s", (id,))
        mysql.connection.commit()
        cur.close()
        
        flash(f"{rol_nombre} reactivado con éxito.", "success")
        return redirect(url_for('servicios.admin_clientes'))
    else:
        return redirect(url_for('login.login'))


# FACTURACIÓN Y PAGOS (PDF Y SANDBOX)


@servicios_bp.route('/generar-factura-renovacion/<int:compra_id>', methods=['POST'])
def generar_factura_renovacion(compra_id):
    if 'rol' in session and session['rol'] in ['admin', 'superadmin']:
        mysql = current_app.extensions['mysql']
        cur = mysql.connection.cursor()
        
        try:
            cur.execute("SELECT user_id, producto, precio FROM compras WHERE id = %s", (compra_id,))
            compra = cur.fetchone()
            
            if compra:
                user_id, producto, precio = compra[0], compra[1], compra[2]
                
                # 1. Crea la nueva factura con concepto de Renovación
                concepto_renovacion = f"Renovación Anual - {producto}"
                cur.execute("""
                    INSERT INTO facturas (user_id, total, estado, concepto, fecha_emision, fecha_vencimiento) 
                    VALUES (%s, %s, 'Pendiente', %s, NOW(), DATE_ADD(NOW(), INTERVAL 30 DAY))
                """, (user_id, precio, concepto_renovacion))
                
                factura_id = cur.lastrowid
                
                # 2. Actualiza la factura_id Y REINICIA LA FECHA DE LA COMPRA (NOW())
                cur.execute("""
                    UPDATE compras 
                    SET factura_id = %s, fecha = NOW() 
                    WHERE id = %s
                """, (factura_id, compra_id))
                
                mysql.connection.commit()
                flash(f"¡Factura de renovación #{factura_id} generada con éxito!", "success")
                
        except Exception as e:
            mysql.connection.rollback()
            flash(f"Error al generar factura de renovación: {str(e)}", "danger")
        finally:
            cur.close()
            
        return redirect(url_for('servicios.admin_clientes'))

@servicios_bp.route('/pagar-factura-simulacion/<int:factura_id>', methods=['POST'])
def pagar_factura_simulacion(factura_id):
    if 'user_id' in session:
        mysql = current_app.extensions['mysql']
        cur = mysql.connection.cursor()
        
        try:
            cur.execute("""
                UPDATE facturas 
                SET estado = 'Pagada' 
                WHERE id = %s AND user_id = %s
            """, (factura_id, session['user_id']))
            
            mysql.connection.commit()
            flash("💳 ¡Pago procesado con éxito! (Entorno de Prueba Sandbox)", "success")
        except Exception as e:
            mysql.connection.rollback()
            flash(f"Error al procesar el pago: {str(e)}", "danger")
        finally:
            cur.close()
            
        return redirect(url_for('vista_clientes'))
    else:
        return redirect(url_for('login.login'))

def crear_pdf_factura(factura_id, nombre_cliente, producto, precio):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    
    ruta_logo = os.path.join(current_app.root_path, 'static', 'img', 'logo-dominiosfull.png')
    
    if os.path.exists(ruta_logo):
        c.drawImage(ruta_logo, 100, 710, width=120, height=50, preserveAspectRatio=True, mask='auto')
    else:
        c.setFont("Helvetica-Bold", 20)
        c.drawString(100, 730, "DOMINIOSFULL")

    c.setFont("Helvetica", 9)
    c.drawString(100, 700, "Factura Electrónica de Venta")
    
    c.setFont("Helvetica-Bold", 12)
    c.drawString(380, 730, f"Factura N°: #{factura_id}")
    
    c.setLineWidth(1)
    c.setStrokeColorRGB(0.8, 0.8, 0.8)
    c.line(100, 685, 500, 685)
    
    c.setFont("Helvetica-Bold", 11)
    c.setFillColorRGB(0, 0, 0)
    c.drawString(100, 655, "Cliente:")
    c.setFont("Helvetica", 11)
    c.drawString(160, 655, str(nombre_cliente))
    
    c.setFillColorRGB(0.1, 0.4, 0.8)
    c.rect(100, 610, 400, 22, fill=True, stroke=False)
    
    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(110, 617, "Descripción del Servicio")
    c.drawString(420, 617, "Total")
    
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica", 10)
    c.drawString(110, 580, str(producto))
    c.drawString(420, 580, f"${precio:,.2f}")
    
    c.setStrokeColorRGB(0.8, 0.8, 0.8)
    c.line(100, 550, 500, 550)
    c.setFont("Helvetica-Oblique", 9)
    c.setFillColorRGB(0.4, 0.4, 0.4)
    c.drawString(100, 530, "¡Gracias por su compra en DominiosFull!")
    
    c.save()
    buffer.seek(0)
    return buffer

@servicios_bp.route('/descargar-factura/<int:factura_id>')
def descargar_factura(factura_id):
    if 'user_id' not in session:
        return redirect(url_for('login.login'))

    mysql = current_app.extensions['mysql']
    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT f.id, u.nombre, f.concepto, f.total 
        FROM facturas f
        JOIN usuarios u ON f.user_id = u.id
        WHERE f.id = %s AND (f.user_id = %s OR %s IN ('admin', 'superadmin'))
    """, (factura_id, session['user_id'], session.get('rol')))
    
    factura = cur.fetchone()
    cur.close()

    if factura:
        pdf_buffer = crear_pdf_factura(factura[0], factura[1], factura[2], factura[3])
        
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'factura_{factura_id}.pdf'
        )
    else:
        flash("La factura no existe o no tienes permisos para acceder a ella.", "warning")
        return redirect(url_for('vista_clientes'))


# GESTIÓN DE PRODUCTOS, OFERTAS Y ANALÍTICA


@servicios_bp.route('/admin-productos')
def admin_productos():
    if 'rol' in session and session['rol'] in ['admin', 'superadmin']:
        mysql = current_app.extensions['mysql']
        cur = mysql.connection.cursor()

        # 1. Desactiva automáticamente ofertas expiradas
        cur.execute("""
            UPDATE productos 
            SET precio_oferta = NULL, oferta_fin = NULL 
            WHERE oferta_fin IS NOT NULL AND oferta_fin <= NOW()
        """)
        mysql.connection.commit()

        # 2. Obtiene los productos filtrados según su categoría
        cur.execute("SELECT id_productos, nombre, categoria, precio, precio_oferta, oferta_fin FROM productos WHERE categoria = 'dominio'")
        dominios = cur.fetchall()

        cur.execute("SELECT id_productos, nombre, categoria, precio, precio_oferta, oferta_fin FROM productos WHERE categoria = 'hosting'")
        hostings = cur.fetchall()

        cur.execute("SELECT id_productos, nombre, categoria, precio, precio_oferta, oferta_fin FROM productos WHERE categoria = 'vps'")
        vps = cur.fetchall()

        # 3. Métricas de analítica (Productos más y menos vendidos - de V2)
        cur.execute("""
            SELECT 
                p.nombre, 
                p.categoria, 
                COUNT(c.id) AS ventas, 
                COALESCE(SUM(c.precio), 0) AS ingresos
            FROM productos p
            INNER JOIN compras c ON c.producto = p.nombre
            GROUP BY p.id_productos, p.nombre, p.categoria
            ORDER BY ventas DESC, ingresos DESC, p.nombre ASC
            LIMIT 5
        """)
        productos_mas_vendidos = cur.fetchall()

        cur.execute("""
            SELECT 
                p.nombre, 
                p.categoria, 
                COUNT(c.id) AS ventas, 
                COALESCE(SUM(c.precio), 0) AS ingresos
            FROM productos p
            LEFT JOIN compras c ON c.producto = p.nombre
            GROUP BY p.id_productos, p.nombre, p.categoria
            ORDER BY ventas ASC, ingresos ASC, p.nombre ASC
            LIMIT 5
        """)
        productos_menos_vendidos = cur.fetchall()

        cur.close()

        # Renderiza el panel administrativo con catálogos y analítica
        return render_template(
            'admin-productos.html', 
            dominios=dominios, 
            hostings=hostings, 
            vps=vps,
            productos_mas_vendidos=productos_mas_vendidos,
            productos_menos_vendidos=productos_menos_vendidos
        )
    else:
        return redirect(url_for('login.login'))

@servicios_bp.route('/crear-oferta', methods=['POST'])
def crear_oferta():
    if 'rol' in session and session['rol'] in ['admin', 'superadmin']:
        producto_id = request.form['producto_id']
        precio_oferta = request.form['precio_oferta']
        minutos = int(request.form['minutos'])

        mysql = current_app.extensions['mysql']
        cur = mysql.connection.cursor()

        cur.execute("""
            UPDATE productos 
            SET precio_oferta = %s, oferta_fin = DATE_ADD(NOW(), INTERVAL %s MINUTE)
            WHERE id_productos = %s
        """, (precio_oferta, minutos, producto_id))

        mysql.connection.commit()
        cur.close()

        flash('¡Oferta activada correctamente!', 'success')
        return redirect(url_for('servicios.admin_productos'))
        
    return redirect(url_for('login.login'))

# DESCARGA DE BACKUP DE BASE DE DATOS

@servicios_bp.route('/descargar-backup')
def descargar_backup():
    # Verificación de permisos: Normalizamos el valor a minúsculas y sin espacios
    rol_actual = str(session.get('rol', '')).strip().lower()

    if rol_actual != 'superadmin':
        flash('Acceso denegado. Se requieren permisos de Super Admin.', 'danger')
        return redirect(url_for('servicios.admin_clientes'))

    try:
        # Uso de la extensión MySQL configurada en la aplicación
        mysql = current_app.extensions['mysql']
        cur = mysql.connection.cursor()
        
        # Obtención del listado de tablas de la base de datos
        cur.execute("SHOW TABLES")
        tablas = cur.fetchall()
        
        contenido_sql = []
        contenido_sql.append(f"-- Backup DominiosFull - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        contenido_sql.append("SET FOREIGN_KEY_CHECKS=0;\n\n")

        for tabla in tablas:
            nombre_tabla = tabla[0]
            
            # Extracción de la estructura DDL de la tabla
            cur.execute(f"SHOW CREATE TABLE `{nombre_tabla}`")
            esquema = cur.fetchone()[1]
            contenido_sql.append(f"DROP TABLE IF EXISTS `{nombre_tabla}`;\n")
            contenido_sql.append(f"{esquema};\n\n")
            
            # Extracción de los registros de datos
            cur.execute(f"SELECT * FROM `{nombre_tabla}`")
            filas = cur.fetchall()
            
            if filas:
                for fila in filas:
                    valores = []
                    for valor in fila:
                        if valor is None:
                            valores.append("NULL")
                        elif isinstance(valor, (int, float)):
                            valores.append(str(valor))
                        else:
                            # Escape de caracteres especiales en cadenas
                            texto = str(valor).replace("\\", "\\\\").replace("'", "\\'")
                            valores.append(f"'{texto}'")
                    
                    contenido_sql.append(f"INSERT INTO `{nombre_tabla}` VALUES ({', '.join(valores)});\n")
                contenido_sql.append("\n")

        contenido_sql.append("SET FOREIGN_KEY_CHECKS=1;\n")
        cur.close()

        # Conversión del texto SQL a flujo de bytes en memoria
        buffer = BytesIO()
        buffer.write("".join(contenido_sql).encode('utf-8'))
        buffer.seek(0)

        fecha_hora = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        nombre_archivo = f"backup_dominiosfull_{fecha_hora}.sql"

        # Envío del respaldo generado para su descarga
        return send_file(
            buffer,
            mimetype='application/sql',
            as_attachment=True,
            download_name=nombre_archivo
        )

    except Exception as e:
        flash(f'Ocurrió un problema inesperado: {str(e)}', 'danger')
        return redirect(url_for('servicios.admin_clientes'))