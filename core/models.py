from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone


class Status(models.Model):
    """Статус денежного потока (Бизнес, Личное, Налоги и т.д.)"""
    name = models.CharField(max_length=50, unique=True, verbose_name="Название статуса")
    description = models.TextField(blank=True, verbose_name="Описание")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Статус"
        verbose_name_plural = "Статусы"
        ordering = ['name']

    def __str__(self):
        return self.name


class Type(models.Model):
    """Тип денежного потока (Пополнение, Списание и т.д.)"""
    name = models.CharField(max_length=50, unique=True, verbose_name="Название типа")
    description = models.TextField(blank=True, verbose_name="Описание")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Тип"
        verbose_name_plural = "Типы"
        ordering = ['name']

    def __str__(self):
        return self.name


class Category(models.Model):
    """Категория денежного потока (Инфраструктура, Маркетинг и т.д.)"""
    name = models.CharField(max_length=100, unique=True, verbose_name="Название категории")
    type = models.ForeignKey(Type, on_delete=models.CASCADE, related_name='categories', verbose_name="Тип")
    description = models.TextField(blank=True, verbose_name="Описание")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
        ordering = ['name']

    def __str__(self):
        return self.name


class Subcategory(models.Model):
    """Подкатегория денежного потока (VPS, Прокси, Авито и т.д.)"""
    name = models.CharField(max_length=100, verbose_name="Название подкатегории")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='subcategories', verbose_name="Категория")
    description = models.TextField(blank=True, verbose_name="Описание")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Подкатегория"
        verbose_name_plural = "Подкатегории"
        ordering = ['name']
        unique_together = ['name', 'category']

    def __str__(self):
        return f"{self.name} ({self.category.name})"


class CashFlowRecord(models.Model):
    """Основная модель для записей денежного потока (ДДС)"""
    date = models.DateField(default=timezone.now, verbose_name="Дата")
    status = models.ForeignKey(Status, on_delete=models.CASCADE, verbose_name="Статус")
    type = models.ForeignKey(Type, on_delete=models.CASCADE, verbose_name="Тип")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name="Категория")
    subcategory = models.ForeignKey(Subcategory, on_delete=models.CASCADE, verbose_name="Подкатегория")
    amount = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        validators=[MinValueValidator(0.01)],
        verbose_name="Сумма (руб.)"
    )
    comment = models.TextField(blank=True, verbose_name="Комментарий")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Запись денежного потока"
        verbose_name_plural = "Записи денежного потока"
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.date} - {self.type.name} - {self.amount} руб."

    def clean(self):
        """Проверка бизнес-правил: подкатегория должна принадлежать выбранной категории, категория - выбранному типу"""
        from django.core.exceptions import ValidationError
        
        # Проверка: подкатегория должна принадлежать выбранной категории
        if (hasattr(self, 'subcategory') and hasattr(self, 'category') and 
            self.subcategory and self.category and 
            self.subcategory.category != self.category):
            raise ValidationError("Выбранная подкатегория не принадлежит выбранной категории.")
        
        # Проверка: категория должна принадлежать выбранному типу
        if (hasattr(self, 'category') and hasattr(self, 'type') and 
            self.category and self.type and 
            self.category.type != self.type):
            raise ValidationError("Выбранная категория не относится к выбранному типу.")
