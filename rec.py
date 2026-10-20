from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, session
from flask_mail import Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature
from werkzeug.security import generate_password_hash

# Inicializa el Blueprint encargado del módulo de recuperación de contraseña.
rec_bp = Blueprint('recuperar', __name__, template_folder='templates')

def obtener_serializer():
    # Genera el encriptador firmado usando la clave secreta global de Flask.
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
#Redirección si ya existe una sesión activa
def verificar_sesion_activa():
    if 'user_id' in session:
        rol = str(session.get('rol', '')).strip().lower()
        estado = str(session.get('estado', '')).strip().lower()

        if estado == 'suspendido':
            if rol in ['admin', 'superadmin']:
                return redirect(url_for('admin_suspendido'))
            return redirect(url_for('cuenta_suspendida'))

        if rol in ['admin', 'superadmin']:
            return redirect(url_for('admin_inicio'))
        return redirect(url_for('vista_clientes'))


@rec_bp.route('/recuperar', methods=['GET', 'POST'])
def recuperar():
   # REDIRECCIÓN SI YA EXISTE UNA SESIÓN ACTIVA
    redireccion = verificar_sesion_activa()
    if redireccion:
        return redireccion 
    
    # Valida el tipo de petición enviada por el usuario.
    if request.method == 'POST':
        # Extrae el correo electrónico ingresado en el formulario.
        email = request.form.get('email')
        
        # Procesa el flujo en caso de recibir un correo electrónico válido.
        if email:
            # 1. Genera un token temporal firmado y encriptado.
            serializer = obtener_serializer()
            token = serializer.dumps(email, salt='recuperacion-password-dominiosfull')

            # 2. Genera el enlace dinámico apuntando a la vista de restablecimiento.
            link_recuperacion = url_for('recuperar.restablecer', token=token, _external=True)

            # 3. Envía el correo electrónico mediante Flask-Mail.
            mail = current_app.extensions.get('mail')
            if mail:
                msg = Message(
                    subject="Restablecimiento de Contraseña - DominiosFull",
                    sender=('DominiosFull Soporte', current_app.config.get('MAIL_USERNAME')),
                    recipients=[email]
                )
                msg.body = (
                    f"Hola,\n\n"
                    f"Has solicitado restablecer tu contraseña en DominiosFull.\n"
                    f"Haz clic en el siguiente enlace para crear una nueva contraseña:\n\n"
                    f"{link_recuperacion}\n\n"
                    f"Este enlace es válido durante 15 minutos.\n"
                    f"Si no realizaste esta solicitud, puedes ignorar este mensaje."
                )
                
                try:
                    mail.send(msg)
                except Exception as e:
                    print(f"Error al enviar el correo de recuperación: {e}")

            # Envía un mensaje global de confirmación a la interfaz del usuario.
            flash("Si el correo está registrado, recibirás un enlace de recuperación pronto.", "success")
            # Redirige automáticamente al usuario hacia la pantalla de inicio de sesión.
            return redirect(url_for('login.login'))
            
        # Maneja excepciones en caso de campos vacíos o inválidos.
        flash("Por favor, introduce un correo electrónico válido.", "warning")
    
    # Renderiza y muestra visualmente la plantilla HTML correspondiente a la vista.
    return render_template('recuperar.html')


@rec_bp.route('/restablecer/<token>', methods=['GET', 'POST'])
def restablecer(token):
    # Permite al usuario definir su nueva contraseña tras hacer clic en el correo.
    serializer = obtener_serializer()
    
    # Valida el token y el tiempo de expiración (900 segundos = 15 minutos).
    try:
        email = serializer.loads(token, salt='recuperacion-password-dominiosfull', max_age=900)
    except SignatureExpired:
        flash("El enlace de recuperación ha caducado. Por favor, solicita uno nuevo.", "warning")
        return redirect(url_for('recuperar.recuperar'))
    except BadTimeSignature:
        flash("El enlace de recuperación es inválido o ha sido alterado.", "danger")
        return redirect(url_for('recuperar.recuperar'))

    # Procesa el formulario con la nueva contraseña.
    if request.method == 'POST':
        nueva_password = request.form.get('password')
        
        if nueva_password:
            # 1. Genera el hash de la nueva contraseña.
            password_encriptada = generate_password_hash(nueva_password)

            # 2. Obtiene MySQL de la aplicación y ejecuta el cursor.
            try:
                mysql = current_app.extensions['mysql']
                cur = mysql.connection.cursor()
                
                sql = "UPDATE usuarios SET contraseña = %s WHERE email = %s"
                cur.execute(sql, (password_encriptada, email))
                mysql.connection.commit()
                cur.close()

                flash("¡Tu contraseña ha sido actualizada exitosamente! Ya puedes iniciar sesión.", "success")
                return redirect(url_for('login.login'))

            except Exception as e:
                print(f"Error actualizando la contraseña en MySQL: {e}")
                flash("Ocurrió un error al actualizar tu contraseña. Por favor, inténtalo de nuevo.", "danger")

    return render_template('restablecer.html', token=token)