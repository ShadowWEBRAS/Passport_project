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
from .utils import save_passport_to_file, load_passport_from_file, delete_passport_file, add_passport_history_entry


def is_admin(user):
    return user.is_superuser or user.is_staff


@login_required
def create_passport(request):
    if request.method == 'POST':
        form = PassportForm(request.POST, request.FILES)
        if form.is_valid():
            passport = form.save(commit=False)
            passport.created_by = request.user

            # Обработка пользовательских полей
            custom_fields = {}
            for key, value in request.POST.items():
                if key.startswith('custom_'):
                    field_name = key.replace('custom_', '')
                    custom_fields[field_name] = value

            passport.custom_fields = custom_fields
            passport.save()

            # Сохраняем в файл
            save_passport_to_file(passport)

            messages.success(request, 'Паспорт успешно создан!')
            return redirect('passports:view_passport', pk=passport.pk)
    else:
        form = PassportForm()

    return render(request, 'passports/create_passport.html', {
        'form': form,
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

    if not (request.user.is_superuser or request.user.is_staff or passport.created_by == request.user):
        return HttpResponseForbidden("У вас нет прав для редактирования этого паспорта")

    if request.method == 'POST':
        form = PassportForm(request.POST, request.FILES, instance=passport)
        if form.is_valid():
            old_data = {field: getattr(passport, field) for field in form.changed_data}

            passport = form.save()

            # Обновляем пользовательские поля
            custom_fields = passport.custom_fields.copy()
            for key, value in request.POST.items():
                if key.startswith('custom_'):
                    field_name = key.replace('custom_', '')
                    custom_fields[field_name] = value

            passport.custom_fields = custom_fields
            passport.save()

            # Сохраняем изменения в файл
            save_passport_to_file(passport)

            # Добавляем запись в историю
            add_passport_history_entry(passport, request.user, form.changed_data)

            messages.success(request, 'Паспорт успешно обновлен!')
            return redirect('passports:view_passport', pk=pk)
    else:
        form = PassportForm(instance=passport)

    return render(request, 'passports/edit_passport.html', {
        'form': form,
        'passport': passport,
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
        works = works.filter(work_date__gte=parse_date(start_date))
    if end_date:
        works = works.filter(work_date__lte=parse_date(end_date))

    return render(request, 'passports/work_list.html', {
        'passport': passport,
        'works': works,
        'work_types': MaintenanceWork.WORK_TYPES
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