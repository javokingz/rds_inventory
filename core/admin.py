from django.contrib import admin


class ServiceAdmin(admin.ModelAdmin):
    readonly_fields = ('created', 'uploated')


