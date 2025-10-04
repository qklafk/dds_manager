from django.test import TestCase, Client, TransactionTestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone
from decimal import Decimal
import json
from datetime import date, timedelta
from .models import Status, Type, Category, Subcategory, CashFlowRecord
from .forms import CashFlowRecordForm, CashFlowFilterForm


# ============================================================================
# МОДЕЛИ - ДЕТАЛЬНЫЕ ТЕСТЫ
# ============================================================================

class StatusModelTest(TestCase):
    """Тесты для модели Status"""
    
    def test_status_creation(self):
        """Тест создания статуса"""
        status = Status.objects.create(
            name="Бизнес",
            description="Бизнес-транзакции"
        )
        self.assertEqual(status.name, "Бизнес")
        self.assertEqual(status.description, "Бизнес-транзакции")
        self.assertIsNotNone(status.created_at)
        self.assertIsNotNone(status.updated_at)
    
    def test_status_str_representation(self):
        """Тест строкового представления статуса"""
        status, _ = Status.objects.get_or_create(name="Личное")
        self.assertEqual(str(status), "Личное")
    
    def test_status_unique_name(self):
        """Тест уникальности имени статуса"""
        Status.objects.create(name="Бизнес")
        with self.assertRaises(IntegrityError):
            Status.objects.create(name="Бизнес")


class TypeModelTest(TestCase):
    """Тесты для модели Type"""
    
    def test_type_creation(self):
        """Тест создания типа"""
        type_obj, created = Type.objects.get_or_create(
            name="Пополнение",
            defaults={"description": "Поступление денег"}
        )
        self.assertEqual(type_obj.name, "Пополнение")
        self.assertEqual(type_obj.description, "Поступление денег")
    
    def test_type_str_representation(self):
        """Тест строкового представления типа"""
        type_obj, _ = Type.objects.get_or_create(name="Списание")
        self.assertEqual(str(type_obj), "Списание")


class CategoryModelTest(TestCase):
    """Тесты для модели Category"""
    
    def setUp(self):
        self.type, _ = Type.objects.get_or_create(name="Списание", defaults={"description": "Расход денег"})
    
    def test_category_creation(self):
        """Тест создания категории"""
        category = Category.objects.create(
            name="Инфраструктура",
            type=self.type,
            description="Затраты на инфраструктуру"
        )
        self.assertEqual(category.name, "Инфраструктура")
        self.assertEqual(category.type, self.type)
        self.assertEqual(category.description, "Затраты на инфраструктуру")
    
    def test_category_str_representation(self):
        """Тест строкового представления категории"""
        category, _ = Category.objects.get_or_create(name="Маркетинг", defaults={"type": self.type})
        self.assertEqual(str(category), "Маркетинг")
    
    def test_category_unique_name(self):
        """Тест уникальности имени категории"""
        Category.objects.create(name="Инфраструктура", type=self.type)
        with self.assertRaises(IntegrityError):
            Category.objects.create(name="Инфраструктура", type=self.type)


class SubcategoryModelTest(TestCase):
    """Тесты для модели Subcategory"""
    
    def setUp(self):
        self.type, _ = Type.objects.get_or_create(name="Списание")
        self.category, _ = Category.objects.get_or_create(name="Инфраструктура", defaults={"type": self.type})
    
    def test_subcategory_creation(self):
        """Тест создания подкатегории"""
        subcategory = Subcategory.objects.create(
            name="VPS",
            category=self.category,
            description="Затраты на виртуальный сервер"
        )
        self.assertEqual(subcategory.name, "VPS")
        self.assertEqual(subcategory.category, self.category)
        self.assertEqual(subcategory.description, "Затраты на виртуальный сервер")
    
    def test_subcategory_str_representation(self):
        """Тест строкового представления подкатегории"""
        subcategory, _ = Subcategory.objects.get_or_create(name="Proxy", defaults={"category": self.category})
        expected = f"Proxy ({self.category.name})"
        self.assertEqual(str(subcategory), expected)
    
    def test_subcategory_unique_together(self):
        """Тест уникальности комбинации имя+категория"""
        Subcategory.objects.create(name="VPS", category=self.category)
        # Можно создать VPS в другой категории
        other_category, _ = Category.objects.get_or_create(name="Маркетинг", defaults={"type": self.type})
        Subcategory.objects.create(name="VPS", category=other_category)
        
        # Но нельзя создать VPS в той же категории
        with self.assertRaises(IntegrityError):
            Subcategory.objects.create(name="VPS", category=self.category)


class CashFlowRecordModelTest(TestCase):
    """Тесты для модели CashFlowRecord"""
    
    def setUp(self):
        self.status, _ = Status.objects.get_or_create(name="Бизнес", defaults={"description": "Бизнес-транзакции"})
        self.type, _ = Type.objects.get_or_create(name="Списание", defaults={"description": "Расход денег"})
        self.category = Category.objects.create(
            name="Инфраструктура", 
            type=self.type, 
            description="Затраты на инфраструктуру"
        )
        self.subcategory = Subcategory.objects.create(
            name="VPS", 
            category=self.category, 
            description="Затраты на виртуальный сервер"
        )

    def test_cash_flow_record_creation(self):
        """Тест создания записи денежного потока"""
        record = CashFlowRecord.objects.create(
            date=date.today(),
            status=self.status,
            type=self.type,
            category=self.category,
            subcategory=self.subcategory,
            amount=Decimal('1000.00'),
            comment="Тестовая транзакция"
        )
        
        self.assertEqual(record.status, self.status)
        self.assertEqual(record.type, self.type)
        self.assertEqual(record.category, self.category)
        self.assertEqual(record.subcategory, self.subcategory)
        self.assertEqual(record.amount, Decimal('1000.00'))
        self.assertEqual(record.comment, "Тестовая транзакция")
        self.assertIsNotNone(record.created_at)
        self.assertIsNotNone(record.updated_at)

    def test_cash_flow_record_str_representation(self):
        """Тест строкового представления записи"""
        record = CashFlowRecord.objects.create(
            date=date(2025, 10, 4),
            status=self.status,
            type=self.type,
            category=self.category,
            subcategory=self.subcategory,
            amount=Decimal('1500.50')
        )
        expected = "2025-10-04 - Списание - 1500.50 руб."
        self.assertEqual(str(record), expected)

    def test_cash_flow_record_default_date(self):
        """Тест значения даты по умолчанию"""
        record = CashFlowRecord.objects.create(
            status=self.status,
            type=self.type,
            category=self.category,
            subcategory=self.subcategory,
            amount=Decimal('1000.00')
        )
        # Дата должна быть установлена автоматически
        self.assertIsNotNone(record.date)

    def test_cash_flow_record_amount_validation(self):
        """Тест валидации суммы"""
        # Сумма должна быть больше 0
        with self.assertRaises(ValidationError):
            record = CashFlowRecord(
                status=self.status,
                type=self.type,
                category=self.category,
                subcategory=self.subcategory,
                amount=Decimal('0.00')
            )
            record.full_clean()

    def test_business_rules_validation_subcategory_category_mismatch(self):
        """Тест валидации: подкатегория должна принадлежать категории"""
        other_type, _ = Type.objects.get_or_create(name="Пополнение", defaults={"description": "Поступление денег"})
        other_category = Category.objects.create(
            name="Зарплата", 
            type=other_type, 
            description="Доходы от зарплаты"
        )
        other_subcategory = Subcategory.objects.create(
            name="Зарплата", 
            category=other_category
        )
        
        with self.assertRaises(ValidationError):
            record = CashFlowRecord(
                status=self.status,
                type=self.type,
                category=self.category,  # Инфраструктура
                subcategory=other_subcategory,  # Подкатегория от другой категории
                amount=Decimal('1000.00')
            )
            record.clean()

    def test_business_rules_validation_category_type_mismatch(self):
        """Тест валидации: категория должна принадлежать типу"""
        other_type, _ = Type.objects.get_or_create(name="Пополнение", defaults={"description": "Поступление денег"})
        other_category = Category.objects.create(
            name="Зарплата", 
            type=other_type, 
            description="Доходы от зарплаты"
        )
        
        with self.assertRaises(ValidationError):
            record = CashFlowRecord(
                status=self.status,
                type=self.type,  # Списание
                category=other_category,  # Категория от типа "Пополнение"
                subcategory=self.subcategory,
                amount=Decimal('1000.00')
            )
            record.clean()

    def test_cash_flow_record_ordering(self):
        """Тест сортировки записей"""
        # Создаем записи с разными датами
        record1 = CashFlowRecord.objects.create(
            date=date(2025, 10, 1),
            status=self.status,
            type=self.type,
            category=self.category,
            subcategory=self.subcategory,
            amount=Decimal('1000.00')
        )
        
        record2 = CashFlowRecord.objects.create(
            date=date(2025, 10, 3),
            status=self.status,
            type=self.type,
            category=self.category,
            subcategory=self.subcategory,
            amount=Decimal('2000.00')
        )
        
        records = CashFlowRecord.objects.all()
        # Должны быть отсортированы по убыванию даты
        self.assertEqual(records[0], record2)
        self.assertEqual(records[1], record1)


# ============================================================================
# ПРЕДСТАВЛЕНИЯ - ДЕТАЛЬНЫЕ ТЕСТЫ
# ============================================================================

class ViewTest(TestCase):
    """Тесты для всех представлений"""
    
    def setUp(self):
        self.client = Client()
        
        # Создаем тестовые данные
        self.status, _ = Status.objects.get_or_create(name="Бизнес", defaults={"description": "Бизнес-транзакции"})
        self.type, _ = Type.objects.get_or_create(name="Списание", defaults={"description": "Расход денег"})
        self.category, _ = Category.objects.get_or_create(
            name="Инфраструктура", 
            defaults={"type": self.type, "description": "Затраты на инфраструктуру"}
        )
        self.subcategory, _ = Subcategory.objects.get_or_create(
            name="VPS", 
            defaults={"category": self.category, "description": "Затраты на виртуальный сервер"}
        )
        
        # Создаем тестовую запись
        self.record = CashFlowRecord.objects.create(
            date=date.today(),
            status=self.status,
            type=self.type,
            category=self.category,
            subcategory=self.subcategory,
            amount=Decimal('1000.00'),
            comment="Тестовая запись"
        )

    def test_index_view_get(self):
        """Тест главной страницы (GET)"""
        response = self.client.get(reverse('core:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Записи денежного потока')
        self.assertContains(response, 'Фильтры')
        self.assertContains(response, 'Новая запись')

    def test_index_view_with_filters(self):
        """Тест главной страницы с фильтрами"""
        response = self.client.get(reverse('core:index'), {
            'date_from': '2025-10-01',
            'date_to': '2025-10-31',
            'status': self.status.id,
            'type': self.type.id
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Записи денежного потока')

    def test_index_view_invalid_date_filter(self):
        """Тест главной страницы с некорректными датами"""
        response = self.client.get(reverse('core:index'), {
            'date_from': '2025-10-31',
            'date_to': '2025-10-01'  # Дата "с" больше даты "по"
        })
        self.assertEqual(response.status_code, 200)
        # Должна отображаться ошибка валидации
        self.assertContains(response, 'Дата')

    def test_record_create_view_get(self):
        """Тест страницы создания записи (GET)"""
        response = self.client.get(reverse('core:record_create'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Создать запись денежного потока')
        self.assertContains(response, 'form')

    def test_record_create_view_post_valid(self):
        """Тест создания записи (POST с валидными данными)"""
        form_data = {
            'date': date.today(),
            'status': self.status.id,
            'type': self.type.id,
            'category': self.category.id,
            'subcategory': self.subcategory.id,
            'amount': '2000.00',
            'comment': 'Новая тестовая запись'
        }
        response = self.client.post(reverse('core:record_create'), form_data)
        self.assertEqual(response.status_code, 302)  # Редирект после успешного создания
        self.assertRedirects(response, reverse('core:index'))

    def test_record_create_view_post_invalid(self):
        """Тест создания записи (POST с невалидными данными)"""
        form_data = {
            'date': date.today(),
            'status': self.status.id,
            'type': self.type.id,
            'category': self.category.id,
            'subcategory': self.subcategory.id,
            'amount': '0.00',  # Невалидная сумма
            'comment': 'Тестовая запись'
        }
        response = self.client.post(reverse('core:record_create'), form_data)
        self.assertEqual(response.status_code, 200)  # Остается на той же странице
        self.assertContains(response, 'form')

    def test_record_edit_view_get(self):
        """Тест страницы редактирования записи (GET)"""
        response = self.client.get(reverse('core:record_edit', args=[self.record.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Редактировать запись денежного потока')
        self.assertContains(response, str(self.record.amount))

    def test_record_edit_view_post_valid(self):
        """Тест редактирования записи (POST с валидными данными)"""
        form_data = {
            'date': date.today(),
            'status': self.status.id,
            'type': self.type.id,
            'category': self.category.id,
            'subcategory': self.subcategory.id,
            'amount': '1500.00',
            'comment': 'Обновленная запись'
        }
        response = self.client.post(reverse('core:record_edit', args=[self.record.id]), form_data)
        self.assertEqual(response.status_code, 302)  # Редирект после успешного обновления
        self.assertRedirects(response, reverse('core:index'))

    def test_record_delete_view_get(self):
        """Тест страницы удаления записи (GET)"""
        response = self.client.get(reverse('core:record_delete', args=[self.record.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Удалить запись денежного потока')
        # Проверяем, что страница содержит информацию о записи
        self.assertContains(response, self.record.comment)

    def test_record_delete_view_post(self):
        """Тест удаления записи (POST)"""
        response = self.client.post(reverse('core:record_delete', args=[self.record.id]))
        self.assertEqual(response.status_code, 302)  # Редирект после удаления
        self.assertRedirects(response, reverse('core:index'))
        
        # Проверяем, что запись удалена
        self.assertFalse(CashFlowRecord.objects.filter(id=self.record.id).exists())

    def test_directory_management_view(self):
        """Тест страницы управления справочниками"""
        response = self.client.get(reverse('core:directory_management'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Управление списками')
        self.assertContains(response, 'Статусы')
        self.assertContains(response, 'Типы')
        self.assertContains(response, 'Категории')
        self.assertContains(response, 'Подкатегории')

    def test_ajax_categories_endpoint(self):
        """Тест AJAX endpoint для получения категорий по типу"""
        response = self.client.get(reverse('core:get_categories_by_type', args=[self.type.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        
        data = json.loads(response.content)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['id'], self.category.id)
        self.assertEqual(data[0]['name'], self.category.name)

    def test_ajax_subcategories_endpoint(self):
        """Тест AJAX endpoint для получения подкатегорий по категории"""
        response = self.client.get(reverse('core:get_subcategories_by_category', args=[self.category.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        
        data = json.loads(response.content)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['id'], self.subcategory.id)
        self.assertEqual(data[0]['name'], self.subcategory.name)

    def test_ajax_categories_endpoint_invalid_type(self):
        """Тест AJAX endpoint с несуществующим типом"""
        response = self.client.get(reverse('core:get_categories_by_type', args=[99999]))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data), 0)

    def test_ajax_subcategories_endpoint_invalid_category(self):
        """Тест AJAX endpoint с несуществующей категорией"""
        response = self.client.get(reverse('core:get_subcategories_by_category', args=[99999]))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data), 0)


# ============================================================================
# ФОРМЫ - ДЕТАЛЬНЫЕ ТЕСТЫ
# ============================================================================

class FormTest(TestCase):
    """Тесты для всех форм"""
    
    def setUp(self):
        self.status, _ = Status.objects.get_or_create(name="Бизнес", defaults={"description": "Бизнес-транзакции"})
        self.type, _ = Type.objects.get_or_create(name="Списание", defaults={"description": "Расход денег"})
        self.category = Category.objects.create(
            name="Инфраструктура", 
            type=self.type, 
            description="Затраты на инфраструктуру"
        )
        self.subcategory = Subcategory.objects.create(
            name="VPS", 
            category=self.category, 
            description="Затраты на виртуальный сервер"
        )

    def test_cash_flow_record_form_valid(self):
        """Тест валидной формы записи денежного потока"""
        form_data = {
            'date': date.today(),
            'status': self.status.id,
            'type': self.type.id,
            'category': self.category.id,
            'subcategory': self.subcategory.id,
            'amount': '1000.00',
            'comment': 'Тестовая транзакция'
        }
        
        form = CashFlowRecordForm(data=form_data)
        self.assertTrue(form.is_valid(), f"Form errors: {form.errors}")

    def test_cash_flow_record_form_invalid_amount(self):
        """Тест формы с невалидной суммой"""
        form_data = {
            'date': date.today(),
            'status': self.status.id,
            'type': self.type.id,
            'category': self.category.id,
            'subcategory': self.subcategory.id,
            'amount': '0.00',  # Невалидная сумма
            'comment': 'Тестовая транзакция'
        }
        
        form = CashFlowRecordForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('amount', form.errors)

    def test_cash_flow_record_form_missing_required_fields(self):
        """Тест формы с отсутствующими обязательными полями"""
        form_data = {
            'date': date.today(),
            'amount': '1000.00'
            # Отсутствуют обязательные поля
        }
        
        form = CashFlowRecordForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('status', form.errors)
        self.assertIn('type', form.errors)
        self.assertIn('category', form.errors)
        self.assertIn('subcategory', form.errors)

    def test_cash_flow_record_form_business_rules_validation(self):
        """Тест валидации бизнес-правил в форме"""
        # Создаем несовместимые данные
        other_type, _ = Type.objects.get_or_create(name="Пополнение", defaults={"description": "Поступление денег"})
        other_category = Category.objects.create(
            name="Зарплата", 
            type=other_type, 
            description="Доходы от зарплаты"
        )
        other_subcategory = Subcategory.objects.create(
            name="Зарплата", 
            category=other_category
        )
        
        form_data = {
            'date': date.today(),
            'status': self.status.id,
            'type': self.type.id,  # Списание
            'category': other_category.id,  # Категория от типа "Пополнение"
            'subcategory': other_subcategory.id,
            'amount': '1000.00',
            'comment': 'Тестовая транзакция'
        }
        
        form = CashFlowRecordForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('__all__', form.errors)

    def test_cash_flow_filter_form_valid(self):
        """Тест валидной формы фильтрации"""
        form_data = {
            'date_from': '2025-10-01',
            'date_to': '2025-10-31',
            'status': self.status.id,
            'type': self.type.id
        }
        
        form = CashFlowFilterForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_cash_flow_filter_form_invalid_date_range(self):
        """Тест формы фильтрации с некорректным диапазоном дат"""
        form_data = {
            'date_from': '2025-10-31',
            'date_to': '2025-10-01'  # Дата "с" больше даты "по"
        }
        
        form = CashFlowFilterForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('__all__', form.errors)

    def test_cash_flow_filter_form_empty(self):
        """Тест пустой формы фильтрации"""
        form = CashFlowFilterForm(data={})
        self.assertTrue(form.is_valid())  # Пустая форма должна быть валидной


# ============================================================================
# ИНТЕГРАЦИОННЫЕ ТЕСТЫ
# ============================================================================

class IntegrationTest(TestCase):
    """Интеграционные тесты для проверки работы всей системы"""
    
    def setUp(self):
        self.client = Client()
        
        # Создаем полную иерархию данных
        self.status, _ = Status.objects.get_or_create(name="Бизнес", defaults={"description": "Бизнес-транзакции"})
        self.type, _ = Type.objects.get_or_create(name="Списание", defaults={"description": "Расход денег"})
        self.category = Category.objects.create(
            name="Инфраструктура", 
            type=self.type, 
            description="Затраты на инфраструктуру"
        )
        self.subcategory = Subcategory.objects.create(
            name="VPS", 
            category=self.category, 
            description="Затраты на виртуальный сервер"
        )

    def test_full_workflow_create_record(self):
        """Тест полного рабочего процесса создания записи"""
        # 1. Переходим на страницу создания
        response = self.client.get(reverse('core:record_create'))
        self.assertEqual(response.status_code, 200)
        
        # 2. Создаем запись
        form_data = {
            'date': date.today(),
            'status': self.status.id,
            'type': self.type.id,
            'category': self.category.id,
            'subcategory': self.subcategory.id,
            'amount': '1000.00',
            'comment': 'Интеграционный тест'
        }
        
        response = self.client.post(reverse('core:record_create'), form_data)
        self.assertEqual(response.status_code, 302)
        
        # 3. Проверяем, что запись создана
        record = CashFlowRecord.objects.get(comment='Интеграционный тест')
        self.assertEqual(record.amount, Decimal('1000.00'))
        
        # 4. Проверяем, что запись отображается на главной странице
        response = self.client.get(reverse('core:index'))
        self.assertContains(response, 'Интеграционный тест')

    def test_full_workflow_edit_record(self):
        """Тест полного рабочего процесса редактирования записи"""
        # 1. Создаем запись
        record = CashFlowRecord.objects.create(
            date=date.today(),
            status=self.status,
            type=self.type,
            category=self.category,
            subcategory=self.subcategory,
            amount=Decimal('1000.00'),
            comment="Исходная запись"
        )
        
        # 2. Редактируем запись
        form_data = {
            'date': date.today(),
            'status': self.status.id,
            'type': self.type.id,
            'category': self.category.id,
            'subcategory': self.subcategory.id,
            'amount': '2000.00',
            'comment': 'Обновленная запись'
        }
        
        response = self.client.post(reverse('core:record_edit', args=[record.id]), form_data)
        self.assertEqual(response.status_code, 302)
        
        # 3. Проверяем, что запись обновлена
        record.refresh_from_db()
        self.assertEqual(record.amount, Decimal('2000.00'))
        self.assertEqual(record.comment, 'Обновленная запись')

    def test_full_workflow_delete_record(self):
        """Тест полного рабочего процесса удаления записи"""
        # 1. Создаем запись
        record = CashFlowRecord.objects.create(
            date=date.today(),
            status=self.status,
            type=self.type,
            category=self.category,
            subcategory=self.subcategory,
            amount=Decimal('1000.00'),
            comment="Запись для удаления"
        )
        
        # 2. Удаляем запись
        response = self.client.post(reverse('core:record_delete', args=[record.id]))
        self.assertEqual(response.status_code, 302)
        
        # 3. Проверяем, что запись удалена
        self.assertFalse(CashFlowRecord.objects.filter(id=record.id).exists())

    def test_ajax_cascade_filtering(self):
        """Тест каскадной фильтрации через AJAX"""
        # 1. Получаем категории по типу
        response = self.client.get(reverse('core:get_categories_by_type', args=[self.type.id]))
        self.assertEqual(response.status_code, 200)
        categories_data = json.loads(response.content)
        self.assertEqual(len(categories_data), 1)
        self.assertEqual(categories_data[0]['name'], 'Инфраструктура')
        
        # 2. Получаем подкатегории по категории
        response = self.client.get(reverse('core:get_subcategories_by_category', args=[self.category.id]))
        self.assertEqual(response.status_code, 200)
        subcategories_data = json.loads(response.content)
        self.assertEqual(len(subcategories_data), 1)
        self.assertEqual(subcategories_data[0]['name'], 'VPS')

    def test_statistics_calculation(self):
        """Тест расчета статистики"""
        # Создаем записи доходов и расходов
        income_type, _ = Type.objects.get_or_create(name="Пополнение", defaults={"description": "Поступление денег"})
        income_category = Category.objects.create(
            name="Зарплата", 
            type=income_type, 
            description="Доходы от зарплаты"
        )
        income_subcategory = Subcategory.objects.create(
            name="Зарплата", 
            category=income_category, 
            description="Основная зарплата"
        )
        
        # Запись дохода
        CashFlowRecord.objects.create(
            date=date.today(),
            status=self.status,
            type=income_type,
            category=income_category,
            subcategory=income_subcategory,
            amount=Decimal('50000.00'),
            comment="Зарплата"
        )
        
        # Запись расхода
        CashFlowRecord.objects.create(
            date=date.today(),
            status=self.status,
            type=self.type,
            category=self.category,
            subcategory=self.subcategory,
            amount=Decimal('1000.00'),
            comment="VPS"
        )
        
        # Проверяем главную страницу
        response = self.client.get(reverse('core:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '50000')  # Доходы
        self.assertContains(response, '1000')  # Расходы
        self.assertContains(response, '49000')  # Баланс