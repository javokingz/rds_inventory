from django.shortcuts import render, HttpResponse
from django.http import JsonResponse
import boto3
import json
from botocore.exceptions import ClientError, NoCredentialsError, ProfileNotFound
import subprocess
import os

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