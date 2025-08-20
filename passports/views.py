from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden
from django.db import models
from django.core.paginator import Paginator
from .models import EquipmentPassport
from .forms import PassportForm


@login_required
def create_passport(request):
    if request.method == 'POST':
        form = PassportForm(request.POST, request.FILES)
        if form.is_valid():
            passport = form.save(commit=False)
            passport.created_by = request.user
            passport.save()
            messages.success(request, 'Паспорт успешно создан!')
            return redirect('passports:view_passport', pk=passport.pk)
    else:
        form = PassportForm()
    return render(request, 'passports/create_passport.html', {'form': form})


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
            models.Q(equipment_type__name__icontains=search_query)
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
            models.Q(equipment_type__name__icontains=keywords)
        )
    if status:
        passports = passports.filter(status=status)

    equipment_types = EquipmentType.objects.all()

    return render(request, 'passports/passport_search.html', {
        'passports': passports,
        'result_count': passports.count(),
        'equipment_types': equipment_types
    })


@login_required
def view_passport(request, pk):
    passport = get_object_or_404(EquipmentPassport, pk=pk)

    if not (request.user.is_superuser or request.user.is_staff or passport.created_by == request.user):
        return HttpResponseForbidden("У вас нет прав для просмотра этого паспорта")

    return render(request, 'passports/view_passport.html', {'passport': passport})


@login_required
def edit_passport(request, pk):
    passport = get_object_or_404(EquipmentPassport, pk=pk)

    if not (request.user.is_superuser or request.user.is_staff or passport.created_by == request.user):
        return HttpResponseForbidden("У вас нет прав для редактирования этого паспорта")

    if request.method == 'POST':
        form = PassportForm(request.POST, request.FILES, instance=passport)
        if form.is_valid():
            form.save()
            messages.success(request, 'Паспорт успешно обновлен!')
            return redirect('passports:view_passport', pk=pk)
    else:
        form = PassportForm(instance=passport)

    return render(request, 'passports/edit_passport.html', {
        'form': form,
        'passport': passport
    })


@login_required
def delete_passport(request, pk):
    passport = get_object_or_404(EquipmentPassport, pk=pk)

    if not (request.user.is_superuser or request.user.is_staff or passport.created_by == request.user):
        return JsonResponse({'status': 'forbidden'}, status=403)

    if request.method == 'DELETE':
        passport.delete()
        return JsonResponse({'status': 'success'})

    return JsonResponse({'status': 'error'}, status=400)
