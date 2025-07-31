from django import forms
from .models import EquipmentPassport, EquipmentType

class PassportForm(forms.ModelForm):
    class Meta:
        model = EquipmentPassport
        fields = [
            'equipment_type',
            'name',
            'serial_number',
            'inventory_number',
            'production_date',
            'commissioning_date',
            'description',
            'location',
            'responsible_person',
            'status',
            'last_maintenance',
            'photo'
        ]
        widgets = {
            'production_date': forms.DateInput(attrs={'type': 'date'}),
            'commissioning_date': forms.DateInput(attrs={'type': 'date'}),
            'last_maintenance': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 4}),
        }
        labels = {
            'equipment_type': 'Тип оборудования',
            'name': 'Наименование оборудования',
            'serial_number': 'Заводской номер',
            'inventory_number': 'Инвентарный номер',
            'production_date': 'Дата изготовления',
            'commissioning_date': 'Дата ввода в эксплуатацию',
            'description': 'Описание',
            'location': 'Место установки',
            'responsible_person': 'Ответственное лицо',
            'status': 'Статус оборудования',
            'last_maintenance': 'Дата последнего ТО',
            'photo': 'Фото оборудования',
        }

class EquipmentTypeForm(forms.ModelForm):
    class Meta:
        model = EquipmentType
        fields = ['name', 'description']
        labels = {
            'name': 'Название типа',
            'description': 'Описание типа'
        }