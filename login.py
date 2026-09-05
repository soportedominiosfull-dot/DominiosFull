import random
import requests
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import check_password_hash
from flask_mail import Message

login_bp = Blueprint('login', __name__)

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

# 1. Autenticación tradicional mediante contraseña + Inicio de 2FA

@login_bp.route('/login', methods=['GET', 'POST'])
def login():
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
    
    from app import mysql, mail
    if request.method == 'POST':

        # VALIDACIÓN RECAPTCHA
        captcha_response = request.form.get('g-recaptcha-response')
        if not validar_recaptcha(captcha_response):
            flash('Por favor, completa la verificación del reCAPTCHA.', 'warning')
            return redirect(url_for('login.login'))

        email = request.form['email']
        password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("SELECT id, nombre, email, contraseña, codigo_2fa, rol, estado FROM usuarios WHERE email = %s", (email,))
        user = cur.fetchone()

        if user:
            if check_password_hash(user[3], password):
                
                rol_limpio = str(user[5]).strip().lower()
                estado_limpio = str(user[6]).strip().lower()
  
                if estado_limpio == 'suspendido':
                    cur.close()
                    session['rol'] = rol_limpio
                    session['estado'] = 'suspendido'
                    if rol_limpio in ['admin', 'superadmin']:
                        return redirect(url_for('admin_suspendido'))
                    else:
                        return redirect(url_for('cuenta_suspendida'))
                    
                codigo = str(random.randint(100000, 999999))
                
                cur.execute("UPDATE usuarios SET codigo_2fa = %s WHERE email = %s", (codigo, email))
                mysql.connection.commit()
                cur.close()

                msg = Message("Tu código de verificación - DominiosFull", sender='soporte.dominiosfull@gmail.com')
                msg.recipients = [email]
                msg.body = f"Hola {user[1]},\n\nTu código de verificación de 2 pasos es: {codigo}\n\nIngrésalo para completar tu inicio de sesión."
                mail.send(msg)

                session['temp_user_id'] = user[0]
                session['temp_rol'] = rol_limpio
                session['temp_estado'] = estado_limpio
                session['temp_email'] = email
                session['temp_nombre'] = user[1]

                return redirect(url_for('login.verificar_2fa'))
            else:
                cur.close()
                flash('Contraseña incorrecta.', 'danger')
                return redirect(url_for('login.login'))
        else:
            cur.close()
            flash('Usuario no registrado.', 'warning')
            return redirect(url_for('login.login'))
    
    return render_template('login.html')


# 2. Confirmación y validación del código 2FA

@login_bp.route('/verificar-2fa', methods=['GET', 'POST'])
def verificar_2fa():
    from app import mysql

    if 'temp_user_id' not in session:
        return redirect(url_for('login.login'))

    if request.method == 'POST':
        codigo_ingresado = request.form.get('codigo', '').strip()

        cur = mysql.connection.cursor()
        cur.execute("SELECT codigo_2fa FROM usuarios WHERE id = %s", (session['temp_user_id'],))
        row = cur.fetchone()

        if row and row[0] == codigo_ingresado:
            cur.execute("UPDATE usuarios SET codigo_2fa = NULL, ultimo_login = NOW() WHERE id = %s", (session['temp_user_id'],))
            mysql.connection.commit()
            cur.close()

            session['user_id'] = session.pop('temp_user_id')
            session['rol'] = session.pop('temp_rol')
            session['estado'] = session.pop('temp_estado', 'activo')
            session['email'] = session.pop('temp_email')
            session['nombre'] = session.pop('temp_nombre')

            if session['rol'] in ['admin', 'superadmin']:
                return redirect(url_for('admin_inicio'))
            else:
                return redirect(url_for('vista_clientes'))
        else:
            cur.close()
            flash('Código de verificación incorrecto.', 'danger')
            return redirect(url_for('login.verificar_2fa'))

    return render_template('verificar_2fa.html')


# 3. Autenticación mediante enlaces mágicos (Magic Links)

@login_bp.route('/magic-link', methods=['POST'])
def magic_link():
    from app import mysql, mail, serializer

    captcha_response = request.form.get('g-recaptcha-response')
    if not validar_recaptcha(captcha_response):
        flash('Por favor, completa la verificación del reCAPTCHA.', 'warning')
        return redirect(url_for('login.login'))

    email = request.form.get('email', '').strip()
    
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, email FROM usuarios WHERE email = %s", (email,))
    user = cur.fetchone()
    cur.close()

    if user:
        token = serializer.dumps(email, salt='magic-link')
        link = url_for('login.magic_link_login', token=token, _external=True)

        msg = Message("Tu Magic Link para SoftNova", sender='soporte.dominiosfull@gmail.com')
        msg.recipients = [email]
        msg.body = f"Haz clic en el siguiente enlace para acceder a tu cuenta. Expira en 15 minutos: {link}"

        mail.send(msg)
        flash("Se ha enviado un enlace mágico a tu correo electrónico.", 'info')
    else:
        flash("El correo electrónico no está registrado.", 'warning')
        
    return redirect(url_for('login.login'))

@login_bp.route('/login-token/<token>')
def magic_link_login(token):
    from app import mysql, serializer
    try:
        email = serializer.loads(token, salt='magic-link', max_age=900)
    except:
        flash("El enlace ha expirado o es inválido.", 'danger')
        return redirect(url_for('login.login'))
    
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM usuarios WHERE email = %s", (email,))
    user = cur.fetchone()

    if user:
        user_id = user[0]
        nombre = user[1]
        rol = str(user[5]).strip().lower()
        estado = str(user[6]).strip().lower()

        if estado == 'suspendido':
            cur.close()
            session['user_id'] = user_id
            session['rol'] = rol
            session['estado'] = 'suspendido'
            session['nombre'] = nombre
            session['email'] = email

            if rol in ['admin', 'superadmin']:
                return redirect(url_for('admin_suspendido'))
            else:
                return redirect(url_for('cuenta_suspendida'))

        cur.execute("UPDATE usuarios SET ultimo_login = NOW() WHERE email = %s", (email,))
        mysql.connection.commit()
        cur.close()

        session['user_id'] = user_id
        session['rol'] = rol
        session['estado'] = estado
        session['email'] = email
        session['nombre'] = nombre

        if rol in ['admin', 'superadmin']:
            return redirect(url_for('admin_inicio'))
        else:
            return redirect(url_for('vista_clientes'))
    else:
        cur.close()
        flash("El usuario no está registrado.", 'warning')
        return redirect(url_for('login.login'))