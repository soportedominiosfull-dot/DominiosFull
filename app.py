from flask import Flask, render_template, session, redirect, url_for, jsonify, request, flash
from flask_mysqldb import MySQL
from itsdangerous import URLSafeTimedSerializer
from flask_mail import Mail, Message
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

app = Flask(__name__)

app.secret_key = 'Proyectosena2026C-M-C'

# Configuración de la base de datos (Alwaysdata)
app.config['MYSQL_HOST'] = 'mysql-dominiosfull.alwaysdata.net'
app.config['MYSQL_USER'] = 'dominiosfull'
app.config['MYSQL_PASSWORD'] = 'ProyectoSENA-server1427'
app.config['MYSQL_DB'] = 'dominiosfull_bd'
app.config['MYSQL_DATABASE_CHARSET'] = 'utf8mb4'

mysql = MySQL(app)

# Configuración de Flask-Mail para el envío de enlaces mágicos
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'soporte.dominiosfull@gmail.com'
app.config['MAIL_PASSWORD'] = 'yiqkbyzxjwahcwng'  # Código generado por Google para aplicaciones externas
app.config['MAIL_DEFAULT_SENDER'] = 'soporte.dominiosfull@gmail.com'
mail = Mail(app)

serializer = URLSafeTimedSerializer(app.secret_key)

# Correo autorizado para otorgar permisos de cambio de rol
EMAIL_AUTORIZADO = 'samuel_chaconst@gfc.edu.co'

# Evita errores de contexto al utilizar las instancias dentro de otros módulos
@app.before_request
def antes_de_peticion():
    app.extensions['mysql'] = mysql
    app.extensions['mail'] = mail
    
    try:
        cur = mysql.connection.cursor()
        cur.execute("SET NAMES utf8mb4;")
        cur.execute("SET CHARACTER SET utf8mb4;")
        cur.execute("SET character_set_connection=utf8mb4;")
        cur.close()
    except Exception:
        pass

@app.context_processor
def inject_user_nombre():
    nombre = session.get('nombre')
    email = session.get('email')
    rol = session.get('rol')
    return {'nombre': nombre, 'email': email, 'rol': rol}

def obtener_productos_destacados():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT p.categoria, p.nombre, COUNT(c.id) AS ventas
        FROM productos p
        INNER JOIN compras c ON c.producto = p.nombre
        GROUP BY p.categoria, p.nombre
        ORDER BY p.categoria ASC, ventas DESC, p.nombre ASC
    """)
    ventas = cur.fetchall()
    cur.close()

    destacados = {'dominio': [], 'hosting': [], 'vps': []}
    limites = {'dominio': 3, 'hosting': 2, 'vps': 1}
    for categoria, nombre, _ in ventas:
        if len(destacados[categoria]) < limites[categoria]:
            destacados[categoria].append(nombre)
    return destacados

# Módulos importados
from login import login_bp
from register import register_bp
from carrito import carrito_bp
from servicios import servicios_bp
from rec import rec_bp

app.register_blueprint(login_bp)
app.register_blueprint(register_bp)
app.register_blueprint(carrito_bp)
app.register_blueprint(servicios_bp)
app.register_blueprint(rec_bp)

# --- RUTAS PRINCIPALES ---

@app.route('/')
def index():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT r.comentario, r.estrellas, u.nombre, r.fecha
        FROM resenas r
        JOIN usuarios u ON r.user_id = u.id
        WHERE r.estrellas >= 4
        ORDER BY r.fecha DESC LIMIT 10
    """)
    resenas_destacadas = cur.fetchall()

    cur.execute("""
        SELECT r.comentario, r.estrellas, u.nombre, r.fecha
        FROM resenas r
        JOIN usuarios u ON r.user_id = u.id
        ORDER BY r.fecha DESC
    """)
    todas_resenas = cur.fetchall()
    cur.close()

    nombre = session.get('nombre')
    rol = session.get('rol')

    return render_template('index.html', nombre=nombre, rol=rol, resenas_destacadas=resenas_destacadas, todas_resenas=todas_resenas)

@app.route('/dominios')
def dominios():
    cur = mysql.connection.cursor()
    query = """
        SELECT 
            id_productos, 
            nombre, 
            precio, 
            CASE 
                WHEN oferta_fin IS NOT NULL AND oferta_fin > NOW() THEN precio_oferta 
                ELSE NULL 
            END AS oferta_activa
        FROM productos 
        WHERE categoria = 'dominio'
    """
    cur.execute(query)
    dominios = cur.fetchall()
    cur.close()
    productos_destacados = obtener_productos_destacados()

    return render_template('dominios.html', dominios=dominios, productos_destacados=productos_destacados)

@app.route('/hosting')
def hosting():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT id_productos, nombre, categoria, precio, precio_oferta, oferta_fin 
        FROM productos 
        WHERE categoria = 'hosting'
        ORDER BY id_productos ASC
    """)
    lista_hostings = cur.fetchall()
    cur.close()
    productos_destacados = obtener_productos_destacados()
    return render_template('hosting.html', hostings=lista_hostings, productos_destacados=productos_destacados)

@app.route('/vps')
def vps():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT id_productos, nombre, categoria, precio, precio_oferta, oferta_fin 
        FROM productos 
        WHERE categoria = 'vps'
        ORDER BY id_productos ASC
    """)
    lista_vps = cur.fetchall()
    cur.close()
    productos_destacados = obtener_productos_destacados()
    return render_template('vps.html', vps_planes=lista_vps, productos_destacados=productos_destacados)

@app.route('/soporte')
def soporte():
    return render_template('soporte.html')

@app.route('/terminos')
def terminos():
    return render_template('terminos.html')

@app.route('/privacidad')
def privacidad():
    return render_template('privacidad.html')

# --- CONTROL DE ACCESOS Y PANELES ---

@app.route('/admin-inicio')
def admin_inicio():
    if 'rol' in session and session['rol'] in ['admin', 'superadmin']:
        cur = mysql.connection.cursor()

        # VERIFICACIÓN DE ESTADO EN BASE DE DATOS
        if 'user_id' in session:
            cur.execute("SELECT estado FROM usuarios WHERE id = %s", (session['user_id'],))
            usr = cur.fetchone()
            if usr and str(usr[0]).strip().lower() == 'suspendido':
                session['estado'] = 'suspendido'
                cur.close()
                return redirect(url_for('admin_suspendido'))
    
        cur.execute("SELECT COALESCE(SUM(precio), 0) FROM compras")
        ventas_total = cur.fetchone()[0] or 0
        cur.execute("SELECT COUNT(*) FROM usuarios WHERE rol = 'cliente'")
        clientes_total = cur.fetchone()[0] or 0
        cur.execute("SELECT COUNT(*) FROM compras")
        servicios_total = cur.fetchone()[0] or 0
        cur.execute(
            "SELECT c.id, u.nombre, c.producto, c.precio, c.fecha "
            "FROM compras c "
            "LEFT JOIN usuarios u ON c.user_id = u.id "
            "ORDER BY c.fecha DESC LIMIT 5"
        )
        ultimas_compras = cur.fetchall()
        cur.close()

        return render_template(
            'admin-inicio.html',
            ventas_total=ventas_total,
            clientes_total=clientes_total,
            servicios_total=servicios_total,
            ultimas_compras=ultimas_compras
        )
    else:
        return redirect(url_for('login.login'))

@app.route('/vista-clientes')
def vista_clientes():
    if 'rol' in session and session['rol'] == 'cliente':
        nombre_usuario = session.get('nombre')
        email_usuario = session.get('email')
        facturas = []
        dominios_usuario = []
        hosting_usuario = []
        vps_usuario = []

        if 'user_id' in session:
            cur = mysql.connection.cursor()
            cur.execute("SELECT nombre, email, estado FROM usuarios WHERE id = %s", (session['user_id'],))
            usuario = cur.fetchone()
            
            if usuario:
                if usuario[2] == 'suspendido':
                    cur.close()
                    return redirect(url_for('cuenta_suspendida'))
                
                nombre_usuario = usuario[0]
                email_usuario = usuario[1]
                session['nombre'] = nombre_usuario
                session['email'] = email_usuario
                
            cur.execute("""
                SELECT id, fecha_emision, concepto, total, estado 
                FROM facturas 
                WHERE user_id = %s 
                ORDER BY fecha_emision DESC
            """, (session['user_id'],))
            facturas = cur.fetchall()

            cur.execute("""
                SELECT producto, DATE_FORMAT(DATE_ADD(fecha, INTERVAL 1 YEAR), '%%d/%%m/%%Y') AS vencimiento
                FROM compras 
                WHERE user_id = %s AND producto LIKE '.%%'
                ORDER BY fecha DESC
            """, (session['user_id'],))
            raw_dominios = cur.fetchall()
            dominios_usuario = [
                {'nombre': item[0], 'estado': 'Activo', 'fecha_vencimiento': item[1]}
                for item in raw_dominios
            ]

            cur.execute("""
                SELECT producto 
                FROM compras 
                WHERE user_id = %s AND (producto LIKE '%%Gigas%%' OR producto LIKE '%%PYMES%%')
                ORDER BY fecha DESC
            """, (session['user_id'],))
            raw_hosting = cur.fetchall()
            hosting_usuario = [{'nombre_plan': item[0], 'estado': 'Activo'} for item in raw_hosting]

            cur.execute("""
                SELECT producto 
                FROM compras 
                WHERE user_id = %s AND producto LIKE '%%VPS%%'
                ORDER BY fecha DESC
            """, (session['user_id'],))
            raw_vps = cur.fetchall()
            vps_usuario = [{'nombre_plan': item[0], 'ip': 'En asignación', 'estado': 'Activo'} for item in raw_vps]
            
            cur.close()

        return render_template(
            'vista-clientes.html', 
            nombre=nombre_usuario, 
            email=email_usuario, 
            facturas=facturas,
            dominios_usuario=dominios_usuario,
            hosting_usuario=hosting_usuario,
            vps_usuario=vps_usuario
        )
    else:
        return redirect(url_for('login.login'))

@app.route('/cuenta-suspendida')
def cuenta_suspendida():
    return render_template('baneado.html')

@app.route('/admin-suspendido')
def admin_suspendido():
    # Imprime en la consola de Python los valores exactos para verificar
    print("ROL EN SESION:", session.get('rol'))
    print("ESTADO EN SESION:", session.get('estado'))

    # Si session['estado'] viene en mayúsculas o con espacios, strip/lower lo soluciona
    estado = str(session.get('estado')).strip().lower()

    if 'rol' in session and estado == 'suspendido':
        return render_template('admin-suspendido.html')
    
    return redirect(url_for('login.login'))

# --- PERFIL Y CONTRASEÑA ---

@app.route('/actualizar-perfil', methods=['POST'])
def actualizar_perfil():
    if 'rol' not in session or session['rol'] not in ['cliente', 'admin', 'superadmin']:
        return redirect(url_for('login.login'))

    nombre = request.form.get('nombre', '').strip()

    if not nombre:
        flash('El nombre es obligatorio.', 'warning')
        return redirect(url_for('admin_inicio') if session.get('rol') in ['admin', 'superadmin'] else url_for('vista_clientes'))

    if 'user_id' not in session:
        flash('Debes iniciar sesión para actualizar tu perfil.', 'warning')
        return redirect(url_for('login.login'))

    try:
        cur = mysql.connection.cursor()
        cur.execute("UPDATE usuarios SET nombre=%s WHERE id=%s", (nombre, session['user_id']))
        mysql.connection.commit()
        session['nombre'] = nombre
        flash('Nombre actualizado con éxito.', 'success')
    except Exception as e:
        flash('Error al actualizar el nombre: ' + str(e), 'danger')
    finally:
        cur.close()

    return redirect(url_for('admin_inicio') if session.get('rol') in ['admin', 'superadmin'] else url_for('vista_clientes'))

@app.route('/cambiar-contrasena', methods=['POST'])
def cambiar_contrasena():
    if 'rol' not in session or session['rol'] not in ['cliente', 'admin', 'superadmin']:
        return redirect(url_for('login.login'))

    destino = 'admin_inicio' if session.get('rol') in ['admin', 'superadmin'] else 'vista_clientes'

    actual = request.form.get('contraseña-actual', '')
    nueva = request.form.get('nueva-contraseña', '')
    confirmar = request.form.get('confirmar-contraseña', '')

    if not actual or not nueva or not confirmar:
        flash('Todos los campos de contraseña son obligatorios.', 'warning')
        return redirect(url_for(destino))

    if nueva != confirmar:
        flash('La nueva contraseña no coincide con la confirmación.', 'danger')
        return redirect(url_for(destino))

    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT contraseña FROM usuarios WHERE id = %s", (session['user_id'],))
        row = cur.fetchone()

        if not row or not check_password_hash(row[0], actual):
            flash('Contraseña actual incorrecta.', 'danger')
            return redirect(url_for(destino))

        nueva_hash = generate_password_hash(nueva)
        cur.execute("UPDATE usuarios SET contraseña = %s WHERE id = %s", (nueva_hash, session['user_id']))
        mysql.connection.commit()
        flash('Contraseña actualizada con éxito.', 'success')
    except Exception as e:
        flash('Error al cambiar la contraseña: ' + str(e), 'danger')
    finally:
        cur.close()

    return redirect(url_for(destino))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# --- SISTEMA SEGURO DE CAMBIO DE ROL CON AUTORIZACIÓN POR CORREO ---

@app.route('/solicitar-cambio-rol', methods=['POST'])
def solicitar_cambio_rol():
    if 'rol' not in session or session['rol'] not in ['admin', 'superadmin']:
        flash('Acceso denegado. Se requieren permisos de administrador.', 'danger')
        return redirect(url_for('index'))

    usuario_id = request.form.get('usuario_id')
    nuevo_rol = request.form.get('nuevo_rol')

    if not usuario_id or not nuevo_rol:
        flash('Datos insuficientes para procesar la solicitud.', 'warning')
        return redirect(request.referrer)

    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT nombre, email, rol FROM usuarios WHERE id = %s", (usuario_id,))
        usr = cur.fetchone()
        cur.close()

        if not usr:
            flash('El usuario especificado no existe.', 'danger')
            return redirect(request.referrer)

        nombre_usr, email_usr, rol_actual = usr[0], usr[1], usr[2]

        if rol_actual == nuevo_rol:
            flash('El usuario ya cuenta con ese rol asignado.', 'info')
            return redirect(request.referrer)

        # Generar token encriptado que expira en 15 minutos (900 segundos)
        token = serializer.dumps({'usuario_id': usuario_id, 'nuevo_rol': nuevo_rol}, salt='cambio-rol-seguro')
        link_confirmacion = url_for('confirmar_cambio_rol', token=token, _external=True)

        # Crear y enviar mensaje por correo a Samuel Chacón
        msg = Message(
            subject="SOLICITUD CRÍTICA: Autorización de Cambio de Rol",
            recipients=[EMAIL_AUTORIZADO],
            body=f"Hola Samuel,\n\n"
                 f"Se ha solicitado un cambio de rol en el sistema:\n\n"
                 f"• Usuario: {nombre_usr} ({email_usr})\n"
                 f"• Rol actual: {rol_actual}\n"
                 f"• Rol solicitado: {nuevo_rol}\n\n"
                 f"Para AUTORIZAR este cambio, haz clic en el siguiente enlace de un solo uso:\n"
                 f"{link_confirmacion}\n\n"
                 f"Este enlace expira automáticamente en 15 minutos.\n"
                 f"Si tú no solicitaste esto, ignora este correo."
        )
        mail.send(msg)

        flash(f'Solicitud enviada con éxito. Se envió un correo a {EMAIL_AUTORIZADO} para la aprobación.', 'info')
    except Exception as e:
        flash('Error al enviar la solicitud de autorización: ' + str(e), 'danger')

    return redirect(request.referrer)


@app.route('/confirmar-cambio-rol/<token>')
def confirmar_cambio_rol(token):
    try:
        # Desencriptar token con límite de tiempo de 15 minutos
        datos = serializer.loads(token, salt='cambio-rol-seguro', max_age=900)
        usuario_id = datos['usuario_id']
        nuevo_rol = datos['nuevo_rol']

        cur = mysql.connection.cursor()
        cur.execute("UPDATE usuarios SET rol = %s WHERE id = %s", (nuevo_rol, usuario_id))
        mysql.connection.commit()
        cur.close()

        flash(f'¡AUTORIZADO! El rol del usuario ID {usuario_id} ha sido cambiado exitosamente a "{nuevo_rol}".', 'success')
    except Exception as e:
        flash('El enlace de autorización es inválido, ya fue usado o ha expirado.', 'danger')

    # Redirige a admin-inicio o a la vista desde donde fue invocado
    return redirect(url_for('admin_inicio'))

# --- MODERACIÓN DE RESEÑAS ---

PALABRAS_PROHIBIDAS = ['hijueputa', 'gonorrea', 'malparido', 'mierda', 'pendejo', 'puta', 'estafa', 'robos', 'ladrones', 'estafadores', 'robo', 'ladron', 'estafador', 'maldito', 'idiota', 'imbecil', 'tonto', 'inútil', 'basura', 'desgraciado', 'malnacido', 'cabrón', 'culero', 'verga', 'coño', 'joder', 'puta madre', 'mierda de servicio', 'estafa total', 'robo descarado', 'ladrones de mierda', 'estafadores sinvergüenzas', 'maldito estafador', 'idiota inútil', 'imbécil tonto', 'inútil basurero', 'desgraciado malnacido', 'cabrón culero', 'verga de mierda', 'coño de joder', 'puta madre estafadora', 'mierda de servicio estafador', 'estafa total ladrona', 'robo descarado estafador', 'ladrones de mierda estafadores', 'estafadores sinvergüenzas malnacidos', 'maldito estafador idiota', 'idiota inútil imbécil', 'imbécil tonto inútil', 'inútil basurero desgraciado', 'desgraciado malnacido cabrón', 'cabrón culero verga', 'verga de mierda coño', 'coño de joder puta madre', 'puta madre estafadora mierda', 'mierda de servicio estafador estafa', 'estafa total ladrona robo', 'robo descarado estafador ladrones', 'ladrones de mierda estafadores sinvergüenzas', 'estafadores sinvergüenzas malnacidos maldito', 'maldito estafador idiota inútil', 'idiota inútil imbécil tonto', 'imbécil tonto inútil basurero', 'inútil basurero desgraciado malnacido', 'desgraciado malnacido cabrón culero', 'cabrón culero verga de mierda', 'verga de mierda coño de joder', 'coño de joder puta madre estafadora', 'puta madre estafadora mierda de servicio', 'mierda de servicio estafador estafa total', 'estafa total ladrona robo descarado', 'robo descarado estafador ladrones de mierda', 'ladrones de mierda estafadores sinvergüenzas malnacidos', 'estafadores sinvergüenzas malnacidos maldito estafador', 'maldito estafador idiota inútil imbécil', 'idiota inútil imbécil tonto inútil basurero', 'imbécil tonto inútil basurero desgraciado', 'inútil basurero desgraciado malnacido cabrón', 'desgraciado malnacido cabrón culero verga', 'cabrón culero verga de mierda coño', 'verga de mierda coño de joder puta madre', 'coño de joder puta madre estafadora mierda de servicio', 'puta madre estafadora mierda de servicio estafador estafa total', 'mierda de servicio estafador estafa total ladrona robo descarado', 'estafa total ladrona robo descarado estafador ladrones de mierda', 'robo descarado estafador ladrones de mierda estafadores sinvergüenzas malnacidos', 'nigga', 'zorra', 'nigger', 'niggers', 'put4']

def contiene_palabras_invalidas(texto):
    texto_lower = texto.lower()
    for palabra in PALABRAS_PROHIBIDAS:
        if palabra in texto_lower:
            return True
    return False

@app.route('/guardar-resena', methods=['POST'])
def guardar_resena():
    if 'user_id' not in session:
        return redirect(url_for('login.login'))

    user_id = session['user_id']
    comentario = request.form.get('comentario', '').strip()
    estrellas = request.form.get('estrellas')

    if not comentario or not estrellas:
        flash('Por favor escribe un comentario y selecciona una puntuación.', 'warning')
        return redirect(request.referrer)

    if contiene_palabras_invalidas(comentario):
        flash('Tu comentario contiene palabras no apropiadas. Por favor modéralo.', 'danger')
        return redirect(request.referrer)

    cursor = mysql.connection.cursor()
    query = """
        INSERT INTO resenas (user_id, comentario, estrellas)
        VALUES (%s, %s, %s)
    """
    cursor.execute(query, (user_id, comentario, int(estrellas)))
    mysql.connection.commit()
    cursor.close()

    flash('¡Gracias por tu opinión! Tu comentario ha sido publicado.', 'success')
    return redirect(request.referrer)

@app.route('/admin-opiniones')
def admin_opiniones():
    if 'rol' in session and session['rol'] in ['admin', 'superadmin']:
        cur = mysql.connection.cursor()
        cur.execute("""
            SELECT r.id_resena, r.comentario, r.estrellas, r.fecha, u.nombre, u.email
            FROM resenas r
            JOIN usuarios u ON r.user_id = u.id
            ORDER BY r.fecha DESC
        """)
        lista_resenas = cur.fetchall()
        cur.close()
        return render_template('admin-opiniones.html', resenas=lista_resenas)
    else:
        return redirect(url_for('login.login'))

@app.route('/eliminar-resena/<int:id_resena>', methods=['POST'])
def eliminar_resena(id_resena):
    if 'rol' in session and session['rol'] in ['admin', 'superadmin']:
        try:
            cur = mysql.connection.cursor()
            
            # 1. Eliminar la reseña seleccionada
            cur.execute("DELETE FROM resenas WHERE id_resena = %s", (id_resena,))
            
            # 2. Reordenar los IDs para cerrar huecos (1, 2, 3...)
            cur.execute("SET @count = 0;")
            cur.execute("UPDATE resenas SET id_resena = (@count := @count + 1);")
            
            # 3. Reiniciar el AUTO_INCREMENT para que el siguiente sea consecutivo
            cur.execute("ALTER TABLE resenas AUTO_INCREMENT = 1;")
            
            mysql.connection.commit()
            cur.close()
            flash('La reseña ha sido eliminada con éxito.', 'success')
        except Exception as e:
            flash('Error al eliminar la reseña: ' + str(e), 'danger')
        
        return redirect(url_for('admin_opiniones'))
    else:
        return redirect(url_for('login.login'))


# VERIFICACIÓN DE ESTADO EN TIEMPO REAL PARA USUARIOS LOGUEADOS

# Excepciones: Rutas que NO deben bloquearse para evitar bucles infinitos de redirección
RUTAS_EXCEPTUADAS = [
    'login.login', 
    'login.logout', 
    'logout', 
    'cuenta_suspendida', 
    'admin_suspendido', 
    'static'
]

@app.before_request
def verificar_estado_usuario_activo():
    # Solo evalúa si hay un usuario con sesión iniciada
    if 'user_id' in session:
        # Permite acceso a recursos estáticos o vistas de suspensión/logout
        if request.endpoint in RUTAS_EXCEPTUADAS or (request.endpoint and request.endpoint.startswith('static')):
            return

        try:
            cur = mysql.connection.cursor()
            cur.execute("SELECT estado, rol FROM usuarios WHERE id = %s", (session['user_id'],))
            usr = cur.fetchone()
            cur.close()

            if usr:
                estado_actual = str(usr[0]).strip().lower()
                rol_actual = str(usr[1]).strip().lower()

                # SI EL USUARIO FUE SUSPENDIDO MIENTRAS NAVEGABA:
                if estado_actual == 'suspendido':
                    # Actualizamos la sesión para reflejar la suspensión
                    session['estado'] = 'suspendido'
                    session['rol'] = rol_actual

                    # Si intenta navegar en una vista admin, lo manda a admin_suspendido
                    if rol_actual in ['admin', 'superadmin']:
                        return redirect(url_for('admin_suspendido'))
                    # Si es cliente, lo manda a cuenta_suspendida
                    else:
                        return redirect(url_for('cuenta_suspendida'))
            else:
                # Si el usuario ya no existe en la BD, limpia la sesión
                session.clear()
                return redirect(url_for('login.login'))

        except Exception as e:
            # En caso de un fallo temporal en la BD, deja continuar para no romper la app
            pass

#ELIMINAR CACHE DE NAVEGADOR PARA EVITAR QUE USUARIOS SUSPENDIDOS ACCEDAN A VISTAS ANTERIORES
@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=1000, debug=True)


# --- NOTAS DE EJECUCIÓN ---
# 1. Abrir la terminal en la carpeta raíz del proyecto.
# 2. Activar el entorno virtual: .\venv\Scripts\activate
# 3. Ejecutar la aplicación: python app.py

# --- NOTAS DE MANTENIMIENTO DEL ENTORNO VIRTUAL (VENV) ---
# Si el proyecto es cambiado de ubicación o presenta errores de dependencias:
# 1. Eliminar la carpeta venv: Remove-Item -Recurse -Force venv (en PowerShell)
# 2. Generar un nuevo entorno virtual: python -m venv venv
# 3. Instalar dependencias necesarias: pip install flask flask_mysqldb flask-mail itsdangerous reportlab datetime requests
# 4. Verificar la contraseña local de MySQL si difiere del valor por defecto '12345'

#CARGAR A GITHUB
# 1. Verificar los archivos modificados
#git status

# 2. Agregar todos los cambios al área de preparación
#git add .

# 3. Confirmar los cambios con un mensaje descriptivo
#git commit -m "MENSAJE DE LOS CAMBIOS REALIZADOS"

# 4. Subir los cambios al repositorio remoto (reemplaza 'main' por 'master' si tu rama usa ese nombre)
#git push origin main