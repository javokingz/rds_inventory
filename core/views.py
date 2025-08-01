from django.shortcuts import render, HttpResponse
from django.http import JsonResponse
import boto3
import json
from botocore.exceptions import ClientError, NoCredentialsError, ProfileNotFound
import subprocess
import os
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Configurar matplotlib para usar backend no interactivo
import io
import base64
import pandas as pd
import numpy as np

def get_aws_profiles():
    """Obtiene la lista de perfiles de AWS configurados localmente"""
    try:
        # Usar AWS CLI para obtener los perfiles
        result = subprocess.run(['aws', 'configure', 'list-profiles'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            profiles = result.stdout.strip().split('\n')
            return [profile for profile in profiles if profile]
        else:
            # Fallback: intentar leer el archivo de configuración directamente
            aws_config_path = os.path.expanduser('~/.aws/config')
            if os.path.exists(aws_config_path):
                profiles = []
                with open(aws_config_path, 'r') as f:
                    for line in f:
                        if line.startswith('[profile '):
                            profile = line.strip()[9:-1]  # Remover '[profile ' y ']'
                            profiles.append(profile)
                return profiles
    except Exception as e:
        print(f"Error obteniendo perfiles: {e}")
    
    return []

def get_rds_instances(profile_name):
    """Obtiene las instancias de RDS de un perfil específico"""
    try:
        # Crear sesión de AWS con el perfil especificado
        session = boto3.Session(profile_name=profile_name)
        rds_client = session.client('rds')
        
        # Obtener todas las instancias de RDS
        response = rds_client.describe_db_instances()
        
        instances = []
        for instance in response['DBInstances']:
            instance_info = {
                'DBInstanceIdentifier': instance.get('DBInstanceIdentifier', 'N/A'),
                'DBInstanceClass': instance.get('DBInstanceClass', 'N/A'),
                'Engine': instance.get('Engine', 'N/A'),
                'EngineVersion': instance.get('EngineVersion', 'N/A'),
                'DBInstanceStatus': instance.get('DBInstanceStatus', 'N/A'),
                'Endpoint': {
                    'Address': instance.get('Endpoint', {}).get('Address', 'N/A'),
                    'Port': instance.get('Endpoint', {}).get('Port', 'N/A')
                },
                'AllocatedStorage': instance.get('AllocatedStorage', 'N/A'),
                'StorageType': instance.get('StorageType', 'N/A'),
                'AvailabilityZone': instance.get('AvailabilityZone', 'N/A'),
                'MultiAZ': instance.get('MultiAZ', False),
                'PubliclyAccessible': instance.get('PubliclyAccessible', False),
                'BackupRetentionPeriod': instance.get('BackupRetentionPeriod', 'N/A'),
                'DBName': instance.get('DBName', 'N/A'),
                'MasterUsername': instance.get('MasterUsername', 'N/A'),
                'VpcSecurityGroups': [
                    {
                        'VpcSecurityGroupId': sg.get('VpcSecurityGroupId', 'N/A'),
                        'Status': sg.get('Status', 'N/A')
                    } for sg in instance.get('VpcSecurityGroups', [])
                ],
                'DBSubnetGroup': {
                    'DBSubnetGroupName': instance.get('DBSubnetGroup', {}).get('DBSubnetGroupName', 'N/A'),
                    'VpcId': instance.get('DBSubnetGroup', {}).get('VpcId', 'N/A')
                } if instance.get('DBSubnetGroup') else {}
            }
            instances.append(instance_info)
        
        return instances
    
    except ProfileNotFound:
        return {'error': f'Perfil "{profile_name}" no encontrado'}
    except NoCredentialsError:
        return {'error': 'No se encontraron credenciales de AWS'}
    except ClientError as e:
        return {'error': f'Error de AWS: {str(e)}'}
    except Exception as e:
        return {'error': f'Error inesperado: {str(e)}'}

def home(request):
    """Vista principal que muestra el dashboard de RDS"""
    profiles = get_aws_profiles()
    selected_profile = request.GET.get('profile', '')
    rds_data = None
    error_message = None
    
    if selected_profile:
        rds_data = get_rds_instances(selected_profile)
        if isinstance(rds_data, dict) and 'error' in rds_data:
            error_message = rds_data['error']
            rds_data = None
    
    context = {
        'profiles': profiles,
        'selected_profile': selected_profile,
        'rds_instances': rds_data,
        'error_message': error_message
    }
    
    return render(request, 'core/dashboard.html', context)

def get_rds_data_ajax(request):
    """Vista AJAX para obtener datos de RDS sin recargar la página"""
    profile_name = request.GET.get('profile')
    if not profile_name:
        return JsonResponse({'error': 'No se especificó un perfil'})
    
    rds_data = get_rds_instances(profile_name)
    return JsonResponse({'data': rds_data})

def get_cloudwatch_metrics(profile_name, instance_id, metric_name, period=300, hours=24):
    """Obtiene métricas de CloudWatch para una instancia RDS específica"""
    try:
        session = boto3.Session(profile_name=profile_name)
        cloudwatch = session.client('cloudwatch')
        
        # Calcular el rango de tiempo
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        
        # Obtener métricas
        response = cloudwatch.get_metric_statistics(
            Namespace='AWS/RDS',
            MetricName=metric_name,
            Dimensions=[
                {
                    'Name': 'DBInstanceIdentifier',
                    'Value': instance_id
                }
            ],
            StartTime=start_time,
            EndTime=end_time,
            Period=period,
            Statistics=['Average', 'Maximum', 'Minimum']
        )
        
        return response['Datapoints']
    
    except Exception as e:
        print(f"Error obteniendo métricas de CloudWatch: {e}")
        return []

def create_metric_chart(metric_data, title, ylabel, color='blue'):
    """Crea una gráfica de métricas usando matplotlib"""
    if not metric_data:
        return None
    
    # Ordenar datos por timestamp
    sorted_data = sorted(metric_data, key=lambda x: x['Timestamp'])
    
    # Extraer datos
    timestamps = [point['Timestamp'] for point in sorted_data]
    averages = [point['Average'] for point in sorted_data]
    maximums = [point['Maximum'] for point in sorted_data]
    minimums = [point['Minimum'] for point in sorted_data]
    
    # Crear gráfica
    plt.figure(figsize=(10, 6))
    plt.plot(timestamps, averages, label='Promedio', color=color, linewidth=2)
    plt.fill_between(timestamps, minimums, maximums, alpha=0.3, color=color, label='Rango (Min-Max)')
    
    plt.title(title, fontsize=14, fontweight='bold')
    plt.xlabel('Tiempo', fontsize=12)
    plt.ylabel(ylabel, fontsize=12)
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # Convertir gráfica a base64
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()
    plt.close()
    
    return base64.b64encode(image_png).decode()

def instance_details(request, instance_id):
    """Vista para mostrar detalles de una instancia RDS con métricas de CloudWatch"""
    profile_name = request.GET.get('profile')
    if not profile_name:
        return HttpResponse('Perfil no especificado', status=400)
    
    try:
        # Obtener información de la instancia
        session = boto3.Session(profile_name=profile_name)
        rds_client = session.client('rds')
        
        response = rds_client.describe_db_instances(DBInstanceIdentifier=instance_id)
        if not response['DBInstances']:
            return HttpResponse('Instancia no encontrada', status=404)
        
        instance = response['DBInstances'][0]
        
        # Obtener métricas de CloudWatch
        cpu_metrics = get_cloudwatch_metrics(profile_name, instance_id, 'CPUUtilization')
        memory_metrics = get_cloudwatch_metrics(profile_name, instance_id, 'FreeableMemory')
        storage_metrics = get_cloudwatch_metrics(profile_name, instance_id, 'FreeStorageSpace')
        connection_metrics = get_cloudwatch_metrics(profile_name, instance_id, 'DatabaseConnections')
        
        # Crear gráficas
        cpu_chart = create_metric_chart(cpu_metrics, 'Utilización de CPU (%)', 'CPU %', 'red')
        memory_chart = create_metric_chart(memory_metrics, 'Memoria Libre (MB)', 'Memoria (MB)', 'green')
        storage_chart = create_metric_chart(storage_metrics, 'Espacio Libre de Almacenamiento (MB)', 'Almacenamiento (MB)', 'orange')
        connection_chart = create_metric_chart(connection_metrics, 'Conexiones de Base de Datos', 'Conexiones', 'purple')
        
        # Calcular estadísticas resumidas
        def calculate_stats(metrics):
            if not metrics:
                return {'avg': 0, 'max': 0, 'min': 0, 'current': 0}
            
            averages = [m['Average'] for m in metrics]
            maximums = [m['Maximum'] for m in metrics]
            minimums = [m['Minimum'] for m in metrics]
            
            return {
                'avg': round(sum(averages) / len(averages), 2),
                'max': round(max(maximums), 2),
                'min': round(min(minimums), 2),
                'current': round(averages[-1] if averages else 0, 2)
            }
        
        cpu_stats = calculate_stats(cpu_metrics)
        memory_stats = calculate_stats(memory_metrics)
        storage_stats = calculate_stats(storage_metrics)
        connection_stats = calculate_stats(connection_metrics)
        
        context = {
            'instance': instance,
            'profile_name': profile_name,
            'cpu_chart': cpu_chart,
            'memory_chart': memory_chart,
            'storage_chart': storage_chart,
            'connection_chart': connection_chart,
            'cpu_stats': cpu_stats,
            'memory_stats': memory_stats,
            'storage_stats': storage_stats,
            'connection_stats': connection_stats,
        }
        
        return render(request, 'core/instance_details.html', context)
        
    except Exception as e:
        return HttpResponse(f'Error: {str(e)}', status=500)