from django.contrib import admin
from .models import EquipmentPassport, MaintenanceWork, EquipmentType


@admin.register(EquipmentType)
class EquipmentTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_by', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'description')


@admin.register(EquipmentPassport)
class EquipmentPassportAdmin(admin.ModelAdmin):
    list_display = ('name', 'serial_number', 'inventory_number', 'equipment_type', 'status', 'created_by', 'created_at')
    list_filter = ('status', 'equipment_type', 'created_at')
    search_fields = ('name', 'serial_number', 'inventory_number', 'location')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(created_by=request.user)


@admin.register(MaintenanceWork)
class MaintenanceWorkAdmin(admin.ModelAdmin):
    list_display = ('passport', 'work_type', 'work_date', 'responsible_person', 'cost')
    list_filter = ('work_type', 'work_date')
    search_fields = ('passport__name', 'responsible_person', 'description')
    date_hierarchy = 'work_date'