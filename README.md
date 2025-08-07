# 🚀 RDS Dashboard - AWS

Un dashboard moderno y elegante para gestionar y monitorear instancias de Amazon RDS, construido con Django y Tailwind CSS.

## ✨ Características

- **Interfaz Moderna**: Diseño limpio y responsive usando Tailwind CSS
- **Gestión de RDS**: Visualización y gestión de instancias de Amazon RDS
- **Autenticación**: Sistema de usuarios con registro y login
- **Perfiles AWS**: Soporte para múltiples perfiles de AWS
- **Dashboard Interactivo**: Tablas dinámicas con DataTables
- **Notificaciones**: Alertas y notificaciones con SweetAlert2
- **Responsive**: Diseño adaptativo para móviles y tablets

## 🎨 Diseño

### Framework CSS: Tailwind CSS
- **Versión**: 3.4.0
- **Enfoque**: Utility-first CSS framework
- **Ventajas**:
  - Desarrollo más rápido
  - Menor tamaño de archivos CSS
  - Mayor flexibilidad en el diseño
  - Mejor rendimiento

### Componentes Personalizados
- Cards con sombras y efectos hover
- Botones con gradientes y animaciones
- Formularios con iconos integrados
- Alertas y notificaciones estilizadas
- Tablas responsivas

## 🛠️ Tecnologías

### Backend
- **Django 5.2.4**: Framework web de Python
- **boto3**: SDK de AWS para Python
- **SQLite**: Base de datos (desarrollo)

### Frontend
- **Tailwind CSS 3.4.0**: Framework CSS utility-first
- **Font Awesome 6.0.0**: Iconos
- **DataTables**: Tablas interactivas
- **SweetAlert2**: Alertas y notificaciones
- **jQuery**: Manipulación del DOM

### DevOps
- **Docker**: Containerización
- **Docker Compose**: Orquestación de contenedores

## 📦 Instalación

### Prerrequisitos
- Python 3.11+
- Docker y Docker Compose
- AWS CLI configurado

### Desarrollo Local

1. **Clonar el repositorio**
```bash
git clone <repository-url>
cd rds_inventory
```

2. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

3. **Configurar variables de entorno**
```bash
cp .env.example .env
# Editar .env con tus configuraciones
```

4. **Ejecutar migraciones**
```bash
python manage.py migrate
```

5. **Crear superusuario**
```bash
python manage.py createsuperuser
```

6. **Ejecutar el servidor**
```bash
python manage.py runserver
```

### Con Docker

```bash
# Desarrollo
docker-compose up --build

# Producción
docker-compose -f docker-compose.prod.yml up --build
```

## 🎯 Uso

1. **Acceder al dashboard**: `http://localhost:8000`
2. **Registrarse o iniciar sesión**
3. **Seleccionar perfil de AWS**
4. **Explorar instancias de RDS**
5. **Ver detalles de cada instancia**

## 📁 Estructura del Proyecto

```
rds_inventory/
├── core/                    # Aplicación principal
│   ├── models.py           # Modelos de datos
│   ├── views.py            # Vistas de Django
│   ├── auth_views.py       # Vistas de autenticación
│   └── tests.py            # Tests
├── templates/              # Templates HTML
│   └── core/
│       ├── dashboard.html  # Dashboard principal
│       ├── instance_details.html
│       └── auth/           # Templates de autenticación
├── static/                 # Archivos estáticos
│   ├── css/
│   │   └── tailwind.css    # CSS principal con Tailwind
│   ├── js/                 # JavaScript
│   └── img/                # Imágenes
├── rds_dashboard/          # Configuración de Django
├── requirements.txt        # Dependencias de Python
├── docker-compose.yml      # Configuración de Docker
└── README.md              # Documentación
```

## 🎨 Personalización

### Colores y Temas
Los colores principales están definidos en `static/css/tailwind.css`:

```css
:root {
    --primary-color: #3b82f6;    /* Azul principal */
    --success-color: #10b981;    /* Verde */
    --warning-color: #f59e0b;    /* Amarillo */
    --danger-color: #ef4444;     /* Rojo */
    --dark-color: #1e293b;       /* Gris oscuro */
}
```

### Componentes
Los componentes están estilizados con clases de Tailwind y CSS personalizado:

- **Cards**: `.card`, `.card-header`, `.card-body`
- **Botones**: `.btn`, `.btn-primary`, `.btn-success`
- **Formularios**: `.form-control`, `.form-label`
- **Alertas**: `.alert`, `.alert-success`, `.alert-danger`

## 🔧 Configuración de AWS

1. **Instalar AWS CLI**
```bash
pip install awscli
```

2. **Configurar credenciales**
```bash
aws configure
```

3. **Crear perfiles adicionales**
```bash
aws configure --profile mi-perfil
```

## 🚀 Despliegue

### Producción con Docker
```bash
# Construir imagen de producción
docker-compose -f docker-compose.prod.yml up -d --build

# Verificar estado
docker-compose -f docker-compose.prod.yml ps
```

### Variables de Entorno de Producción
```bash
SECRET_KEY=tu-clave-secreta-super-segura
ALLOWED_HOSTS=tu-dominio.com,www.tu-dominio.com
DEBUG=False
```

## 🧪 Testing

```bash
# Ejecutar tests
python manage.py test

# Tests con cobertura
coverage run --source='.' manage.py test
coverage report
```

## 📊 Monitoreo

- **Logs**: Los logs se guardan en `/app/logs/`
- **Health Checks**: Verificar estado con `docker ps`
- **Métricas**: Monitorear recursos con `docker stats`

## 🤝 Contribución

1. Fork el repositorio
2. Crear una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crear un Pull Request

## 📝 Changelog

### v2.0.0 - Migración a Tailwind CSS
- ✅ Migrado de Bootstrap 4 a Tailwind CSS 3.4.0
- ✅ Rediseño completo de la interfaz
- ✅ Mejoras en la responsividad
- ✅ Optimización del rendimiento
- ✅ Nuevos componentes personalizados

### v1.0.0 - Versión inicial
- ✅ Dashboard básico con Bootstrap
- ✅ Gestión de instancias RDS
- ✅ Sistema de autenticación
- ✅ Soporte para perfiles AWS

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## 📞 Soporte

Si tienes problemas o preguntas:

1. Revisar la documentación
2. Buscar en los issues existentes
3. Crear un nuevo issue con detalles del problema

---

**Desarrollado con ❤️ usando Django y Tailwind CSS** 