from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.db import transaction
from core.models import AWSProfile, RDSInstance, VpcSecurityGroup, SyncLog
import boto3
from botocore.exceptions import ClientError, NoCredentialsError, ProfileNotFound
import subprocess
import os
from datetime import datetime, timedelta


class Command(BaseCommand):
    help = 'Sincroniza datos de instancias RDS desde AWS a la base de datos local'

    def add_arguments(self, parser):
        parser.add_argument(
            '--profile',
            type=str,
            help='Nombre del perfil de AWS a sincronizar (si no se especifica, sincroniza todos)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forzar sincronización incluso si no ha pasado el tiempo mínimo'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mostrar qué se haría sin ejecutar cambios'
        )

    def handle(self, *args, **options):
        profile_name = options['profile']
        force = options['force']
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING('MODO DRY-RUN: No se realizarán cambios'))

        # Obtener perfiles a sincronizar
        if profile_name:
            try:
                profiles = [AWSProfile.objects.get(name=profile_name)]
            except AWSProfile.DoesNotExist:
                raise CommandError(f'Perfil "{profile_name}" no encontrado en la base de datos')
        else:
            profiles = AWSProfile.objects.filter(is_active=True)

        if not profiles:
            self.stdout.write(self.style.WARNING('No hay perfiles activos para sincronizar'))
            return

        for profile in profiles:
            self.stdout.write(f'Sincronizando perfil: {profile.name}')
            self.sync_profile(profile, force, dry_run)

    def sync_profile(self, profile, force, dry_run):
        """Sincroniza un perfil específico"""
        sync_log = None
        
        try:
            # Verificar si es necesario sincronizar
            if not force and profile.last_sync:
                time_since_last_sync = timezone.now() - profile.last_sync
                if time_since_last_sync < timedelta(minutes=15):  # Mínimo 15 minutos entre sincronizaciones
                    self.stdout.write(
                        self.style.WARNING(
                            f'Perfil {profile.name} sincronizado hace {time_since_last_sync.seconds // 60} minutos. '
                            f'Use --force para forzar sincronización.'
                        )
                    )
                    return

            # Crear log de sincronización
            if not dry_run:
                sync_log = SyncLog.objects.create(
                    profile=profile,
                    status='success',
                    started_at=timezone.now()
                )

            # Obtener instancias de AWS
            aws_instances = self.get_aws_instances(profile.name)
            
            if isinstance(aws_instances, dict) and 'error' in aws_instances:
                error_msg = aws_instances['error']
                self.stdout.write(self.style.ERROR(f'Error obteniendo instancias: {error_msg}'))
                
                if not dry_run and sync_log:
                    sync_log.status = 'failed'
                    sync_log.error_message = error_msg
                    sync_log.completed_at = timezone.now()
                    sync_log.save()
                return

            # Obtener instancias existentes en la base de datos
            existing_instances = {
                instance.instance_id: instance 
                for instance in profile.rds_instances.all()
            }

            instances_found = len(aws_instances)
            instances_created = 0
            instances_updated = 0
            instances_deleted = 0

            # Procesar instancias de AWS
            for aws_instance in aws_instances:
                instance_id = aws_instance['DBInstanceIdentifier']
                
                if instance_id in existing_instances:
                    # Actualizar instancia existente
                    if not dry_run:
                        self.update_instance(existing_instances[instance_id], aws_instance)
                        instances_updated += 1
                    else:
                        self.stdout.write(f'  Actualizaría: {instance_id}')
                        instances_updated += 1
                else:
                    # Crear nueva instancia
                    if not dry_run:
                        self.create_instance(profile, aws_instance)
                        instances_created += 1
                    else:
                        self.stdout.write(f'  Crearía: {instance_id}')
                        instances_created += 1

            # Eliminar instancias que ya no existen en AWS
            aws_instance_ids = {instance['DBInstanceIdentifier'] for instance in aws_instances}
            for instance_id, instance in existing_instances.items():
                if instance_id not in aws_instance_ids:
                    if not dry_run:
                        self.stdout.write(f'  Eliminando: {instance_id}')
                        instance.delete()
                        instances_deleted += 1
                    else:
                        self.stdout.write(f'  Eliminaría: {instance_id}')
                        instances_deleted += 1

            # Actualizar perfil
            if not dry_run:
                profile.last_sync = timezone.now()
                profile.save()

                # Actualizar log de sincronización
                if sync_log:
                    sync_log.instances_found = instances_found
                    sync_log.instances_created = instances_created
                    sync_log.instances_updated = instances_updated
                    sync_log.instances_deleted = instances_deleted
                    sync_log.completed_at = timezone.now()
                    sync_log.save()

            # Mostrar resumen
            self.stdout.write(
                self.style.SUCCESS(
                    f'Perfil {profile.name} sincronizado: '
                    f'{instances_found} encontradas, '
                    f'{instances_created} creadas, '
                    f'{instances_updated} actualizadas, '
                    f'{instances_deleted} eliminadas'
                )
            )

        except Exception as e:
            error_msg = f'Error sincronizando perfil {profile.name}: {str(e)}'
            self.stdout.write(self.style.ERROR(error_msg))
            
            if not dry_run and sync_log:
                sync_log.status = 'failed'
                sync_log.error_message = error_msg
                sync_log.completed_at = timezone.now()
                sync_log.save()

    def get_aws_instances(self, profile_name):
        """Obtiene instancias de RDS desde AWS"""
        try:
            session = boto3.Session(profile_name=profile_name)
            rds_client = session.client('rds')
            
            response = rds_client.describe_db_instances()
            return response['DBInstances']
            
        except ProfileNotFound:
            return {'error': f'Perfil "{profile_name}" no encontrado'}
        except NoCredentialsError:
            return {'error': 'No se encontraron credenciales de AWS'}
        except ClientError as e:
            return {'error': f'Error de AWS: {str(e)}'}
        except Exception as e:
            return {'error': f'Error inesperado: {str(e)}'}

    def create_instance(self, profile, aws_instance):
        """Crea una nueva instancia en la base de datos"""
        with transaction.atomic():
            # Crear instancia principal
            instance = RDSInstance.objects.create(
                instance_id=aws_instance['DBInstanceIdentifier'],
                profile=profile,
                instance_class=aws_instance.get('DBInstanceClass', 'N/A'),
                engine=aws_instance.get('Engine', 'N/A'),
                engine_version=aws_instance.get('EngineVersion', 'N/A'),
                status=aws_instance.get('DBInstanceStatus', 'N/A'),
                endpoint_address=aws_instance.get('Endpoint', {}).get('Address'),
                endpoint_port=aws_instance.get('Endpoint', {}).get('Port'),
                allocated_storage=aws_instance.get('AllocatedStorage', 0),
                storage_type=aws_instance.get('StorageType', 'gp2'),
                availability_zone=aws_instance.get('AvailabilityZone', 'N/A'),
                multi_az=aws_instance.get('MultiAZ', False),
                publicly_accessible=aws_instance.get('PubliclyAccessible', False),
                database_name=aws_instance.get('DBName'),
                master_username=aws_instance.get('MasterUsername'),
                backup_retention_period=aws_instance.get('BackupRetentionPeriod', 0),
                vpc_id=aws_instance.get('DBSubnetGroup', {}).get('VpcId'),
                subnet_group_name=aws_instance.get('DBSubnetGroup', {}).get('DBSubnetGroupName'),
            )

            # Crear grupos de seguridad
            for sg in aws_instance.get('VpcSecurityGroups', []):
                VpcSecurityGroup.objects.create(
                    rds_instance=instance,
                    security_group_id=sg.get('VpcSecurityGroupId', 'N/A'),
                    status=sg.get('Status', 'N/A')
                )

    def update_instance(self, instance, aws_instance):
        """Actualiza una instancia existente"""
        with transaction.atomic():
            # Actualizar campos básicos
            instance.instance_class = aws_instance.get('DBInstanceClass', 'N/A')
            instance.engine = aws_instance.get('Engine', 'N/A')
            instance.engine_version = aws_instance.get('EngineVersion', 'N/A')
            instance.status = aws_instance.get('DBInstanceStatus', 'N/A')
            instance.endpoint_address = aws_instance.get('Endpoint', {}).get('Address')
            instance.endpoint_port = aws_instance.get('Endpoint', {}).get('Port')
            instance.allocated_storage = aws_instance.get('AllocatedStorage', 0)
            instance.storage_type = aws_instance.get('StorageType', 'gp2')
            instance.availability_zone = aws_instance.get('AvailabilityZone', 'N/A')
            instance.multi_az = aws_instance.get('MultiAZ', False)
            instance.publicly_accessible = aws_instance.get('PubliclyAccessible', False)
            instance.database_name = aws_instance.get('DBName')
            instance.master_username = aws_instance.get('MasterUsername')
            instance.backup_retention_period = aws_instance.get('BackupRetentionPeriod', 0)
            instance.vpc_id = aws_instance.get('DBSubnetGroup', {}).get('VpcId')
            instance.subnet_group_name = aws_instance.get('DBSubnetGroup', {}).get('DBSubnetGroupName')
            instance.last_sync = timezone.now()
            instance.save()

            # Actualizar grupos de seguridad
            instance.security_groups.all().delete()
            for sg in aws_instance.get('VpcSecurityGroups', []):
                VpcSecurityGroup.objects.create(
                    rds_instance=instance,
                    security_group_id=sg.get('VpcSecurityGroupId', 'N/A'),
                    status=sg.get('Status', 'N/A')
                ) 