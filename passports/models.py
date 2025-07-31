from django.db import models
from django.contrib.auth.models import User

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

    equipment_type = models.ForeignKey(
        EquipmentType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Тип оборудования'
    )
    name = models.CharField('Наименование', max_length=255)
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

    def __str__(self):
        return f"{self.name} ({self.serial_number})"