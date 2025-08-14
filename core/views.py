from django.shortcuts import render, HttpResponse, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from .models import AWSProfile, RDSInstance, VpcSecurityGroup, RDSMetric, SyncLog
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

@login_required
def home(request):
    """Vista principal que muestra el dashboard de RDS desde la base de datos"""
    # Obtener perfiles activos de la base de datos
    profiles = AWSProfile.objects.filter(is_active=True).order_by('name')
    selected_profile_id = request.GET.get('profile', '')
    
    rds_instances = None
    error_message = None
    selected_profile = None
    
    if selected_profile_id:
        try:
            selected_profile = get_object_or_404(AWSProfile, id=selected_profile_id, is_active=True)
            rds_instances = RDSInstance.objects.filter(profile=selected_profile).select_related('profile')
        except AWSProfile.DoesNotExist:
            error_message = f'Perfil con ID {selected_profile_id} no encontrado'
    
    # Obtener estadísticas generales
    total_instances = RDSInstance.objects.count()
    available_instances = RDSInstance.objects.filter(status='available').count()
    other_instances = total_instances - available_instances
    
    # Obtener últimos logs de sincronización
    recent_syncs = SyncLog.objects.select_related('profile').order_by('-started_at')[:5]
    
    context = {
        'profiles': profiles,
        'selected_profile': selected_profile,
        'rds_instances': rds_instances,
        'error_message': error_message,
        'total_instances': total_instances,
        'available_instances': available_instances,
        'other_instances': other_instances,
        'recent_syncs': recent_syncs,
    }
    
    return render(request, 'core/dashboard.html', context)

@login_required
def get_rds_data_ajax(request):
    """Vista AJAX para obtener datos de RDS desde la base de datos"""
    profile_id = request.GET.get('profile')
    if not profile_id:
        return JsonResponse({'error': 'No se especificó un perfil'})
    
    try:
        profile = get_object_or_404(AWSProfile, id=profile_id, is_active=True)
        instances = RDSInstance.objects.filter(profile=profile).select_related('profile')
        
        # Convertir a formato JSON
        data = []
        for instance in instances:
            instance_data = {
                'DBInstanceIdentifier': instance.instance_id,
                'DBInstanceClass': instance.instance_class,
                'Engine': instance.engine,
                'EngineVersion': instance.engine_version,
                'DBInstanceStatus': instance.status,
                'Endpoint': {
                    'Address': instance.endpoint_address or 'N/A',
                    'Port': instance.endpoint_port or 'N/A'
                },
                'AllocatedStorage': instance.allocated_storage,
                'StorageType': instance.storage_type,
                'AvailabilityZone': instance.availability_zone,
                'MultiAZ': instance.multi_az,
                'PubliclyAccessible': instance.publicly_accessible,
                'BackupRetentionPeriod': instance.backup_retention_period,
                'DBName': instance.database_name or 'N/A',
                'MasterUsername': instance.master_username or 'N/A',
                'VpcSecurityGroups': [
                    {
                        'VpcSecurityGroupId': sg.security_group_id,
                        'Status': sg.status
                    } for sg in instance.security_groups.all()
                ],
                'DBSubnetGroup': {
                    'DBSubnetGroupName': instance.subnet_group_name or 'N/A',
                    'VpcId': instance.vpc_id or 'N/A'
                }
            }
            data.append(instance_data)
        
        return JsonResponse({'data': data})
        
    except AWSProfile.DoesNotExist:
        return JsonResponse({'error': 'Perfil no encontrado'})
    except Exception as e:
        return JsonResponse({'error': f'Error: {str(e)}'})

@login_required
def instance_details(request, instance_id):
    """Vista para mostrar detalles de una instancia RDS desde la base de datos"""
    try:
        # Obtener instancia de la base de datos
        instance = get_object_or_404(RDSInstance, instance_id=instance_id)
        
        # Obtener métricas recientes de la base de datos
        end_time = timezone.now()
        start_time = end_time - timedelta(hours=24)
        
        cpu_metrics = RDSMetric.objects.filter(
            rds_instance=instance,
            metric_name='CPUUtilization',
            timestamp__range=(start_time, end_time)
        ).order_by('timestamp')
        
        memory_metrics = RDSMetric.objects.filter(
            rds_instance=instance,
            metric_name='FreeableMemory',
            timestamp__range=(start_time, end_time)
        ).order_by('timestamp')
        
        storage_metrics = RDSMetric.objects.filter(
            rds_instance=instance,
            metric_name='FreeStorageSpace',
            timestamp__range=(start_time, end_time)
        ).order_by('timestamp')
        
        connection_metrics = RDSMetric.objects.filter(
            rds_instance=instance,
            metric_name='DatabaseConnections',
            timestamp__range=(start_time, end_time)
        ).order_by('timestamp')
        
        # Crear gráficas si hay métricas
        cpu_chart = create_metric_chart_from_db(cpu_metrics, 'Utilización de CPU (%)', 'CPU %', 'red')
        memory_chart = create_metric_chart_from_db(memory_metrics, 'Memoria Libre (MB)', 'Memoria (MB)', 'green')
        storage_chart = create_metric_chart_from_db(storage_metrics, 'Espacio Libre de Almacenamiento (MB)', 'Almacenamiento (MB)', 'orange')
        connection_chart = create_metric_chart_from_db(connection_metrics, 'Conexiones de Base de Datos', 'Conexiones', 'purple')
        
        # Calcular estadísticas
        cpu_stats = calculate_stats_from_db(cpu_metrics)
        memory_stats = calculate_stats_from_db(memory_metrics)
        storage_stats = calculate_stats_from_db(storage_metrics)
        connection_stats = calculate_stats_from_db(connection_metrics)
        
        # Obtener grupos de seguridad
        security_groups = instance.security_groups.all()
        
        context = {
            'instance': instance,
            'profile_name': instance.profile.name,
            'cpu_chart': cpu_chart,
            'memory_chart': memory_chart,
            'storage_chart': storage_chart,
            'connection_chart': connection_chart,
            'cpu_stats': cpu_stats,
            'memory_stats': memory_stats,
            'storage_stats': storage_stats,
            'connection_stats': connection_stats,
            'security_groups': security_groups,
        }
        
        return render(request, 'core/instance_details.html', context)
        
    except Exception as e:
        return HttpResponse(f'Error: {str(e)}', status=500)

def create_metric_chart_from_db(metrics, title, ylabel, color='blue'):
    """Crea una gráfica de métricas desde datos de la base de datos"""
    if not metrics.exists():
        return None
    
    # Extraer datos
    timestamps = [point.timestamp for point in metrics]
    averages = [point.average for point in metrics]
    maximums = [point.maximum for point in metrics]
    minimums = [point.minimum for point in metrics]
    
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

def calculate_stats_from_db(metrics):
    """Calcula estadísticas desde métricas de la base de datos"""
    if not metrics.exists():
        return {'avg': 0, 'max': 0, 'min': 0, 'current': 0}
    
    averages = [m.average for m in metrics]
    maximums = [m.maximum for m in metrics]
    minimums = [m.minimum for m in metrics]
    
    return {
        'avg': round(sum(averages) / len(averages), 2),
        'max': round(max(maximums), 2),
        'min': round(min(minimums), 2),
        'current': round(averages[-1] if averages else 0, 2)
    }

@login_required
def sync_status(request):
    """Vista para mostrar el estado de sincronización"""
    profiles = AWSProfile.objects.filter(is_active=True).order_by('name')
    recent_syncs = SyncLog.objects.select_related('profile').order_by('-started_at')[:20]
    
    context = {
        'profiles': profiles,
        'recent_syncs': recent_syncs,
    }
    
    return render(request, 'core/sync_status.html', context)

# Funciones auxiliares mantenidas para compatibilidad
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
    """Obtiene las instancias de RDS de un perfil específico (mantenido para compatibilidad)"""
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

def get_cloudwatch_metrics(profile_name, instance_id, metric_name, period=300, hours=24):
    """Obtiene métricas de CloudWatch para una instancia RDS específica (mantenido para compatibilidad)"""
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
    """Crea una gráfica de métricas usando matplotlib (mantenido para compatibilidad)"""
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