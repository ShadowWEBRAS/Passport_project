from django import forms
from .models import EquipmentPassport, MaintenanceWork, EquipmentType


class PassportForm(forms.ModelForm):
    equipment_type_name = forms.CharField(
        label='Тип оборудования',
        required=False,
        widget=forms.TextInput(attrs={'list': 'equipment-types'})
    )

    class Meta:
        model = EquipmentPassport
        fields = [
            'name', 'serial_number', 'inventory_number', 'production_date',
            'commissioning_date', 'description', 'location', 'responsible_person',
            'status', 'last_maintenance', 'photo'
        ]
        widgets = {
            'production_date': forms.DateInput(attrs={'type': 'date'}),
            'commissioning_date': forms.DateInput(attrs={'type': 'date'}),
            'last_maintenance': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.equipment_type:
            self.fields['equipment_type_name'].initial = self.instance.equipment_type.name

    def save(self, commit=True):
        passport = super().save(commit=False)

        equipment_type_name = self.cleaned_data.get('equipment_type_name')
        if equipment_type_name:
            equipment_type, created = EquipmentType.objects.get_or_create(
                name=equipment_type_name,
                defaults={'created_by': self.initial.get('user')}
            )
            passport.equipment_type = equipment_type

        if commit:
            passport.save()
            self.save_m2m()

        return passport


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