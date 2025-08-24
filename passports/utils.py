import json
import yaml
import os
from django.conf import settings
from datetime import datetime


def save_passport_to_file(passport_instance):
    """Сохраняет паспорт в файл"""
    file_path = passport_instance.get_passport_file_path()

    passport_data = {
        'id': str(passport_instance.id),
        'name': passport_instance.name,
        'equipment_type': passport_instance.equipment_type.name if passport_instance.equipment_type else None,
        'serial_number': passport_instance.serial_number,
        'inventory_number': passport_instance.inventory_number,
        'production_date': passport_instance.production_date.isoformat() if passport_instance.production_date else None,
        'commissioning_date': passport_instance.commissioning_date.isoformat() if passport_instance.commissioning_date else None,
        'description': passport_instance.description,
        'location': passport_instance.location,
        'responsible_person': passport_instance.responsible_person,
        'status': passport_instance.status,
        'last_maintenance': passport_instance.last_maintenance.isoformat() if passport_instance.last_maintenance else None,
        'created_by': passport_instance.created_by.username if passport_instance.created_by else None,
        'created_at': passport_instance.created_at.isoformat(),
        'updated_at': passport_instance.updated_at.isoformat(),
        'custom_fields': passport_instance.custom_fields,
        'maintenance_works': []
    }

    # Добавляем работы по обслуживанию
    for work in passport_instance.maintenance_works.all():
        work_data = {
            'id': str(work.id),
            'work_type': work.work_type,
            'work_date': work.work_date.isoformat(),
            'responsible_person': work.responsible_person,
            'description': work.description,
            'cost': float(work.cost) if work.cost else None,
            'materials_used': work.materials_used,
            'created_by': work.created_by.username if work.created_by else None,
            'created_at': work.created_at.isoformat(),
            'custom_fields': work.custom_fields
        }
        passport_data['maintenance_works'].append(work_data)

    # Сохраняем в JSON
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(passport_data, f, ensure_ascii=False, indent=2)

    return file_path


def load_passport_from_file(passport_id):
    """Загружает паспорт из файла"""
    file_path = os.path.join(settings.PASSPORTS_DIR, f"{passport_id}.json")

    if not os.path.exists(file_path):
        return None

    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def delete_passport_file(passport_id):
    """Удаляет файл паспорта"""
    file_path = os.path.join(settings.PASSPORTS_DIR, f"{passport_id}.json")

    if os.path.exists(file_path):
        os.remove(file_path)
        return True
    return False


def get_passport_history(passport_id):
    """Получает историю изменений паспорта"""
    history_file = os.path.join(settings.PASSPORTS_DIR, f"{passport_id}_history.json")

    if os.path.exists(history_file):
        with open(history_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def add_passport_history_entry(passport_instance, user, changed_fields):
    """Добавляет запись в историю изменений"""
    history_file = os.path.join(settings.PASSPORTS_DIR, f"{passport_instance.id}_history.json")

    history_entry = {
        'timestamp': datetime.now().isoformat(),
        'user': user.username,
        'changed_fields': changed_fields
    }

    history = get_passport_history(passport_instance.id)
    history.append(history_entry)

    with open(history_file, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def get_changed_fields(initial_data, new_data):
    """Сравнивает начальные и новые данные, возвращает список измененных полей."""
    changed_fields = []
    for field in initial_data:
        if initial_data[field] != new_data.get(field):
            changed_fields.append(field)
    return changed_fields