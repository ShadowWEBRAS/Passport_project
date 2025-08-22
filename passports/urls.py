from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .api_views import EquipmentPassportViewSet, MaintenanceWorkViewSet

app_name = 'passports'

router = DefaultRouter()
router.register(r'api/passports', EquipmentPassportViewSet)
router.register(r'api/maintenance-works', MaintenanceWorkViewSet)

urlpatterns = [
    path('create/', views.create_passport, name='create_passport'),
    path('list/', views.passport_list, name='passport_list'),
    path('search/', views.passport_search, name='search'),
    path('view/<uuid:pk>/', views.view_passport, name='view_passport'),
    path('edit/<uuid:pk>/', views.edit_passport, name='edit_passport'),
    path('delete/<uuid:pk>/', views.delete_passport, name='delete_passport'),
    path('add-work/<uuid:pk>/', views.add_maintenance_work, name='add_work'),
    path('works/<uuid:pk>/', views.maintenance_work_list, name='work_list'),
    path('', include(router.urls)),
]