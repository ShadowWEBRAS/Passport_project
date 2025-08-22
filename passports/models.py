from django.db import models
from django.contrib.auth.models import User
import uuid
import os

class EquipmentType(models.Model):
    name = models.CharField('Название типа', max_length=100, unique=True)
    description = models.TextField('Описание типа', blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class EquipmentPassport(models.Model):
    STATUS_CHOICES = [
        ('in_operation', 'В эксплуатации'),
        ('repair', 'В ремонте'),
        ('reserve', 'В резерве'),
        ('decommissioned', 'Списано'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField('Наименование', max_length=255)
    equipment_type = models.ForeignKey(EquipmentType, on_delete=models.SET_NULL, null=True, blank=True)
    serial_number = models.CharField('Заводской номер', max_length=100)
    inventory_number = models.CharField('Инвентарный номер', max_length=100)
    production_date = models.DateField('Дата изготовления')
    commissioning_date = models.DateField('Дата ввода в эксплуатацию')
    description = models.TextField('Описание', blank=True)
    location = models.CharField('Место установки', max_length=255)
    responsible_person = models.CharField('Ответственное лицо', max_length=100, blank=True)
    status = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES, default='in_operation')
    last_maintenance = models.DateField('Дата последнего ТО', null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='passports')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    photo = models.ImageField(
        'Фото оборудования',
        upload_to='equipment_photos/',
        blank=True,
        null=True
    )
    custom_fields = models.JSONField('Пользовательские поля', default=dict, blank=True)

    def __str__(self):
        return f"{self.name} ({self.serial_number})"

    def get_passport_file_path(self):
        from django.conf import settings
        return os.path.join(settings.PASSPORTS_DIR, f"{self.id}.json")

    class Meta:
        ordering = ['-created_at']

class MaintenanceWork(models.Model):
    WORK_TYPES = [
        ('repair', 'Ремонт'),
        ('maintenance', 'Техническое обслуживание'),
        ('diagnostic', 'Диагностика'),
        ('inspection', 'Осмотр'),
        ('calibration', 'Калибровка'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    passport = models.ForeignKey(EquipmentPassport, on_delete=models.CASCADE, related_name='maintenance_works')
    work_type = models.CharField('Тип работы', max_length=20, choices=WORK_TYPES)
    work_date = models.DateField('Дата выполнения')
    responsible_person = models.CharField('Ответственное лицо', max_length=100)
    description = models.TextField('Описание работы', blank=True)
    cost = models.DecimalField('Стоимость', max_digits=10, decimal_places=2, null=True, blank=True)
    materials_used = models.TextField('Использованные материалы', blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    custom_fields = models.JSONField('Дополнительные параметры', default=dict, blank=True)

    def __str__(self):
        return f"{self.get_work_type_display()} - {self.passport.name}"

    class Meta:
        ordering = ['-work_date']