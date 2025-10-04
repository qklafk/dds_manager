# Импорты для настройки URL маршрутов
from django.urls import path
from . import views

# Имя приложения для namespace в URL'ах
app_name = 'core'

# URL маршруты приложения
urlpatterns = [
    # Основные страницы приложения
    path('', views.index, name='index'),  # Главная страница с записями ДДС
    path('directory/', views.directory_management, name='directory_management'),  # Управление справочниками
    
    # CRUD операции для записей денежного потока
    path('record/create/', views.record_create, name='record_create'),  # Создание записи
    path('record/<int:pk>/edit/', views.record_edit, name='record_edit'),  # Редактирование записи
    path('record/<int:pk>/delete/', views.record_delete, name='record_delete'),  # Удаление записи
    
    # CRUD операции для статусов
    path('status/create/', views.status_create, name='status_create'),  # Создание статуса
    path('status/<int:pk>/edit/', views.status_edit, name='status_edit'),  # Редактирование статуса
    path('status/<int:pk>/delete/', views.status_delete, name='status_delete'),  # Удаление статуса
    
    # CRUD операции для типов
    path('type/create/', views.type_create, name='type_create'),  # Создание типа
    path('type/<int:pk>/edit/', views.type_edit, name='type_edit'),  # Редактирование типа
    path('type/<int:pk>/delete/', views.type_delete, name='type_delete'),  # Удаление типа
    
    # CRUD операции для категорий
    path('category/create/', views.category_create, name='category_create'),  # Создание категории
    path('category/<int:pk>/edit/', views.category_edit, name='category_edit'),  # Редактирование категории
    path('category/<int:pk>/delete/', views.category_delete, name='category_delete'),  # Удаление категории
    
    # CRUD операции для подкатегорий
    path('subcategory/create/', views.subcategory_create, name='subcategory_create'),  # Создание подкатегории
    path('subcategory/<int:pk>/edit/', views.subcategory_edit, name='subcategory_edit'),  # Редактирование подкатегории
    path('subcategory/<int:pk>/delete/', views.subcategory_delete, name='subcategory_delete'),  # Удаление подкатегории
    
    # AJAX endpoints для динамической фильтрации
    path('api/categories/<int:type_id>/', views.get_categories_by_type, name='get_categories_by_type'),  # Получение категорий по типу
    path('api/subcategories/<int:category_id>/', views.get_subcategories_by_category, name='get_subcategories_by_category'),  # Получение подкатегорий по категории
]
