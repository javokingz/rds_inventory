from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import AWSProfile, RDSInstance, VpcSecurityGroup, RDSMetric, SyncLog

@admin.register(AWSProfile)
class AWSProfileAdmin(admin.ModelAdmin):
    list_display = ['name', 'region', 'is_active', 'last_sync', 'instances_count', 'created_at']
    list_filter = ['is_active', 'region', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at', 'last_sync']
    
    def instances_count(self, obj):
        count = obj.rds_instances.count()
        if count > 0:
            url = reverse('admin:core_rdsinstance_changelist') + f'?profile__id__exact={obj.id}'
            return format_html('<a href="{}">{} instancias</a>', url, count)
        return '0 instancias'
    instances_count.short_description = 'Instancias RDS'
    
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('rds_instances')

@admin.register(RDSInstance)
class RDSInstanceAdmin(admin.ModelAdmin):
    list_display = [
        'instance_id', 'profile', 'status', 'engine', 'instance_class', 
        'availability_zone', 'multi_az', 'endpoint_display', 'last_sync'
    ]
    list_filter = [
        'status', 'engine', 'instance_class', 'storage_type', 'multi_az', 
        'publicly_accessible', 'profile', 'created_at'
    ]
    search_fields = ['instance_id', 'endpoint_address', 'database_name']
    readonly_fields = ['created_at', 'updated_at', 'last_sync']
    list_per_page = 50
    
    fieldsets = (
        ('Identificación', {
            'fields': ('instance_id', 'profile')
        }),
        ('Información Básica', {
            'fields': ('instance_class', 'engine', 'engine_version', 'status')
        }),
        ('Endpoint', {
            'fields': ('endpoint_address', 'endpoint_port')
        }),
        ('Almacenamiento', {
            'fields': ('allocated_storage', 'storage_type')
        }),
        ('Configuración de Red', {
            'fields': ('availability_zone', 'multi_az', 'publicly_accessible')
        }),
        ('Base de Datos', {
            'fields': ('database_name', 'master_username', 'backup_retention_period')
        }),
        ('VPC y Seguridad', {
            'fields': ('vpc_id', 'subnet_group_name')
        }),
        ('Metadatos', {
            'fields': ('created_at', 'updated_at', 'last_sync'),
            'classes': ('collapse',)
        }),
    )
    
    def endpoint_display(self, obj):
        if obj.endpoint_address and obj.endpoint_port:
            return f"{obj.endpoint_address}:{obj.endpoint_port}"
        return "No disponible"
    endpoint_display.short_description = 'Endpoint'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('profile')

@admin.register(VpcSecurityGroup)
class VpcSecurityGroupAdmin(admin.ModelAdmin):
    list_display = ['security_group_id', 'rds_instance', 'status']
    list_filter = ['status', 'rds_instance__profile']
    search_fields = ['security_group_id', 'rds_instance__instance_id']
    list_per_page = 100

@admin.register(RDSMetric)
class RDSMetricAdmin(admin.ModelAdmin):
    list_display = ['rds_instance', 'metric_name', 'timestamp', 'average', 'maximum', 'minimum', 'unit']
    list_filter = ['metric_name', 'rds_instance__profile', 'timestamp']
    search_fields = ['rds_instance__instance_id']
    readonly_fields = ['timestamp']
    list_per_page = 100
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('rds_instance', 'rds_instance__profile')

@admin.register(SyncLog)
class SyncLogAdmin(admin.ModelAdmin):
    list_display = [
        'profile', 'status', 'instances_found', 'instances_updated', 
        'instances_created', 'instances_deleted', 'duration', 'started_at'
    ]
    list_filter = ['status', 'profile', 'started_at']
    search_fields = ['profile__name', 'error_message']
    readonly_fields = ['started_at', 'completed_at', 'duration']
    list_per_page = 50
    
    fieldsets = (
        ('Información General', {
            'fields': ('profile', 'status')
        }),
        ('Estadísticas', {
            'fields': ('instances_found', 'instances_updated', 'instances_created', 'instances_deleted')
        }),
        ('Tiempo', {
            'fields': ('started_at', 'completed_at', 'duration')
        }),
        ('Errores', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        }),
    )
    
    def duration(self, obj):
        return obj.duration
    duration.short_description = 'Duración'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('profile')

# Configuración del admin
admin.site.site_header = "RDS Dashboard - Administración"
admin.site.site_title = "RDS Dashboard Admin"
admin.site.index_title = "Panel de Control"


