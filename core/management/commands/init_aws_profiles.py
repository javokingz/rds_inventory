from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from core.models import AWSProfile
import subprocess
import os


class Command(BaseCommand):
    help = 'Inicializa perfiles de AWS en la base de datos desde la configuración local'

    def add_arguments(self, parser):
        parser.add_argument(
            '--region',
            type=str,
            default='us-east-1',
            help='Región por defecto para los perfiles (default: us-east-1)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forzar recreación de perfiles existentes'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mostrar qué se haría sin ejecutar cambios'
        )

    def handle(self, *args, **options):
        region = options['region']
        force = options['force']
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING('MODO DRY-RUN: No se realizarán cambios'))

        # Obtener perfiles de AWS CLI
        aws_profiles = self.get_aws_profiles()
        
        if not aws_profiles:
            self.stdout.write(self.style.WARNING('No se encontraron perfiles de AWS configurados'))
            return

        self.stdout.write(f'Encontrados {len(aws_profiles)} perfiles de AWS: {", ".join(aws_profiles)}')

        # Procesar cada perfil
        for profile_name in aws_profiles:
            self.process_profile(profile_name, region, force, dry_run)

        self.stdout.write(self.style.SUCCESS('Inicialización de perfiles completada'))

    def get_aws_profiles(self):
        """Obtiene la lista de perfiles de AWS configurados localmente"""
        try:
            # Usar AWS CLI para obtener los perfiles
            result = subprocess.run(
                ['aws', 'configure', 'list-profiles'], 
                capture_output=True, text=True, timeout=10
            )
            
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
            self.stdout.write(self.style.ERROR(f'Error obteniendo perfiles: {e}'))
        
        return []

    def process_profile(self, profile_name, region, force, dry_run):
        """Procesa un perfil específico"""
        try:
            # Verificar si el perfil ya existe
            existing_profile = AWSProfile.objects.filter(name=profile_name).first()
            
            if existing_profile:
                if force:
                    if not dry_run:
                        self.stdout.write(f'  Actualizando perfil existente: {profile_name}')
                        existing_profile.region = region
                        existing_profile.is_active = True
                        existing_profile.save()
                    else:
                        self.stdout.write(f'  Actualizaría perfil existente: {profile_name}')
                else:
                    self.stdout.write(f'  Perfil ya existe: {profile_name} (use --force para actualizar)')
            else:
                if not dry_run:
                    self.stdout.write(f'  Creando nuevo perfil: {profile_name}')
                    AWSProfile.objects.create(
                        name=profile_name,
                        region=region,
                        description=f'Perfil AWS configurado localmente',
                        is_active=True
                    )
                else:
                    self.stdout.write(f'  Crearía nuevo perfil: {profile_name}')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error procesando perfil {profile_name}: {e}')) 