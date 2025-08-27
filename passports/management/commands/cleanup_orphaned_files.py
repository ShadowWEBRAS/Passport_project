from django.core.management.base import BaseCommand
from django.conf import settings
import os
import json


class Command(BaseCommand):
    help = 'Очищает файлы паспортов, для которых нет записей в базе данных'

    def handle(self, *args, **options):
        from passports.models import EquipmentPassport

        existing_passport_ids = set(str(passport.id) for passport in EquipmentPassport.objects.all())
        files_in_directory = set()
        deleted_count = 0

        if os.path.exists(settings.PASSPORTS_DIR):
            for filename in os.listdir(settings.PASSPORTS_DIR):
                if filename.endswith('.json'):
                    # Извлекаем UUID из имени файла
                    file_id = filename.split('.')[0]
                    if '_history' in file_id:
                        file_id = file_id.replace('_history', '')
                    files_in_directory.add(file_id)

        orphaned_files = files_in_directory - existing_passport_ids

        for orphan_id in orphaned_files:
            file_path = os.path.join(settings.PASSPORTS_DIR, f"{orphan_id}.json")
            history_file = os.path.join(settings.PASSPORTS_DIR, f"{orphan_id}_history.json")

            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                if os.path.exists(history_file):
                    os.remove(history_file)
                deleted_count += 1
            except OSError as e:
                self.stdout.write(
                    self.style.ERROR(f'Ошибка при удалении файла {orphan_id}: {e}')
                )

        if deleted_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f'Удалено {deleted_count} orphaned файлов')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('Orphaned файлы не найдены')
            )