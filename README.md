# Sistema de Cotizaciones - Capital & Farmer

Un sistema web inteligente para generar cotizaciones legales automáticas utilizando análisis de IA para determinar complejidad y precios dinámicos.

## Estructura del Proyecto

```
parimango-capital-farmer-exam/
├── README.md
├── app.py
├── templates/
│   ├── login.html
│   ├── index.html
│   ├── base.html  
│   └── cotizaciones.html
├── requirements.txt
└── cotizaciones.db
```

## Instalación

1. **Clone el repositorio**
   ```bash
   git clone https://github.com/AleFine/parimango-capital-farmer-exam.git
   cd parimango-capital-farmer-exam
   ```
3. **(Opcional) Activar un .venv**
   ```bash
   python -m venv .venv .\.venv\Scripts\Activate
   ```

4. **Instale las dependencias**
   ```bash
   pip install -r requirements.txt
   ```

5. **Configure la API Key de OpenAI**
   - La API key ya está configurada para este caso de prueba

6. **Ejecute la aplicación**
   ```bash
   python app.py
   ```

## Uso

1. **Acceso al sistema**
   - Navegue a `http://localhost:5000`
   - Credenciales por defecto: `admin` / `admin123`

2. **Generar cotización**
   - Complete el formulario con datos del cliente
   - Seleccione el tipo de servicio legal
   - Describa detalladamente el caso
   - El sistema analizará automáticamente y generará precio

3. **Gestión de cotizaciones**
   - Visualice todas las cotizaciones en `/cotizaciones`
   - Revise análisis de complejidad y servicios adicionales
   - Exporte propuestas para enviar a clientes

## APIs Utilizadas

- **OpenAI API**: Análisis inteligente de casos legales para determinar complejidad, ajuste de precios y generación de propuestas personalizadas

## Funcionalidades Principales

### Cotizaciones Inteligentes
- Análisis automático de complejidad de casos
- Ajuste dinámico de precios (0%, 25%, 50%)
- Generación de propuestas profesionales personalizadas
- Recomendación de servicios adicionales

### Gestión de Servicios
- **Constitución de empresa**: $1,500 base
- **Defensa laboral**: $2,000 base  
- **Consultoría tributaria**: $800 base

### Sistema de Autenticación
- Login seguro con Flask-Login
- Hash de contraseñas con Werkzeug
- Sesiones protegidas

### Base de Datos Robusta
- SQLite para desarrollo
- Estructura normalizada
- Números de cotización únicos (COT-2025-XXXX)

## Funcionalidades Bonus Implementadas

**Tests Unitarios**: Suite de pruebas automatizadas para validar funcionalidades críticas

**IA Avanzada**: Integración con OpenAI para análisis contextual de casos legales

**Dashboard de Cotizaciones**: Interface completa para gestión y seguimiento

**Seguridad**: Autenticación, validación de datos y manejo seguro de sesiones

**Responsive Design**: Interface adaptable para escritorio y móviles

## Preguntas Técnicas - Respuestas

# 1. ARQUITECTURA MODULAR:
¿Cómo modularizarías el sistema para que las cotizaciones, tickets, expedientes y otros módulos puedan mantenerse independientes pero conectados?

Implementaría una arquitectura basada en microservicios con API Gateway. Cada módulo (cotizaciones, tickets, expedientes) sería un servicio independiente con su propia base de datos.


# 2. ESCALABILIDAD:
¿Qué ajustes aplicarías a la base de datos si el sistema empieza con 10 usuarios pero escala a 100?

Para escalar de 10 a 100 usuarios: (1) Migrar de SQLite a PostgreSQL con connection pooling, (2) Implementar caché Redis para consultas frecuentes, (3) Usar índices en campos de búsqueda, (4) Configurar réplicas de lectura y particionar tablas grandes por fecha.


# 3. INTEGRACIONES:
¿Cómo automatizarías el guardado de documentos legales en Google Drive o Dropbox?

Usaría las APIs oficiales de Google Drive/Dropbox con OAuth2. Implementaría un servicio de almacenamiento abstracto que permita cambiar entre proveedores. Los documentos se subirían de forma asíncrona usando Celery para no bloquear la aplicación principal.


# 4. DEPLOYMENT:
¿Cómo desplegarías esta aplicación para que sea accesible desde computadoras y celulares del estudio, con bajo costo de mantenimiento?

Desplegaría usando Docker + Docker Compose en un VPS económico (DigitalOcean/Linode). Nginx como reverse proxy, certificado SSL con Let's Encrypt, y GitHub Actions para CI/CD. 


# 5. SEGURIDAD:
¿Qué harías para mantener la seguridad básica de los datos (sin entrar en detalles avanzados)?

Implementaría: (1) Autenticación con tokens JWT y refresh tokens, (2) Encriptación de datos sensibles en base de datos, (3) Rate limiting en APIs.

## Tecnologías Utilizadas

- **Backend**: Flask, SQLite, OpenAI SDK
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap CSS
- **Autenticación**: Flask-Login, Werkzeug
- **IA**: OpenAI API
- **Testing**: unittest

