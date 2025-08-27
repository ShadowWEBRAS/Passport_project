from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden
from django.db import models
from django.core.paginator import Paginator
from django.utils.dateparse import parse_date
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import EquipmentPassport, MaintenanceWork, EquipmentType
from .forms import PassportForm, MaintenanceWorkForm, CustomFieldForm
from .utils import save_passport_to_file, load_passport_from_file, delete_passport_file, add_passport_history_entry, \
    get_passport_history, delete_multiple_passport_files
import json
import uuid


def is_admin(user):
    return user.is_superuser or user.is_staff


@login_required
def create_passport(request):
    equipment_types = EquipmentType.objects.all()

    if request.method == 'POST':
        form = PassportForm(request.POST, request.FILES)
        if form.is_valid():
            passport = form.save(commit=False)
            passport.created_by = request.user

            # Обработка типа оборудования
            equipment_type_name = request.POST.get('equipment_type_name')
            if equipment_type_name:
                equipment_type, created = EquipmentType.objects.get_or_create(
                    name=equipment_type_name,
                    defaults={'created_by': request.user}
                )
                passport.equipment_type = equipment_type

            # Обработка custom fields
            custom_fields_json = request.POST.get('custom_fields_json', '{}')
            try:
                custom_fields = json.loads(custom_fields_json)
                passport.custom_fields = custom_fields
            except json.JSONDecodeError:
                passport.custom_fields = {}

            passport.save()

            save_passport_to_file(passport)
            messages.success(request, 'Паспорт успешно создан!')
            return redirect('passports:view_passport', pk=passport.pk)
        else:
            print("Form errors:", form.errors)
    else:
        form = PassportForm()

    return render(request, 'passports/create_passport.html', {
        'form': form,
        'equipment_types': equipment_types,
        'custom_field_form': CustomFieldForm()
    })


@login_required
def passport_list(request):
    status_filter = request.GET.get('status', 'all')
    sort = request.GET.get('sort', '-created_at')
    search_query = request.GET.get('q', '')

    if request.user.is_superuser or request.user.is_staff:
        passports = EquipmentPassport.objects.all()
    else:
        passports = EquipmentPassport.objects.filter(created_by=request.user)

    if status_filter != 'all':
        passports = passports.filter(status=status_filter)

    if search_query:
        passports = passports.filter(
            models.Q(name__icontains=search_query) |
            models.Q(serial_number__icontains=search_query) |
            models.Q(inventory_number__icontains=search_query) |
            models.Q(description__icontains=search_query) |
            models.Q(location__icontains=search_query)
        )

    if sort == 'oldest':
        passports = passports.order_by('created_at')
    elif sort == 'name':
        passports = passports.order_by('name')
    else:
        passports = passports.order_by('-created_at')

    paginator = Paginator(passports, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'passports/passport_list.html', {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'sort': sort,
        'search_query': search_query
    })


@login_required
def passport_search(request):
    name = request.GET.get('name', '')
    serial_number = request.GET.get('serial_number', '')
    inventory_number = request.GET.get('inventory_number', '')
    equipment_type = request.GET.get('equipment_type', '')
    commissioning_date = request.GET.get('commissioning_date', '')
    location = request.GET.get('location', '')
    keywords = request.GET.get('keywords', '')
    status = request.GET.get('status', '')

    passports = EquipmentPassport.objects.all()

    if not (request.user.is_superuser or request.user.is_staff):
        passports = passports.filter(created_by=request.user)

    if name:
        passports = passports.filter(name__icontains=name)
    if serial_number:
        passports = passports.filter(serial_number__icontains=serial_number)
    if inventory_number:
        passports = passports.filter(inventory_number__icontains=inventory_number)
    if equipment_type:
        passports = passports.filter(equipment_type__name__icontains=equipment_type)
    if commissioning_date:
        passports = passports.filter(commissioning_date=commissioning_date)
    if location:
        passports = passports.filter(location__icontains=location)
    if keywords:
        passports = passports.filter(
            models.Q(name__icontains=keywords) |
            models.Q(description__icontains=keywords) |
            models.Q(serial_number__icontains=keywords) |
            models.Q(inventory_number__icontains=keywords) |
            models.Q(location__icontains=keywords)
        )
    if status:
        passports = passports.filter(status=status)

    return render(request, 'passports/passport_search.html', {
        'passports': passports,
        'result_count': passports.count(),
        'search_params': request.GET
    })


@login_required
def view_passport(request, pk):
    passport = get_object_or_404(EquipmentPassport, pk=pk)

    if not (request.user.is_superuser or request.user.is_staff or passport.created_by == request.user):
        return HttpResponseForbidden("У вас нет прав для просмотра этого паспорта")

    # Загружаем данные из файла
    file_data = load_passport_from_file(passport.id)

    return render(request, 'passports/view_passport.html', {
        'passport': passport,
        'file_data': file_data
    })


@login_required
def edit_passport(request, pk):
    passport = get_object_or_404(EquipmentPassport, pk=pk)
    equipment_types = EquipmentType.objects.all()

    if not (request.user.is_superuser or request.user.is_staff or passport.created_by == request.user):
        return HttpResponseForbidden("У вас нет прав для редактирования этого паспорта")

    if request.method == 'POST':
        # Сохраняем старые значения, преобразуя даты в строки для сравнения
        old_data = {}
        for field in ['name', 'serial_number', 'inventory_number', 'production_date',
                      'commissioning_date', 'description', 'location', 'responsible_person',
                      'status', 'last_maintenance']:
            value = getattr(passport, field)
            if hasattr(value, 'isoformat'):
                # Преобразуем даты в строки для корректного сравнения
                old_data[field] = value.isoformat() if value else None
            else:
                old_data[field] = value

        form = PassportForm(request.POST, request.FILES, instance=passport)

        if form.is_valid():
            passport = form.save(commit=False)

            # Обрабатываем тип оборудования
            equipment_type_name = request.POST.get('equipment_type_name')
            if equipment_type_name:
                equipment_type, created = EquipmentType.objects.get_or_create(
                    name=equipment_type_name,
                    defaults={'created_by': request.user}
                )
                passport.equipment_type = equipment_type

            # Обработка custom fields
            custom_fields_json = request.POST.get('custom_fields_json', '{}')
            try:
                custom_fields = json.loads(custom_fields_json)
                passport.custom_fields = custom_fields
            except json.JSONDecodeError:
                passport.custom_fields = {}

            # Определяем измененные поля
            changed_fields = {}
            for field in form.changed_data:
                if field != 'custom_fields_json' and field != 'equipment_type_name':
                    new_value = getattr(passport, field)
                    if hasattr(new_value, 'isoformat'):
                        # Преобразуем новые значения дат в строки для сравнения
                        new_value = new_value.isoformat() if new_value else None

                    # Сравниваем строковые представления
                    old_value_str = old_data.get(field)
                    new_value_str = str(new_value) if new_value is not None else None

                    if str(old_value_str) != str(new_value_str):
                        changed_fields[field] = {
                            'old': old_value_str,
                            'new': new_value_str
                        }

            # Сохраняем историю изменений
            if changed_fields:
                add_passport_history_entry(passport, request.user, changed_fields)

            passport.save()

            # Сохраняем изменения в файл
            save_passport_to_file(passport)

            messages.success(request, 'Паспорт успешно обновлен!')
            return redirect('passports:view_passport', pk=pk)
        else:
            print("Form errors:", form.errors)
            messages.error(request, 'Ошибка при сохранении. Проверьте данные.')
    else:
        form = PassportForm(instance=passport)
        # Устанавливаем начальное значение для поля типа оборудования
        if passport.equipment_type:
            form.fields['equipment_type_name'].initial = passport.equipment_type.name

    return render(request, 'passports/edit_passport.html', {
        'form': form,
        'passport': passport,
        'equipment_types': equipment_types,
        'custom_field_form': CustomFieldForm()
    })


@login_required
def delete_passport(request, pk):
    passport = get_object_or_404(EquipmentPassport, pk=pk)

    if not (request.user.is_superuser or request.user.is_staff or passport.created_by == request.user):
        return JsonResponse({'status': 'forbidden'}, status=403)

    if request.method == 'DELETE':
        # Удаляем файл паспорта
        delete_passport_file(passport.id)

        # Удаляем запись из БД
        passport.delete()

        return JsonResponse({'status': 'success'})

    return JsonResponse({'status': 'error'}, status=400)


@login_required
def delete_multiple_passports(request):
    """Массовое удаление паспортов через API"""
    if not (request.user.is_superuser or request.user.is_staff):
        return JsonResponse({'status': 'forbidden'}, status=403)

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            passport_ids = data.get('passport_ids', [])

            # Валидация UUID
            valid_ids = []
            for passport_id in passport_ids:
                try:
                    uuid.UUID(passport_id)
                    valid_ids.append(passport_id)
                except ValueError:
                    pass

            if not valid_ids:
                return JsonResponse({'status': 'error', 'message': 'Нет валидных ID паспортов'}, status=400)

            # Получаем паспорта для удаления
            passports = EquipmentPassport.objects.filter(id__in=valid_ids)

            # Удаляем файлы
            file_success, file_errors = delete_multiple_passport_files(valid_ids)

            # Удаляем записи из БД
            db_count = passports.count()
            passports.delete()

            return JsonResponse({
                'status': 'success',
                'message': f'Удалено {db_count} паспортов из БД и {file_success} файлов',
                'db_deleted': db_count,
                'files_deleted': file_success,
                'file_errors': file_errors
            })

        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Неверный формат JSON'}, status=400)

    return JsonResponse({'status': 'error', 'message': 'Метод не разрешен'}, status=405)


@login_required
def add_maintenance_work(request, pk):
    passport = get_object_or_404(EquipmentPassport, pk=pk)

    if not (request.user.is_superuser or request.user.is_staff or passport.created_by == request.user):
        return HttpResponseForbidden("У вас нет прав для добавления работ")

    if request.method == 'POST':
        form = MaintenanceWorkForm(request.POST)
        if form.is_valid():
            work = form.save(commit=False)
            work.passport = passport
            work.created_by = request.user
            work.save()

            # Обновляем файл паспорта
            save_passport_to_file(passport)

            messages.success(request, 'Работа успешно добавлена!')
            return redirect('passports:view_passport', pk=pk)
    else:
        form = MaintenanceWorkForm()

    return render(request, 'passports/add_work.html', {
        'form': form,
        'passport': passport
    })


@login_required
def maintenance_work_list(request, pk):
    passport = get_object_or_404(EquipmentPassport, pk=pk)

    if not (request.user.is_superuser or request.user.is_staff or passport.created_by == request.user):
        return HttpResponseForbidden("У вас нет прав для просмотра работ")

    works = passport.maintenance_works.all()

    # Фильтрация по типу работы
    work_type = request.GET.get('work_type')
    if work_type:
        works = works.filter(work_type=work_type)

    # Фильтрация по дате
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    if start_date:
        try:
            works = works.filter(work_date__gte=parse_date(start_date))
        except (ValueError, TypeError):
            pass
    if end_date:
        try:
            works = works.filter(work_date__lte=parse_date(end_date))
        except (ValueError, TypeError):
            pass

    return render(request, 'passports/work_list.html', {
        'passport': passport,
        'works': works,
        'work_types': MaintenanceWork.WORK_TYPES,
        'current_filters': request.GET.dict()
    })


@login_required
def passport_history(request, pk):
    passport = get_object_or_404(EquipmentPassport, pk=pk)

    if not (request.user.is_superuser or request.user.is_staff or passport.created_by == request.user):
        return HttpResponseForbidden("У вас нет прав для просмотра истории")

    history = get_passport_history(passport.id)

    return render(request, 'passports/passport_history.html', {
        'passport': passport,
        'history': history
    })


# API Views
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_passport_list(request):
    if request.user.is_superuser or request.user.is_staff:
        passports = EquipmentPassport.objects.all()
    else:
        passports = EquipmentPassport.objects.filter(created_by=request.user)

    data = []
    for passport in passports:
        data.append({
            'id': str(passport.id),
            'name': passport.name,
            'serial_number': passport.serial_number,
            'status': passport.status,
            'created_at': passport.created_at
        })

    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_passport_detail(request, pk):
    passport = get_object_or_404(EquipmentPassport, pk=pk)

    if not (request.user.is_superuser or request.user.is_staff or passport.created_by == request.user):
        return Response({'error': 'Permission denied'}, status=403)

    file_data = load_passport_from_file(passport.id)
    return Response(file_data)