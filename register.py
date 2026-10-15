from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash
from flask_mail import Message
import requests
import random

# Inicializa el Blueprint encargado del módulo de registro de nuevos usuarios.
register_bp = Blueprint('register', __name__)

RECAPTCHA_SECRET_KEY = "6LfSvJYtAAAAAOQxEE_7Su2Ne27vi1YFHqNHpKCZ"

def validar_recaptcha(response_token):
    """Consulta directamente a Google si el CAPTCHA fue marcado correctamente."""
    if not response_token:
        return False
    payload = {
        'secret': RECAPTCHA_SECRET_KEY,
        'response': response_token
    }
    try:
        r = requests.post('https://www.google.com/recaptcha/api/siteverify', data=payload)
        return r.json().get('success', False)
    except:
        return False

@register_bp.route('/registro', methods=['GET', 'POST'])
def registro():

    # REDIRECCIÓN SI YA EXISTE UNA SESIÓN ACTIVA O PROCESO 2FA EN CURSO
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

    if 'temp_user_id' in session:
        return redirect(url_for('login.verificar_2fa'))

    from app import mysql, mail
    
    if request.method == 'POST':
        # 1. VALIDACIÓN RECAPTCHA
        captcha_response = request.form.get('g-recaptcha-response')
        if not validar_recaptcha(captcha_response):
            flash('Por favor, completa la verificación del reCAPTCHA.', 'warning')
            return redirect(url_for('register.registro'))
        
        nombre = request.form['nombre']
        email = request.form['email']
        password = request.form['password']
        confirmar = request.form['confirmar']

        # 2. VALIDACIÓN DE CONTRASEÑAS
        if password != confirmar:
            flash('Las contraseñas no coinciden.', 'warning')
            return redirect(url_for('register.registro'))
        
        # 3. VERIFICAR QUE EL CORREO NO EXISTA EN MYSQL
        cur = mysql.connection.cursor()
        cur.execute("SELECT id FROM usuarios WHERE email = %s", (email,))
        existe = cur.fetchone()
        cur.close()

        if existe:
            flash('Este correo electrónico ya se encuentra registrado.', 'warning')
            return redirect(url_for('register.registro'))

        # 4. GENERAR CÓDIGO Y ENVIAR POR CORREO
        codigo = str(random.randint(100000, 999999))
        
        try:
            msg = Message("Tu código de verificación - DominioFull", sender='soporte.dominiosfull@gmail.com')
            msg.recipients = [email]
            msg.body = f"Hola {nombre},\n\nTu código de verificación para completar el registro es: {codigo}\n\nIngrésalo en la plataforma para activar tu cuenta."
            mail.send(msg)
        except Exception as e:
            flash('Error al enviar el correo de verificación. Inténtalo de nuevo.', 'danger')
            return redirect(url_for('register.registro'))

        # 5. GUARDAR DATOS TEMPORALES EN SESIÓN
        session['reg_nombre'] = nombre
        session['reg_email'] = email
        session['reg_password_hash'] = generate_password_hash(password)
        session['reg_codigo_2fa'] = codigo

        return redirect(url_for('register.verificar_2fa_registro'))

    return render_template('registro.html')


@register_bp.route('/2fa_registro', methods=['GET', 'POST'])
def verificar_2fa_registro():
    from app import mysql

    # Si intentan entrar sin llenar el formulario de registro previo
    if 'reg_email' not in session or 'reg_codigo_2fa' not in session:
        return redirect(url_for('register.registro'))

    if request.method == 'POST':
        codigo_ingresado = request.form['codigo']

        # VALIDAR CÓDIGO INGRESADO
        if codigo_ingresado == session.get('reg_codigo_2fa'):
            nombre = session.get('reg_nombre')
            email = session.get('reg_email')
            password_hash = session.get('reg_password_hash')

            try:
                # INSERCIÓN FINAL EN LA BASE DE DATOS
                cur = mysql.connection.cursor()
                cur.execute(
                    "INSERT INTO usuarios (nombre, email, contraseña, estado, rol) VALUES (%s, %s, %s, %s, %s)",
                    (nombre, email, password_hash, 'activo', 'cliente')
                )
                mysql.connection.commit()
                user_id = cur.lastrowid
                cur.close()

                # LIMPIAR VARIABLES TEMPORALES DE REGISTRO
                session.pop('reg_nombre', None)
                session.pop('reg_email', None)
                session.pop('reg_password_hash', None)
                session.pop('reg_codigo_2fa', None)

                # INICIAR SESIÓN DE USUARIO
                session['user_id'] = user_id
                session['rol'] = 'cliente'
                session['nombre'] = nombre

                flash("¡Cuenta creada y verificada con éxito! Bienvenido.", 'success')
                return redirect(url_for('vista_clientes'))

            except Exception as e:
                flash(f"Error al guardar la cuenta: {str(e)}", 'danger')
                return redirect(url_for('register.registro'))
        else:
            flash('El código de verificación es incorrecto.', 'danger')
            return redirect(url_for('register.verificar_2fa_registro'))

    # CORREGIDO: Renderiza la vista 2fa_registro.html para peticiones GET
    return render_template('2fa_registro.html')