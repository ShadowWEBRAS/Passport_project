from rest_framework import serializers
from .models import EquipmentPassport, MaintenanceWork


class MaintenanceWorkSerializer(serializers.ModelSerializer):
    class Meta:
        model = MaintenanceWork
        fields = '__all__'
        read_only_fields = ['id', 'created_by', 'created_at']


class EquipmentPassportSerializer(serializers.ModelSerializer):
    maintenance_works = MaintenanceWorkSerializer(many=True, read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)

    class Meta:
        model = EquipmentPassport
        fields = '__all__'
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']