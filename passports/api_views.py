from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.shortcuts import get_object_or_404
from .models import EquipmentPassport, MaintenanceWork
from .serializers import EquipmentPassportSerializer, MaintenanceWorkSerializer
from .utils import save_passport_to_file, load_passport_from_file


class EquipmentPassportViewSet(viewsets.ModelViewSet):
    queryset = EquipmentPassport.objects.all()
    serializer_class = EquipmentPassportSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        if self.request.user.is_superuser or self.request.user.is_staff:
            return EquipmentPassport.objects.all()
        return EquipmentPassport.objects.filter(created_by=self.request.user)

    def perform_create(self, serializer):
        passport = serializer.save(created_by=self.request.user)
        save_passport_to_file(passport)

    def perform_update(self, serializer):
        passport = serializer.save()
        save_passport_to_file(passport)

    def perform_destroy(self, instance):
        delete_passport_file(instance.id)
        instance.delete()

    @action(detail=True, methods=['get'])
    def file_data(self, request, pk=None):
        passport = self.get_object()
        file_data = load_passport_from_file(passport.id)
        return Response(file_data)

    @action(detail=True, methods=['get'])
    def maintenance_works(self, request, pk=None):
        passport = self.get_object()
        works = passport.maintenance_works.all()

        # Фильтрация
        work_type = request.query_params.get('work_type')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        if work_type:
            works = works.filter(work_type=work_type)
        if start_date:
            works = works.filter(work_date__gte=start_date)
        if end_date:
            works = works.filter(work_date__lte=end_date)

        serializer = MaintenanceWorkSerializer(works, many=True)
        return Response(serializer.data)


class MaintenanceWorkViewSet(viewsets.ModelViewSet):
    queryset = MaintenanceWork.objects.all()
    serializer_class = MaintenanceWorkSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_superuser or self.request.user.is_staff:
            return MaintenanceWork.objects.all()
        return MaintenanceWork.objects.filter(created_by=self.request.user)

    def perform_create(self, serializer):
        work = serializer.save(created_by=self.request.user)
        save_passport_to_file(work.passport)

    def perform_update(self, serializer):
        work = serializer.save()
        save_passport_to_file(work.passport)

    def perform_destroy(self, instance):
        passport = instance.passport
        instance.delete()
        save_passport_to_file(passport)