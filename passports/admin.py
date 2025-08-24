from django.contrib import admin
from .models import EquipmentPassport, MaintenanceWork, EquipmentType
from .utils import load_passport_from_file, delete_passport_file


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
    actions = ['export_to_json', 'mass_delete']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(created_by=request.user)

    def export_to_json(self, request, queryset):
        """Действие для экспорта выбранных паспортов в JSON"""
        import json
        from django.http import HttpResponse

        data = []
        for passport in queryset:
            file_data = load_passport_from_file(passport.id)
            if file_data:
                data.append(file_data)

        response = HttpResponse(json.dumps(data, indent=2, ensure_ascii=False), content_type='application/json')
        response['Content-Disposition'] = 'attachment; filename="passports_export.json"'
        return response

    export_to_json.short_description = "Экспортировать выбранные паспорта в JSON"

    def mass_delete(self, request, queryset):
        """Действие для массового удаления с очисткой файлов"""
        for passport in queryset:
            delete_passport_file(passport.id)
        queryset.delete()
        self.message_user(request, f"Успешно удалено {queryset.count()} паспортов.")

    mass_delete.short_description = "Массовое удаление (с файлами)"


@admin.register(MaintenanceWork)
class MaintenanceWorkAdmin(admin.ModelAdmin):
    list_display = ('passport', 'work_type', 'work_date', 'responsible_person', 'cost')
    list_filter = ('work_type', 'work_date')
    search_fields = ('passport__name', 'responsible_person', 'description')
    date_hierarchy = 'work_date'