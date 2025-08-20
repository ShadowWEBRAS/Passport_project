from django.urls import path
from . import views

app_name = 'passports'

urlpatterns = [
    path('create/', views.create_passport, name='create_passport'),
    path('list/', views.passport_list, name='passport_list'),
    path('search/', views.passport_search, name='search'),
    path('view/<int:pk>/', views.view_passport, name='view_passport'),
    path('edit/<int:pk>/', views.edit_passport, name='edit_passport'),
    path('delete/<int:pk>/', views.delete_passport, name='delete_passport'),
]