from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Status, Type, Category, Subcategory, CashFlowRecord


class CashFlowRecordForm(forms.ModelForm):
    """Форма для создания и редактирования записей денежного потока"""
    
    class Meta:
        model = CashFlowRecord
        fields = ['date', 'status', 'type', 'category', 'subcategory', 'amount', 'comment']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}, format='%Y-%m-%d'),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'type': forms.Select(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'subcategory': forms.Select(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01'}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        labels = {
            'date': 'Дата',
            'status': 'Статус',
            'type': 'Тип',
            'category': 'Категория',
            'subcategory': 'Подкатегория',
            'amount': 'Сумма (руб.)',
            'comment': 'Комментарий',
        }

    def __init__(self, *args, **kwargs):
        """Настройка динамической фильтрации подкатегорий по категориям"""
        super().__init__(*args, **kwargs)
        
        self.fields['status'].queryset = Status.objects.all()
        self.fields['type'].queryset = Type.objects.all()
        self.fields['category'].queryset = Category.objects.all()
        self.fields['subcategory'].queryset = Subcategory.objects.none()
        
        # Устанавливаем правильный формат для поля даты
        self.fields['date'].input_formats = ['%Y-%m-%d']
        
        # Если редактируем существующую запись, заполняем подкатегории
        if self.instance.pk:
            if self.instance.category:
                self.fields['subcategory'].queryset = Subcategory.objects.filter(category=self.instance.category)
            # Устанавливаем начальные значения для полей
            if self.instance.type:
                self.fields['category'].queryset = Category.objects.filter(type=self.instance.type)
        
        # Восстанавливаем подкатегории при ошибке валидации
        if self.is_bound and 'category' in self.data:
            try:
                category_id = int(self.data.get('category'))
                self.fields['subcategory'].queryset = Subcategory.objects.filter(category_id=category_id)
            except (ValueError, TypeError):
                pass

    def clean(self):
        """Проверка бизнес-правил: подкатегория должна принадлежать выбранной категории, категория - выбранному типу"""
        cleaned_data = super().clean()
        category_obj = cleaned_data.get('category')
        subcategory_obj = cleaned_data.get('subcategory')
        type_obj = cleaned_data.get('type')
        date_obj = cleaned_data.get('date')
        
        # Проверка: подкатегория должна принадлежать выбранной категории
        if subcategory_obj and category_obj and subcategory_obj.category != category_obj:
            raise ValidationError("Выбранная подкатегория не принадлежит выбранной категории.")
        
        # Проверка: категория должна принадлежать выбранному типу
        if category_obj and type_obj and category_obj.type != type_obj:
            raise ValidationError("Выбранная категория не относится к выбранному типу.")
        
        # Проверка даты: разрешаем будущие даты для планирования
        # Можно раскомментировать для запрета будущих дат:
        # if date_obj and date_obj > timezone.now().date():
        #     raise ValidationError("Нельзя создавать записи с будущей датой.")
        
        return cleaned_data


class CashFlowFilterForm(forms.Form):
    """
    Форма для фильтрации записей денежного потока.
    
    Позволяет пользователям искать записи по различным критериям:
    дате, статусу, типу, категории и подкатегории. Все поля необязательные,
    можно комбинировать фильтры для точного поиска.
    """
    
    # Фильтр по начальной дате (включительно)
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label='Дата с'
    )
    
    # Фильтр по конечной дате (включительно)
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label='Дата по'
    )
    
    # Фильтр по статусу операции
    status = forms.ModelChoiceField(
        queryset=Status.objects.all(),
        required=False,
        empty_label="Все статусы",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    # Фильтр по типу операции
    type = forms.ModelChoiceField(
        queryset=Type.objects.all(),
        required=False,
        empty_label="Все типы",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    # Фильтр по категории
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=False,
        empty_label="Все категории",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    # Фильтр по подкатегории
    subcategory = forms.ModelChoiceField(
        queryset=Subcategory.objects.all(),
        required=False,
        empty_label="Все подкатегории",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        """
        Инициализация формы фильтрации.
        
        Настраиваем queryset'ы для всех полей, сортируя их по алфавиту
        для удобства пользователей.
        """
        super().__init__(*args, **kwargs)
        
        # Сортируем все списки по алфавиту для удобства
        self.fields['status'].queryset = Status.objects.all().order_by('name')
        self.fields['type'].queryset = Type.objects.all().order_by('name')
        self.fields['category'].queryset = Category.objects.all().order_by('name')
        self.fields['subcategory'].queryset = Subcategory.objects.all().order_by('name')
        
        # Устанавливаем правильный формат для полей даты
        self.fields['date_from'].input_formats = ['%Y-%m-%d']
        self.fields['date_to'].input_formats = ['%Y-%m-%d']

    def clean(self):
        """
        Валидация формы фильтрации.
        
        Проверяем логичность выбранных дат: дата_с не должна быть больше дата_по.
        """
        cleaned_data = super().clean()
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')
        
        # Проверяем логичность диапазона дат
        if date_from and date_to and date_from > date_to:
            raise ValidationError("Дата 'с' не может быть больше даты 'по'. Пожалуйста, выберите корректный диапазон дат.")
        
        return cleaned_data


class DirectoryForm(forms.ModelForm):
    """
    Базовая форма для управления справочниками.
    
    Общая форма для создания и редактирования справочных данных
    (статусы, типы, категории, подкатегории). Содержит общие поля
    и настройки стилизации для всех справочников.
    """
    
    class Meta:
        # Основные поля для всех справочников
        fields = ['name', 'description']
        
        # Настройка виджетов с Bootstrap стилями
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        
        # Русские названия полей
        labels = {
            'name': 'Название',
            'description': 'Описание',
        }


class StatusForm(DirectoryForm):
    """
    Форма для управления статусами денежных потоков.
    
    Наследует базовую форму DirectoryForm и добавляет модель Status.
    Позволяет создавать и редактировать статусы (Бизнес, Личное, Налоги и т.д.).
    """
    class Meta(DirectoryForm.Meta):
        model = Status


class TypeForm(DirectoryForm):
    """
    Форма для управления типами денежных потоков.
    
    Наследует базовую форму DirectoryForm и добавляет модель Type.
    Позволяет создавать и редактировать типы (Пополнение, Списание и т.д.).
    """
    class Meta(DirectoryForm.Meta):
        model = Type


class CategoryForm(DirectoryForm):
    """
    Форма для управления категориями денежных потоков.
    
    Наследует базовую форму DirectoryForm и добавляет модель Category.
    Позволяет создавать и редактировать категории (Инфраструктура, Маркетинг и т.д.).
    """
    
    # Поле выбора типа
    type = forms.ModelChoiceField(
        queryset=Type.objects.all().order_by('name'),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Тип'
    )
    
    class Meta(DirectoryForm.Meta):
        model = Category
        # Включаем поле типа в список полей формы
        fields = ['name', 'type', 'description']


class SubcategoryForm(DirectoryForm):
    """
    Форма для управления подкатегориями денежных потоков.
    
    Расширяет базовую форму DirectoryForm, добавляя поле выбора категории.
    Позволяет создавать и редактировать подкатегории (VPS, Авито и т.д.)
    с привязкой к родительской категории.
    """
    
    # Поле выбора родительской категории
    category = forms.ModelChoiceField(
        queryset=Category.objects.all().order_by('name'),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Категория'
    )
    
    class Meta(DirectoryForm.Meta):
        model = Subcategory
        # Включаем поле категории в список полей формы
        fields = ['name', 'category', 'description']
