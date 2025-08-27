import json
import yaml
import os
import shutil
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

    # Создаем директорию, если она не существует
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    # Сохраняем в JSON
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(passport_data, f, ensure_ascii=False, indent=2)

    return file_path


def load_passport_from_file(passport_id):
    """Загружает паспорт из файла"""
    file_path = os.path.join(settings.PASSPORTS_DIR, f"{passport_id}.json")

    if not os.path.exists(file_path):
        return None

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return None


def delete_passport_file(passport_id):
    """Удаляет файл паспорта"""
    file_path = os.path.join(settings.PASSPORTS_DIR, f"{passport_id}.json")
    history_file = os.path.join(settings.PASSPORTS_DIR, f"{passport_id}_history.json")

    deleted_files = 0

    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            deleted_files += 1
        except OSError:
            pass

    if os.path.exists(history_file):
        try:
            os.remove(history_file)
            deleted_files += 1
        except OSError:
            pass

    return deleted_files > 0


def delete_multiple_passport_files(passport_ids):
    """Удаляет файлы нескольких паспортов"""
    success_count = 0
    error_count = 0

    for passport_id in passport_ids:
        if delete_passport_file(passport_id):
            success_count += 1
        else:
            error_count += 1

    return success_count, error_count


def get_passport_history(passport_id):
    """Получает историю изменений паспорта"""
    history_file = os.path.join(settings.PASSPORTS_DIR, f"{passport_id}_history.json")

    if os.path.exists(history_file):
        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []
    return []



def get_changed_fields(initial_data, new_data):
    """Сравнивает начальные и новые данные, возвращает список измененных полей."""
    changed_fields = []
    for field in initial_data:
        if initial_data[field] != new_data.get(field):
            changed_fields.append(field)
    return changed_fields


def cleanup_orphaned_files():
    """Очищает файлы, для которых нет соответствующих записей в базе данных"""
    from .models import EquipmentPassport
    import os

    existing_passport_ids = set(str(passport.id) for passport in EquipmentPassport.objects.all())
    files_in_directory = set()

    if os.path.exists(settings.PASSPORTS_DIR):
        for filename in os.listdir(settings.PASSPORTS_DIR):
            if filename.endswith('.json'):
                # Извлекаем UUID из имени файла
                file_id = filename.split('.')[0]
                if '_history' in file_id:
                    file_id = file_id.replace('_history', '')
                files_in_directory.add(file_id)

    orphaned_files = files_in_directory - existing_passport_ids
    deleted_count = 0

    for orphan_id in orphaned_files:
        if delete_passport_file(orphan_id):
            deleted_count += 1

    return deleted_count


def add_passport_history_entry(passport_instance, user, changed_fields):
    """Добавляет запись в историю изменений"""
    history_file = os.path.join(settings.PASSPORTS_DIR, f"{passport_instance.id}_history.json")

    history_entry = {
        'timestamp': datetime.now().isoformat(),
        'user': user.username,
        'changed_fields': changed_fields
    }

    # Загружаем существующую историю
    history = []
    if os.path.exists(history_file):
        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            history = []

    # Добавляем новую запись
    history.append(history_entry)

    # Сохраняем обновленную историю
    os.makedirs(os.path.dirname(history_file), exist_ok=True)
    with open(history_file, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)