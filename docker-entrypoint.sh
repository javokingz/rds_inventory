#!/bin/bash

# Salir si hay algún error
set -e

echo "🚀 Iniciando RDS Dashboard..."

# Función para esperar a que el servicio esté listo
wait_for_service() {
    echo "⏳ Esperando a que el servicio esté listo..."
    sleep 5
}

# Función para ejecutar migraciones
run_migrations() {
    echo "📦 Ejecutando migraciones de Django..."
    python manage.py migrate --noinput
}

# Función para recolectar archivos estáticos
collect_static() {
    echo "📁 Recolectando archivos estáticos..."
    python manage.py collectstatic --noinput
}

# Función para crear superusuario si no existe
create_superuser() {
    if [ "$CREATE_SUPERUSER" = "true" ]; then
        echo "👤 Creando superusuario..."
        python manage.py shell -c "
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Superusuario creado: admin/admin123')
else:
    print('Superusuario ya existe')
"
    fi
}

# Función para verificar la configuración de AWS
check_aws_config() {
    echo "🔍 Verificando configuración de AWS..."
    if [ -d "/home/appuser/.aws" ]; then
        echo "✅ Configuración de AWS encontrada"
        aws sts get-caller-identity --output table || echo "⚠️  No se pudo verificar la identidad de AWS"
    else
        echo "⚠️  Configuración de AWS no encontrada. Asegúrate de montar ~/.aws como volumen."
    fi
}

# Ejecutar funciones de inicialización
wait_for_service
run_migrations
collect_static
create_superuser
check_aws_config

echo "✅ RDS Dashboard está listo para usar!"
echo "🌐 Accede a http://localhost:8000"

# Ejecutar el servidor
exec python manage.py runserver 0.0.0.0:8000 