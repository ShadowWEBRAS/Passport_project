from django.core.management.base import BaseCommand
from passports.models import EquipmentPassport
from passports.utils import get_passport_history
import json


class Command(BaseCommand):
    help = 'Восстанавливает историю изменений паспортов'

    def handle(self, *args, **options):
        for passport in EquipmentPassport.objects.all():
            history = get_passport_history(passport.id)
            self.stdout.write(
                f"Паспорт {passport.name}: {len(history)} записей истории"
            )

            # Показываем первую запись для отладки
            if history:
                self.stdout.write(f"  Первая запись: {json.dumps(history[0], indent=2, ensure_ascii=False)}")