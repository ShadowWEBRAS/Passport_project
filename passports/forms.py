from django import forms
from .models import EquipmentPassport, MaintenanceWork, EquipmentType
import json


class PassportForm(forms.ModelForm):
    equipment_type_name = forms.CharField(
        label='Тип оборудования',
        required=False,
        widget=forms.TextInput(attrs={'list': 'equipment-types'})
    )

    # Добавим поле для custom fields
    custom_fields_json = forms.CharField(
        required=False,
        widget=forms.HiddenInput(),
        initial='{}'
    )

    class Meta:
        model = EquipmentPassport
        fields = [
            'name', 'serial_number', 'inventory_number', 'production_date',
            'commissioning_date', 'description', 'location', 'responsible_person',
            'status', 'last_maintenance', 'photo'
        ]
        widgets = {
            'production_date': forms.DateInput(
                attrs={'type': 'date'},
                format='%Y-%m-%d'
            ),
            'commissioning_date': forms.DateInput(
                attrs={'type': 'date'},
                format='%Y-%m-%d'
            ),
            'last_maintenance': forms.DateInput(
                attrs={'type': 'date'},
                format='%Y-%m-%d'
            ),
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.equipment_type:
            self.fields['equipment_type_name'].initial = self.instance.equipment_type.name

        # Убедитесь, что даты отображаются в правильном формате
        for field_name in ['production_date', 'commissioning_date', 'last_maintenance']:
            if self.instance and getattr(self.instance, field_name):
                self.initial[field_name] = getattr(self.instance, field_name).strftime('%Y-%m-%d')

        # Устанавливаем начальное значение для custom fields
        if self.instance and self.instance.custom_fields:
            self.fields['custom_fields_json'].initial = json.dumps(self.instance.custom_fields)


class MaintenanceWorkForm(forms.ModelForm):
    class Meta:
        model = MaintenanceWork
        fields = ['work_type', 'work_date', 'responsible_person', 'description', 'cost', 'materials_used']
        widgets = {
            'work_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
            'materials_used': forms.Textarea(attrs={'rows': 2}),
        }


class CustomFieldForm(forms.Form):
    field_name = forms.CharField(label='Название поля', max_length=100)
    field_value = forms.CharField(label='Значение', required=False)
    field_type = forms.ChoiceField(
        label='Тип поля',
        choices=[
            ('text', 'Текст'),
            ('number', 'Число'),
            ('date', 'Дата'),
            ('boolean', 'Да/Нет')
        ]
    )