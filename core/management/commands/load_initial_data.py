from django.core.management.base import BaseCommand
from core.models import Status, Type, Category, Subcategory


class Command(BaseCommand):
    help = 'Загрузить начальные данные для приложения ДДС на русском языке'

    def handle(self, *args, **options):
        self.stdout.write('Загрузка начальных данных...')

        # Создание статусов
        statuses_data = [
            {'name': 'Бизнес', 'description': 'Бизнес-транзакции'},
            {'name': 'Личное', 'description': 'Личные транзакции'},
            {'name': 'Налог', 'description': 'Налоговые транзакции'},
        ]

        for status_data in statuses_data:
            status, created = Status.objects.get_or_create(
                name=status_data['name'],
                defaults={'description': status_data['description']}
            )
            if created:
                self.stdout.write(f'✓ Создан статус: {status.name}')

        # Создание типов
        types_data = [
            {'name': 'Пополнение', 'description': 'Поступление денег'},
            {'name': 'Списание', 'description': 'Расход денег'},
        ]

        for type_data in types_data:
            type_obj, created = Type.objects.get_or_create(
                name=type_data['name'],
                defaults={'description': type_data['description']}
            )
            if created:
                self.stdout.write(f'✓ Создан тип: {type_obj.name}')

        # Создание категорий с привязкой к типам
        write_off_type = Type.objects.get(name='Списание')
        
        categories_data = [
            {'name': 'Инфраструктура', 'type': write_off_type, 'description': 'Затраты на инфраструктуру'},
            {'name': 'Маркетинг', 'type': write_off_type, 'description': 'Маркетинговые расходы'},
        ]

        for category_data in categories_data:
            category, created = Category.objects.get_or_create(
                name=category_data['name'],
                defaults={
                    'type': category_data['type'],
                    'description': category_data['description']
                }
            )
            if created:
                self.stdout.write(f'✓ Создана категория: {category.name} (тип: {category.type.name})')

        # Создание подкатегорий
        infrastructure_category = Category.objects.get(name='Инфраструктура')
        marketing_category = Category.objects.get(name='Маркетинг')

        subcategories_data = [
            {'name': 'VPS', 'category': infrastructure_category, 'description': 'Затраты на виртуальный сервер'},
            {'name': 'Proxy', 'category': infrastructure_category, 'description': 'Затраты на прокси-сервисы'},
            {'name': 'Farpost', 'category': marketing_category, 'description': 'Реклама на Фарпост'},
            {'name': 'Avito', 'category': marketing_category, 'description': 'Реклама на Авито'},
        ]

        for subcategory_data in subcategories_data:
            subcategory, created = Subcategory.objects.get_or_create(
                name=subcategory_data['name'],
                category=subcategory_data['category'],
                defaults={'description': subcategory_data['description']}
            )
            if created:
                self.stdout.write(f'Создана подкатегория: {subcategory.name}')

        self.stdout.write(
            self.style.SUCCESS('Начальные данные успешно загружены!')
        )
