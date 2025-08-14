# 🐳 RDS Dashboard - Docker

Este documento explica cómo containerizar y desplegar el RDS Dashboard usando Docker.

## 📋 Prerrequisitos

- Docker
- Docker Compose
- Configuración de AWS CLI en el host

## 🚀 Despliegue Rápido

### Desarrollo

```bash
# Construir y ejecutar en modo desarrollo
docker-compose up --build

# Ejecutar en segundo plano
docker-compose up -d --build
```

### Producción

```bash
# Construir y ejecutar en modo producción
docker-compose -f docker-compose.prod.yml up --build

# Ejecutar en segundo plano
docker-compose -f docker-compose.prod.yml up -d --build
```

## 🔧 Configuración

### Variables de Entorno

Crea un archivo `.env` en la raíz del proyecto:

```bash
# Configuración de Django
SECRET_KEY=tu-clave-secreta-aqui
ALLOWED_HOSTS=localhost,127.0.0.1,tu-dominio.com

# Configuración de AWS
AWS_PROFILE=default

# Crear superusuario automáticamente (solo desarrollo)
CREATE_SUPERUSER=true
```

### Configuración de AWS

Asegúrate de tener configurado AWS CLI en tu host:

```bash
# Configurar AWS CLI
aws configure

# O crear perfiles específicos
aws configure --profile mi-perfil
```

## 📁 Estructura de Archivos Docker

```
rds_inventory/
├── Dockerfile                 # Dockerfile para desarrollo
├── Dockerfile.prod           # Dockerfile optimizado para producción
├── docker-compose.yml        # Compose para desarrollo
├── docker-compose.prod.yml   # Compose para producción
├── docker-entrypoint.sh      # Script de inicialización
├── .dockerignore             # Archivos a ignorar en el build
└── rds_dashboard/
    └── settings_prod.py      # Configuración de Django para producción
```

## 🛠️ Comandos Útiles

### Desarrollo

```bash
# Ver logs
docker-compose logs -f

# Ejecutar comandos dentro del contenedor
docker-compose exec rds-dashboard python manage.py shell

# Crear superusuario
docker-compose exec rds-dashboard python manage.py createsuperuser

# Ejecutar migraciones
docker-compose exec rds-dashboard python manage.py migrate

# Recolectar archivos estáticos
docker-compose exec rds-dashboard python manage.py collectstatic
```

### Producción

```bash
# Ver logs
docker-compose -f docker-compose.prod.yml logs -f

# Ejecutar comandos dentro del contenedor
docker-compose -f docker-compose.prod.yml exec rds-dashboard python manage.py shell

# Reiniciar servicios
docker-compose -f docker-compose.prod.yml restart
```

## 🔍 Troubleshooting

### Problemas Comunes

1. **Error de permisos de AWS**
   ```bash
   # Verificar configuración de AWS
   docker-compose exec rds-dashboard aws sts get-caller-identity
   ```

2. **Puerto 8000 ocupado**
   ```bash
   # Cambiar puerto en docker-compose.yml
   ports:
     - "8001:8000"  # Usar puerto 8001 en lugar de 8000
   ```

3. **Problemas de archivos estáticos**
   ```bash
   # Recolectar archivos estáticos manualmente
   docker-compose exec rds-dashboard python manage.py collectstatic --noinput
   ```

### Logs y Debugging

```bash
# Ver logs en tiempo real
docker-compose logs -f rds-dashboard

# Ver logs de producción
docker-compose -f docker-compose.prod.yml logs -f rds-dashboard

# Acceder al contenedor para debugging
docker-compose exec rds-dashboard bash
```

## 🔒 Seguridad

### Configuración de Producción

1. **Cambiar SECRET_KEY**
   ```bash
   # Generar nueva clave secreta
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```

2. **Configurar ALLOWED_HOSTS**
   ```bash
   ALLOWED_HOSTS=tu-dominio.com,www.tu-dominio.com
   ```

3. **Usar HTTPS en producción**
   - Configurar proxy reverso (nginx)
   - Usar certificados SSL

### Volúmenes y Persistencia

```bash
# Backup de la base de datos
docker-compose exec rds-dashboard python manage.py dumpdata > backup.json

# Restaurar base de datos
docker-compose exec -T rds-dashboard python manage.py loaddata < backup.json
```

## 📊 Monitoreo

### Health Checks

El contenedor incluye health checks automáticos:

```bash
# Verificar estado del contenedor
docker ps

# Ver logs de health check
docker inspect rds-dashboard
```

### Métricas

```bash
# Ver uso de recursos
docker stats rds-dashboard

# Ver información del contenedor
docker inspect rds-dashboard
```

## 🚀 Despliegue en Producción

### Con Docker Compose

```bash
# 1. Configurar variables de entorno
cp .env.example .env
# Editar .env con valores de producción

# 2. Construir y ejecutar
docker-compose -f docker-compose.prod.yml up -d --build

# 3. Verificar estado
docker-compose -f docker-compose.prod.yml ps
```

### Con Docker Swarm

```bash
# 1. Inicializar swarm
docker swarm init

# 2. Desplegar stack
docker stack deploy -c docker-compose.prod.yml rds-dashboard

# 3. Verificar servicios
docker service ls
```

## 📝 Notas Adicionales

- El contenedor usa Python 3.11 slim para optimizar el tamaño
- Se incluye AWS CLI para interactuar con servicios AWS
- Los logs se guardan en `/app/logs/` dentro del contenedor
- Los archivos estáticos se recolectan automáticamente al iniciar

## 🤝 Contribución

Para contribuir al proyecto:

1. Fork el repositorio
2. Crear una rama para tu feature
3. Hacer commit de tus cambios
4. Push a la rama
5. Crear un Pull Request

## 📞 Soporte

Si tienes problemas con el despliegue:

1. Revisar los logs del contenedor
2. Verificar la configuración de AWS
3. Comprobar que los puertos estén disponibles
4. Revisar los permisos de archivos 