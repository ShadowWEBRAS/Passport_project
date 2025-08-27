from django.contrib import admin
from django.http import HttpResponse
from django.contrib import messages
from django.utils.translation import ngettext
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
    actions = ['export_to_json', 'mass_delete', 'delete_selected_with_files']

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
        count = queryset.count()
        queryset.delete()

        self.message_user(
            request,
            ngettext(
                'Успешно удален %d паспорт.',
                'Успешно удалено %d паспортов.',
                count,
            ) % count,
            messages.SUCCESS
        )

    mass_delete.short_description = "Массовое удаление (с файлами)"

    def delete_selected_with_files(self, request, queryset):
        """Массовое удаление с подтверждением"""
        if request.POST.get('post'):
            # Действительное удаление после подтверждения
            return self.mass_delete(request, queryset)
        else:
            # Показать страницу подтверждения
            return self._delete_selected_with_files_confirmation(request, queryset)

    delete_selected_with_files.short_description = "Удалить выбранные паспорта (с файлами)"

    def _delete_selected_with_files_confirmation(self, request, queryset):
        """Страница подтверждения массового удаления"""
        from django.template.response import TemplateResponse
        from django.utils.translation import gettext as _

        opts = self.model._meta
        app_label = opts.app_label

        if len(queryset) == 1:
            objects_name = opts.verbose_name
        else:
            objects_name = opts.verbose_name_plural

        title = _("Удалить выбранные %(objects_name)s") % {'objects_name': objects_name}

        context = {
            **self.admin_site.each_context(request),
            'title': title,
            'objects': queryset,
            'object_name': str(objects_name),
            'deletable_objects': [queryset],
            'model_count': len(queryset),
            'opts': opts,
            'app_label': app_label,
        }

        request.current_app = self.admin_site.name

        return TemplateResponse(
            request,
            "admin/passports/equipmentpassport/delete_selected_confirmation.html",
            context,
        )

    def get_actions(self, request):
        actions = super().get_actions(request)
        # Заменяем стандартное действие удаления на наше
        if 'delete_selected' in actions:
            del actions['delete_selected']
        actions['delete_selected_with_files'] = (
            self.delete_selected_with_files,
            'delete_selected_with_files',
            "Удалить выбранные паспорта (с файлами)"
        )
        return actions


@admin.register(MaintenanceWork)
class MaintenanceWorkAdmin(admin.ModelAdmin):
    list_display = ('passport', 'work_type', 'work_date', 'responsible_person', 'cost')
    list_filter = ('work_type', 'work_date')
    search_fields = ('passport__name', 'responsible_person', 'description')
    date_hierarchy = 'work_date'