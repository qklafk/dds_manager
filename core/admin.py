# Импорты для настройки Django админки
from django.contrib import admin
from django.utils.html import format_html
from .models import Status, Type, Category, Subcategory, CashFlowRecord


@admin.register(Status)
class StatusAdmin(admin.ModelAdmin):
    """
    Админка для управления статусами денежных потоков.
    
    Настраивает отображение, поиск и фильтрацию статусов в Django админке.
    """
    # Поля, отображаемые в списке
    list_display = ['name', 'description', 'created_at']
    # Поля для поиска
    search_fields = ['name', 'description']
    # Фильтры в боковой панели
    list_filter = ['created_at']
    # Сортировка по умолчанию
    ordering = ['name']


@admin.register(Type)
class TypeAdmin(admin.ModelAdmin):
    """
    Админка для управления типами денежных потоков.
    
    Настраивает отображение, поиск и фильтрацию типов в Django админке.
    """
    # Поля, отображаемые в списке
    list_display = ['name', 'description', 'created_at']
    # Поля для поиска
    search_fields = ['name', 'description']
    # Фильтры в боковой панели
    list_filter = ['created_at']
    # Сортировка по умолчанию
    ordering = ['name']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """
    Админка для управления категориями денежных потоков.
    
    Настраивает отображение, поиск и фильтрацию категорий в Django админке.
    """
    # Поля, отображаемые в списке
    list_display = ['name', 'type', 'subcategories_count', 'description', 'created_at']
    # Фильтры в боковой панели
    list_filter = ['type', 'created_at']
    # Поля для поиска
    search_fields = ['name', 'description', 'type__name']
    # Сортировка по умолчанию
    ordering = ['type__name', 'name']
    
    # Кастомные действия
    actions = []
    
    def subcategories_count(self, obj):
        """Показывает количество подкатегорий для категории"""
        count = obj.subcategories.count()
        if count == 1:
            return f"{count} подкатегория"
        elif count in [2, 3, 4]:
            return f"{count} подкатегории"
        else:
            return f"{count} подкатегорий"
    subcategories_count.short_description = 'Подкатегории'
    


@admin.register(Subcategory)
class SubcategoryAdmin(admin.ModelAdmin):
    """
    Админка для управления подкатегориями денежных потоков.
    
    Настраивает отображение, поиск и фильтрацию подкатегорий в Django админке.
    Включает отображение родительской категории для лучшей навигации.
    """
    # Поля, отображаемые в списке
    list_display = ['name', 'category_with_type', 'description', 'created_at']
    # Фильтры в боковой панели
    list_filter = ['category', 'category__type', 'created_at']
    # Поля для поиска (включая поиск по родительской категории)
    search_fields = ['name', 'description', 'category__name', 'category__type__name']
    # Сортировка по категории, затем по названию
    ordering = ['category__name', 'name']
    
    def category_with_type(self, obj):
        """Отображение категории с её типом"""
        return f"{obj.category.name} ({obj.category.type.name})"
    category_with_type.short_description = 'Категория (Тип)'
    category_with_type.admin_order_field = 'category__name'


@admin.register(CashFlowRecord)
class CashFlowRecordAdmin(admin.ModelAdmin):
    """
    Админка для управления записями денежного потока.
    
    Настраивает продвинутое отображение, поиск и фильтрацию записей ДДС.
    Включает кастомные методы для красивого отображения сумм и комментариев.
    """
    # Поля, отображаемые в списке записей
    list_display = ['date', 'status', 'type', 'category_with_type', 'subcategory', 'amount_display', 'comment_short', 'created_at']
    
    # Фильтры в боковой панели для быстрой навигации
    list_filter = ['status', 'type', 'category__type', 'category', 'subcategory', 'date', 'created_at']
    
    # Поля для поиска по всем связанным моделям
    search_fields = ['comment', 'amount', 'status__name', 'type__name', 'category__name', 'subcategory__name']
    
    # Иерархия по дате для быстрого перехода
    date_hierarchy = 'date'
    
    # Сортировка: сначала новые записи
    ordering = ['-date', '-created_at']
    
    # Количество записей на страницу
    list_per_page = 25
    
    # Группировка полей в форме редактирования
    fieldsets = (
        ('Основная информация', {
            'fields': ('date', 'status', 'type', 'category', 'subcategory')
        }),
        ('Финансовые детали', {
            'fields': ('amount', 'comment')
        }),
    )
    
    # Кастомные действия
    actions = []
    
    def category_with_type(self, obj):
        """
        Отображение категории с указанием её типа.
        
        Показывает категорию и её тип для лучшего понимания связей.
        """
        return f"{obj.category.name} ({obj.category.type.name})"
    category_with_type.short_description = 'Категория (Тип)'
    category_with_type.admin_order_field = 'category__name'
    
    def amount_display(self, obj):
        """
        Кастомное отображение суммы с форматированием.
        
        Показывает сумму в рублях с разделителями тысяч для лучшей читаемости.
        """
        return f"{obj.amount:,.2f} руб."
    amount_display.short_description = 'Сумма'
    amount_display.admin_order_field = 'amount'
    
    def comment_short(self, obj):
        """
        Кастомное отображение комментария с обрезкой.
        
        Показывает только первые 50 символов комментария с многоточием,
        чтобы не загромождать список записей.
        """
        return obj.comment[:50] + '...' if len(obj.comment) > 50 else obj.comment
    comment_short.short_description = 'Комментарий'
