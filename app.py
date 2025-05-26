# app.py - Sistema de Cotizaciones Legales con IA
import os
import sqlite3
from datetime import datetime
import json
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from openai import OpenAI
import unittest
from functools import wraps

# Configuración de Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here-change-in-production'
app.config['DATABASE'] = 'cotizaciones.db'

# Configuración de Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Cliente DeepSeek API
client = OpenAI(
    api_key="sk-3a0649ce0aac4caeb676530d9c7f3634",
    base_url="https://api.deepseek.com"
)


# Modelo de Usuario para autenticación
class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username


# Inicialización de la base de datos
def init_db():
    """Inicializa la base de datos con las tablas necesarias"""
    conn = sqlite3.connect(app.config['DATABASE'])
    cursor = conn.cursor()

    # Tabla de cotizaciones
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS cotizaciones
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       numero_cotizacion
                       TEXT
                       UNIQUE
                       NOT
                       NULL,
                       nombre_cliente
                       TEXT
                       NOT
                       NULL,
                       email
                       TEXT
                       NOT
                       NULL,
                       tipo_servicio
                       TEXT
                       NOT
                       NULL,
                       descripcion_caso
                       TEXT
                       NOT
                       NULL,
                       precio_base
                       REAL
                       NOT
                       NULL,
                       precio_final
                       REAL
                       NOT
                       NULL,
                       complejidad
                       TEXT,
                       ajuste_precio
                       INTEGER,
                       servicios_adicionales
                       TEXT,
                       propuesta_texto
                       TEXT,
                       fecha_creacion
                       TIMESTAMP
                       DEFAULT
                       CURRENT_TIMESTAMP
                   )
                   ''')

    # Tabla de usuarios para autenticación
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS usuarios
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       username
                       TEXT
                       UNIQUE
                       NOT
                       NULL,
                       password_hash
                       TEXT
                       NOT
                       NULL
                   )
                   ''')

    # Crear usuario de prueba si no existe
    cursor.execute("SELECT * FROM usuarios WHERE username = ?", ('admin',))
    if not cursor.fetchone():
        password_hash = generate_password_hash('admin123')
        cursor.execute("INSERT INTO usuarios (username, password_hash) VALUES (?, ?)",
                       ('admin', password_hash))

    conn.commit()
    conn.close()


# Initialize DB before the first request
@app.before_request
def initialize_database():
    init_db()


# Funciones auxiliares de base de datos
def get_db_connection():
    """Obtiene una conexión a la base de datos"""
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn


def generar_numero_cotizacion():
    """Genera un número único de cotización"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Obtener el último número
    cursor.execute("SELECT COUNT(*) FROM cotizaciones")
    count = cursor.fetchone()[0]

    numero = f"COT-2025-{str(count + 1).zfill(4)}"
    conn.close()

    return numero


# Servicios y precios
SERVICIOS_PRECIOS = {
    'constitucion_empresa': {'nombre': 'Constitución de empresa', 'precio': 1500},
    'defensa_laboral': {'nombre': 'Defensa laboral', 'precio': 2000},
    'consultoria_tributaria': {'nombre': 'Consultoría tributaria', 'precio': 800}
}


# Función para analizar con IA
def analizar_con_ia(descripcion, tipo_servicio):
    """Analiza el caso con IA y genera recomendaciones"""
    try:
        tipo_servicio_texto = SERVICIOS_PRECIOS[tipo_servicio]['nombre']

        prompt = f"""
        Eres un experto asesor legal. Analiza el siguiente caso:

        Tipo de servicio: {tipo_servicio_texto}
        Descripción del caso: {descripcion}

        Proporciona una respuesta en formato JSON con la siguiente estructura exacta:
        {{
            "complejidad": "Baja" o "Media" o "Alta",
            "ajuste_precio": 0 o 25 o 50 (porcentaje de ajuste),
            "servicios_adicionales": ["servicio1", "servicio2"] (lista de servicios adicionales recomendados, puede estar vacía),
            "propuesta_texto": "Texto de 2-3 párrafos para la propuesta al cliente"
        }}

        Para determinar la complejidad:
        - Baja: casos simples, procedimientos estándar (ajuste 0%)
        - Media: casos con algunas complicaciones o requerimientos especiales (ajuste 25%)
        - Alta: casos complejos, múltiples partes involucradas o situaciones excepcionales (ajuste 50%)

        La propuesta debe ser profesional, mencionar los servicios incluidos, tiempo estimado y condiciones básicas.
        """

        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system",
                 "content": "Eres un asesor legal experto. Siempre respondes en formato JSON válido."},
                {"role": "user", "content": prompt}
            ],
            stream=False
        )

        # Parsear la respuesta JSON
        respuesta_texto = response.choices[0].message.content
        # Limpiar el texto para asegurar que sea JSON válido
        respuesta_texto = respuesta_texto.strip()
        if respuesta_texto.startswith('```json'):
            respuesta_texto = respuesta_texto[7:]
        if respuesta_texto.endswith('```'):
            respuesta_texto = respuesta_texto[:-3]

        resultado = json.loads(respuesta_texto)

        return resultado

    except Exception as e:
        print(f"Error al analizar con IA: {str(e)}")
        # Respuesta por defecto en caso de error
        return {
            'complejidad': 'Media',
            'ajuste_precio': 25,
            'servicios_adicionales': ['Revisión de documentación adicional'],
            'propuesta_texto': f"""Estimado cliente,

Hemos analizado su solicitud de {tipo_servicio_texto} y nos complace presentarle nuestra propuesta. 
El servicio incluye asesoría legal completa, preparación de documentación necesaria y 
acompañamiento durante todo el proceso. El tiempo estimado de ejecución es de 2-4 semanas.

Nuestro equipo de expertos se encargará de gestionar todos los aspectos legales de su caso, 
asegurando el cumplimiento de la normativa vigente. Incluimos revisiones ilimitadas de 
documentación y consultas durante el período de servicio.

Quedamos a su disposición para cualquier consulta adicional."""
        }


# Flask-Login callbacks
@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE id = ?", (user_id,))
    user_data = cursor.fetchone()
    conn.close()

    if user_data:
        return User(user_data['id'], user_data['username'])
    return None


# Rutas de autenticación
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Página de login"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM usuarios WHERE username = ?", (username,))
        user_data = cursor.fetchone()
        conn.close()

        if user_data and check_password_hash(user_data['password_hash'], password):
            user = User(user_data['id'], user_data['username'])
            login_user(user)
            flash('Inicio de sesión exitoso', 'success')
            return redirect(url_for('index'))
        else:
            flash('Usuario o contraseña incorrectos', 'error')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    """Cerrar sesión"""
    logout_user()
    flash('Sesión cerrada exitosamente', 'success')
    return redirect(url_for('login'))


# Rutas principales
@app.route('/')
@login_required
def index():
    """Página principal con el formulario de cotización"""
    return render_template('index.html', servicios=SERVICIOS_PRECIOS)


@app.route('/api/cotizacion', methods=['POST'])
@login_required
def crear_cotizacion():
    """API endpoint para crear una nueva cotización"""
    try:
        # Obtener datos del formulario
        data = request.get_json()
        nombre_cliente = data.get('nombre_cliente')
        email = data.get('email')
        tipo_servicio = data.get('tipo_servicio')
        descripcion_caso = data.get('descripcion_caso')

        # Validaciones
        if not all([nombre_cliente, email, tipo_servicio, descripcion_caso]):
            return jsonify({'error': 'Todos los campos son requeridos'}), 400

        if tipo_servicio not in SERVICIOS_PRECIOS:
            return jsonify({'error': 'Tipo de servicio inválido'}), 400

        # Obtener precio base
        precio_base = SERVICIOS_PRECIOS[tipo_servicio]['precio']

        # Analizar con IA
        analisis_ia = analizar_con_ia(descripcion_caso, tipo_servicio)

        # Calcular precio final
        ajuste_porcentaje = analisis_ia['ajuste_precio']
        precio_final = precio_base * (1 + ajuste_porcentaje / 100)

        # Generar número de cotización
        numero_cotizacion = generar_numero_cotizacion()

        # Guardar en base de datos
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
                       INSERT INTO cotizaciones
                       (numero_cotizacion, nombre_cliente, email, tipo_servicio, descripcion_caso,
                        precio_base, precio_final, complejidad, ajuste_precio, servicios_adicionales,
                        propuesta_texto)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                       ''', (
                           numero_cotizacion,
                           nombre_cliente,
                           email,
                           tipo_servicio,
                           descripcion_caso,
                           precio_base,
                           precio_final,
                           analisis_ia['complejidad'],
                           ajuste_porcentaje,
                           json.dumps(analisis_ia['servicios_adicionales']),
                           analisis_ia['propuesta_texto']
                       ))

        conn.commit()
        cotizacion_id = cursor.lastrowid
        conn.close()

        # Preparar respuesta
        respuesta = {
            'numero_cotizacion': numero_cotizacion,
            'nombre_cliente': nombre_cliente,
            'email': email,
            'tipo_servicio': SERVICIOS_PRECIOS[tipo_servicio]['nombre'],
            'precio_base': precio_base,
            'precio_final': precio_final,
            'complejidad': analisis_ia['complejidad'],
            'ajuste_precio': ajuste_porcentaje,
            'servicios_adicionales': analisis_ia['servicios_adicionales'],
            'propuesta_texto': analisis_ia['propuesta_texto'],
            'fecha_creacion': datetime.now().isoformat()
        }

        return jsonify(respuesta), 201

    except Exception as e:
        print(f"Error al crear cotización: {str(e)}")
        return jsonify({'error': 'Error al procesar la cotización'}), 500


@app.route('/cotizaciones')
@login_required
def listar_cotizaciones():
    """Lista todas las cotizaciones"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
                   SELECT *
                   FROM cotizaciones
                   ORDER BY fecha_creacion DESC
                   ''')
    cotizaciones = cursor.fetchall()
    conn.close()

    # Convertir a lista de diccionarios
    cotizaciones_list = []
    for cot in cotizaciones:
        cot_dict = dict(cot)
        # Parsear servicios adicionales
        if cot_dict['servicios_adicionales']:
            cot_dict['servicios_adicionales'] = json.loads(cot_dict['servicios_adicionales'])
        # Obtener nombre del servicio
        if cot_dict['tipo_servicio'] in SERVICIOS_PRECIOS:
            cot_dict['tipo_servicio_nombre'] = SERVICIOS_PRECIOS[cot_dict['tipo_servicio']]['nombre']
        cotizaciones_list.append(cot_dict)

    return render_template('cotizaciones.html', cotizaciones=cotizaciones_list)


# Tests unitarios
class TestCotizaciones(unittest.TestCase):
    def setUp(self):
        """Configurar ambiente de pruebas"""
        app.config['TESTING'] = True
        app.config['DATABASE'] = ':memory:'
        self.app = app.test_client()
        with app.app_context():
            init_db()

    def test_generar_numero_cotizacion(self):
        """Probar generación de números únicos"""
        with app.app_context():
            num1 = generar_numero_cotizacion()
            self.assertTrue(num1.startswith('COT-2025-'))
            self.assertEqual(len(num1), 13)

    def test_validacion_tipo_servicio(self):
        """Probar validación de tipos de servicio"""
        self.assertIn('constitucion_empresa', SERVICIOS_PRECIOS)
        self.assertEqual(SERVICIOS_PRECIOS['constitucion_empresa']['precio'], 1500)


# PARTE 3 - RESPUESTAS TÉCNICAS SOBRE ARQUITECTURA

"""
1. ARQUITECTURA MODULAR:
Implementaría una arquitectura basada en microservicios con API Gateway. Cada módulo (cotizaciones, 
tickets, expedientes) sería un servicio independiente con su propia base de datos. Usaría eventos 
asíncronos (RabbitMQ/Kafka) para comunicación entre servicios y un bus de eventos compartido.

2. ESCALABILIDAD:
Para escalar de 10 a 100 usuarios: (1) Migrar de SQLite a PostgreSQL con connection pooling, 
(2) Implementar caché Redis para consultas frecuentes, (3) Usar índices en campos de búsqueda,
(4) Configurar réplicas de lectura y particionar tablas grandes por fecha.

3. INTEGRACIONES:
Usaría las APIs oficiales de Google Drive/Dropbox con OAuth2. Implementaría un servicio de 
almacenamiento abstracto que permita cambiar entre proveedores. Los documentos se subirían 
de forma asíncrona usando Celery para no bloquear la aplicación principal.

4. DEPLOYMENT:
Desplegaría usando Docker + Docker Compose en un VPS económico (DigitalOcean/Linode). 
Nginx como reverse proxy, certificado SSL con Let's Encrypt, y GitHub Actions para CI/CD.
Para acceso móvil, diseño responsive con PWA para funcionalidad offline básica.

5. SEGURIDAD:
Implementaría: (1) Autenticación con tokens JWT y refresh tokens, (2) Encriptación de datos 
sensibles en base de datos, (3) Rate limiting en APIs, (4) Logs de auditoría para acciones 
críticas, (5) Backups automáticos diarios con encriptación.
"""

# Inicializar la aplicación
if __name__ == '__main__':
    init_db()

    # Ejecutar tests si se solicita
    if len(os.sys.argv) > 1 and os.sys.argv[1] == 'test':
        unittest.main(argv=[''], exit=False)
    else:
        app.run(debug=True, host='0.0.0.0', port=5000)