from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class AWSProfile(models.Model):
    """Modelo para almacenar perfiles de AWS"""
    name = models.CharField(max_length=100, unique=True)
    region = models.CharField(max_length=50, default='us-east-1')
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_sync = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Perfil AWS"
        verbose_name_plural = "Perfiles AWS"
        ordering = ['name']
    
    def __str__(self):
        return self.name

class RDSInstance(models.Model):
    """Modelo para almacenar instancias de RDS"""
    
    # Estados de instancia
    STATUS_CHOICES = [
        ('available', 'Disponible'),
        ('creating', 'Creando'),
        ('deleting', 'Eliminando'),
        ('failed', 'Fallido'),
        ('inaccessible-encryption-credentials', 'Credenciales de encriptación inaccesibles'),
        ('incompatible-parameters', 'Parámetros incompatibles'),
        ('incompatible-restore', 'Restauración incompatible'),
        ('incompatible-network', 'Red incompatible'),
        ('incompatible-option-group', 'Grupo de opciones incompatible'),
        ('incompatible-parameters', 'Parámetros incompatibles'),
        ('maintenance', 'Mantenimiento'),
        ('modifying', 'Modificando'),
        ('rebooting', 'Reiniciando'),
        ('renaming', 'Renombrando'),
        ('resetting-master-credentials', 'Reiniciando credenciales maestras'),
        ('restore-error', 'Error de restauración'),
        ('storage-full', 'Almacenamiento lleno'),
        ('storage-optimization', 'Optimización de almacenamiento'),
        ('upgrading', 'Actualizando'),
    ]
    
    # Tipos de motor
    ENGINE_CHOICES = [
        ('mysql', 'MySQL'),
        ('postgres', 'PostgreSQL'),
        ('mariadb', 'MariaDB'),
        ('oracle-ee', 'Oracle Enterprise Edition'),
        ('oracle-se', 'Oracle Standard Edition'),
        ('oracle-se1', 'Oracle Standard Edition One'),
        ('oracle-se2', 'Oracle Standard Edition Two'),
        ('sqlserver-ee', 'SQL Server Enterprise Edition'),
        ('sqlserver-se', 'SQL Server Standard Edition'),
        ('sqlserver-ex', 'SQL Server Express Edition'),
        ('sqlserver-web', 'SQL Server Web Edition'),
        ('aurora', 'Aurora MySQL'),
        ('aurora-postgresql', 'Aurora PostgreSQL'),
    ]
    
    # Tipos de almacenamiento
    STORAGE_TYPE_CHOICES = [
        ('gp2', 'General Purpose SSD (gp2)'),
        ('gp3', 'General Purpose SSD (gp3)'),
        ('io1', 'Provisioned IOPS SSD (io1)'),
        ('io2', 'Provisioned IOPS SSD (io2)'),
        ('standard', 'Magnetic'),
    ]
    
    # Identificación
    instance_id = models.CharField(max_length=255, unique=True)
    profile = models.ForeignKey(AWSProfile, on_delete=models.CASCADE, related_name='rds_instances')
    
    # Información básica
    instance_class = models.CharField(max_length=100)
    engine = models.CharField(max_length=50, choices=ENGINE_CHOICES)
    engine_version = models.CharField(max_length=50)
    status = models.CharField(max_length=100, choices=STATUS_CHOICES)
    
    # Endpoint
    endpoint_address = models.CharField(max_length=255, blank=True, null=True)
    endpoint_port = models.IntegerField(blank=True, null=True)
    
    # Almacenamiento
    allocated_storage = models.IntegerField(help_text='Almacenamiento en GB')
    storage_type = models.CharField(max_length=20, choices=STORAGE_TYPE_CHOICES)
    
    # Configuración de red
    availability_zone = models.CharField(max_length=100)
    multi_az = models.BooleanField(default=False)
    publicly_accessible = models.BooleanField(default=False)
    
    # Configuración de base de datos
    database_name = models.CharField(max_length=100, blank=True, null=True)
    master_username = models.CharField(max_length=100, blank=True, null=True)
    
    # Configuración de backup
    backup_retention_period = models.IntegerField(help_text='Período de retención en días')
    
    # VPC y seguridad
    vpc_id = models.CharField(max_length=100, blank=True, null=True)
    subnet_group_name = models.CharField(max_length=100, blank=True, null=True)
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_sync = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Instancia RDS"
        verbose_name_plural = "Instancias RDS"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['instance_id']),
            models.Index(fields=['profile', 'status']),
            models.Index(fields=['engine']),
            models.Index(fields=['last_sync']),
        ]
    
    def __str__(self):
        return f"{self.instance_id} ({self.profile.name})"
    
    @property
    def is_available(self):
        return self.status == 'available'
    
    @property
    def endpoint_display(self):
        if self.endpoint_address and self.endpoint_port:
            return f"{self.endpoint_address}:{self.endpoint_port}"
        return "No disponible"

class VpcSecurityGroup(models.Model):
    """Modelo para grupos de seguridad de VPC"""
    rds_instance = models.ForeignKey(RDSInstance, on_delete=models.CASCADE, related_name='security_groups')
    security_group_id = models.CharField(max_length=100)
    status = models.CharField(max_length=50)
    
    class Meta:
        verbose_name = "Grupo de Seguridad VPC"
        verbose_name_plural = "Grupos de Seguridad VPC"
        unique_together = ['rds_instance', 'security_group_id']
    
    def __str__(self):
        return f"{self.security_group_id} - {self.rds_instance.instance_id}"

class RDSMetric(models.Model):
    """Modelo para almacenar métricas de CloudWatch"""
    
    METRIC_TYPES = [
        ('CPUUtilization', 'Utilización de CPU'),
        ('FreeableMemory', 'Memoria Libre'),
        ('FreeStorageSpace', 'Espacio Libre de Almacenamiento'),
        ('DatabaseConnections', 'Conexiones de Base de Datos'),
        ('ReadIOPS', 'Operaciones de Lectura por Segundo'),
        ('WriteIOPS', 'Operaciones de Escritura por Segundo'),
        ('ReadLatency', 'Latencia de Lectura'),
        ('WriteLatency', 'Latencia de Escritura'),
        ('NetworkReceiveThroughput', 'Rendimiento de Recepción de Red'),
        ('NetworkTransmitThroughput', 'Rendimiento de Transmisión de Red'),
    ]
    
    rds_instance = models.ForeignKey(RDSInstance, on_delete=models.CASCADE, related_name='metrics')
    metric_name = models.CharField(max_length=100, choices=METRIC_TYPES)
    timestamp = models.DateTimeField()
    average = models.FloatField()
    maximum = models.FloatField()
    minimum = models.FloatField()
    unit = models.CharField(max_length=20)
    
    class Meta:
        verbose_name = "Métrica RDS"
        verbose_name_plural = "Métricas RDS"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['rds_instance', 'metric_name', 'timestamp']),
            models.Index(fields=['timestamp']),
        ]
        unique_together = ['rds_instance', 'metric_name', 'timestamp']
    
    def __str__(self):
        return f"{self.rds_instance.instance_id} - {self.metric_name} - {self.timestamp}"

class SyncLog(models.Model):
    """Modelo para registrar logs de sincronización"""
    
    SYNC_STATUS_CHOICES = [
        ('success', 'Exitoso'),
        ('failed', 'Fallido'),
        ('partial', 'Parcial'),
    ]
    
    profile = models.ForeignKey(AWSProfile, on_delete=models.CASCADE, related_name='sync_logs')
    status = models.CharField(max_length=20, choices=SYNC_STATUS_CHOICES)
    instances_found = models.IntegerField(default=0)
    instances_updated = models.IntegerField(default=0)
    instances_created = models.IntegerField(default=0)
    instances_deleted = models.IntegerField(default=0)
    error_message = models.TextField(blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Log de Sincronización"
        verbose_name_plural = "Logs de Sincronización"
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.profile.name} - {self.status} - {self.started_at}"
    
    @property
    def duration(self):
        if self.completed_at:
            return self.completed_at - self.started_at
        return timezone.now() - self.started_at
