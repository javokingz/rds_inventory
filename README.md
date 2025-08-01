# RDS Dashboard

Un dashboard web para monitorear y gestionar instancias de Amazon RDS usando Django y AdminLTE.

## Características

- 🔐 Conexión a múltiples perfiles de AWS
- 📊 Visualización de instancias RDS con AdminLTE
- 🔄 Actualización en tiempo real de datos
- 📋 Tabla interactiva con DataTables
- 📱 Diseño responsive
- 🔍 Vista detallada de cada instancia
- 🌐 Interfaz en español

## Requisitos Previos

1. **Python 3.8+**
2. **AWS CLI configurado** con perfiles locales
3. **Credenciales de AWS** configuradas

## Instalación

1. **Clonar el repositorio:**
   ```bash
   git clone <url-del-repositorio>
   cd rds_dashboard
   ```

2. **Crear entorno virtual:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # En Linux/Mac
   # o
   venv\Scripts\activate  # En Windows
   ```

3. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar AWS CLI (si no está configurado):**
   ```bash
   aws configure
   # O para múltiples perfiles:
   aws configure --profile nombre-perfil
   ```

## Configuración de AWS

### Configurar perfiles de AWS

1. **Crear archivo de configuración:**
   ```bash
   mkdir -p ~/.aws
   ```

2. **Configurar credenciales (~/.aws/credentials):**
   ```ini
   [default]
   aws_access_key_id = TU_ACCESS_KEY
   aws_secret_access_key = TU_SECRET_KEY

   [perfil-desarrollo]
   aws_access_key_id = TU_ACCESS_KEY_DESARROLLO
   aws_secret_access_key = TU_SECRET_KEY_DESARROLLO

   [perfil-produccion]
   aws_access_key_id = TU_ACCESS_KEY_PRODUCCION
   aws_secret_access_key = TU_SECRET_KEY_PRODUCCION
   ```

3. **Configurar regiones (~/.aws/config):**
   ```ini
   [default]
   region = us-east-1
   output = json

   [profile perfil-desarrollo]
   region = us-west-2
   output = json

   [profile perfil-produccion]
   region = eu-west-1
   output = json
   ```

## Uso

1. **Ejecutar el servidor de desarrollo:**
   ```bash
   python manage.py runserver
   ```

2. **Abrir en el navegador:**
   ```
   http://localhost:8000
   ```

3. **Seleccionar un perfil de AWS** del menú desplegable

4. **Ver las instancias de RDS** en la tabla

## Funcionalidades

### Dashboard Principal
- Selección de perfil de AWS
- Lista de instancias RDS
- Estado de cada instancia
- Información básica (motor, clase, endpoint)

### Vista Detallada
- Información completa de cada instancia
- Configuración de red
- Almacenamiento
- Configuración de seguridad
- Grupos de seguridad

### Características de la Tabla
- Ordenamiento por columnas
- Búsqueda
- Paginación
- Responsive design

## Estructura del Proyecto

```
rds_dashboard/
├── core/
│   ├── views.py          # Vistas principales
│   ├── models.py         # Modelos (si se necesitan)
│   └── ...
├── templates/
│   └── core/
│       └── dashboard.html # Template principal
├── static/               # Archivos estáticos
├── rds_dashboard/
│   ├── settings.py       # Configuración de Django
│   └── urls.py          # URLs del proyecto
└── requirements.txt     # Dependencias
```

## API Endpoints

- `GET /` - Dashboard principal
- `GET /api/rds-data/?profile=<nombre-perfil>` - Datos de RDS en formato JSON

## Seguridad

- Las credenciales de AWS se manejan localmente
- No se almacenan credenciales en la base de datos
- Usar perfiles de AWS para diferentes entornos

## Troubleshooting

### Error: "No se encontraron credenciales de AWS"
- Verificar que AWS CLI esté configurado
- Comprobar que el perfil seleccionado existe
- Verificar permisos de las credenciales

### Error: "Perfil no encontrado"
- Verificar que el perfil esté en `~/.aws/config`
- Comprobar la sintaxis del archivo de configuración

### Error: "No se encontraron instancias de RDS"
- Verificar que el perfil tenga permisos para RDS
- Comprobar que existan instancias en la región configurada

## Contribuir

1. Fork el proyecto
2. Crear una rama para tu feature
3. Commit tus cambios
4. Push a la rama
5. Abrir un Pull Request

## Licencia

Este proyecto está bajo la Licencia MIT. 