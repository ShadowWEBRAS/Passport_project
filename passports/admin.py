from django.contrib import admin
from .models import EquipmentPassport, EquipmentType

@admin.register(EquipmentType)
class EquipmentTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_by', 'created_at')
    search_fields = ('name',)
    list_filter = ('created_at',)

@admin.register(EquipmentPassport)
class EquipmentPassportAdmin(admin.ModelAdmin):
    list_display = ('name', 'equipment_type', 'serial_number', 'inventory_number', 'created_by', 'status', 'created_at')
    list_filter = ('status', 'created_at', 'created_by', 'equipment_type')
    search_fields = ('name', 'serial_number', 'inventory_number')
    date_hierarchy = 'created_at'