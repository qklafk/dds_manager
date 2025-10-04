# Generated manually to populate category types
from django.db import migrations


def populate_category_types(apps, schema_editor):
    """Заполняем типы для существующих категорий"""
    Type = apps.get_model('core', 'Type')
    Category = apps.get_model('core', 'Category')
    
    # Создаем типы если их нет
    write_off_type, created = Type.objects.get_or_create(
        name='Списание',
        defaults={'description': 'Расход денег'}
    )
    
    replenishment_type, created = Type.objects.get_or_create(
        name='Пополнение',
        defaults={'description': 'Поступление денег'}
    )
    
    # Привязываем существующие категории к типу "Списание"
    Category.objects.filter(type__isnull=True).update(type=write_off_type)


def reverse_populate_category_types(apps, schema_editor):
    """Обратная операция - очищаем типы"""
    Category = apps.get_model('core', 'Category')
    Category.objects.all().update(type=None)


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_category_type'),
    ]

    operations = [
        migrations.RunPython(populate_category_types, reverse_populate_category_types),
    ]
