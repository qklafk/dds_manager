from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from .models import Status, Type, Category, Subcategory, CashFlowRecord
from .forms import (
    CashFlowRecordForm, CashFlowFilterForm, 
    StatusForm, TypeForm, CategoryForm, SubcategoryForm
)


def index(request):
    """Главная страница с таблицей записей ДДС и фильтрами"""
    from django.db.models import Sum
    
    filter_form = CashFlowFilterForm(request.GET)
    records = CashFlowRecord.objects.all()
    
    # Применяем фильтры
    if filter_form.is_valid():
        if filter_form.cleaned_data.get('date_from'):
            records = records.filter(date__gte=filter_form.cleaned_data['date_from'])
        if filter_form.cleaned_data.get('date_to'):
            records = records.filter(date__lte=filter_form.cleaned_data['date_to'])
        if filter_form.cleaned_data.get('status'):
            records = records.filter(status=filter_form.cleaned_data['status'])
        if filter_form.cleaned_data.get('type'):
            records = records.filter(type=filter_form.cleaned_data['type'])
        if filter_form.cleaned_data.get('category'):
            records = records.filter(category=filter_form.cleaned_data['category'])
        if filter_form.cleaned_data.get('subcategory'):
            records = records.filter(subcategory=filter_form.cleaned_data['subcategory'])
    
    # Расчет аналитики
    total_records = records.count()
    
    # Доходы (пополнения)
    income_records = records.filter(type__name__in=['Пополнение', 'Replenishment'])
    total_income = income_records.aggregate(total=Sum('amount'))['total'] or 0
    
    # Расходы (списания)
    expense_records = records.filter(type__name__in=['Списание', 'Write-off'])
    total_expenses = expense_records.aggregate(total=Sum('amount'))['total'] or 0
    
    # Баланс
    balance = total_income - total_expenses
    
    # Пагинация
    paginator = Paginator(records, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'filter_form': filter_form,
        'total_records': total_records,
        'total_income': total_income,
        'total_expenses': total_expenses,
        'balance': balance,
    }
    return render(request, 'core/index.html', context)


def record_create(request):
    """Создание новой записи денежного потока"""
    if request.method == 'POST':
        form = CashFlowRecordForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Запись денежного потока успешно создана!')
            return redirect('core:index')
    else:
        form = CashFlowRecordForm()
    
    context = {
        'form': form,
        'title': 'Создать запись денежного потока',
        'action': 'create'
    }
    return render(request, 'core/record_form.html', context)


def record_edit(request, pk):
    """
    Редактирование существующей записи денежного потока.
    
    Получает запись по ID и позволяет пользователю изменить её данные.
    При успешном обновлении перенаправляет на главную страницу.
    """
    # Получаем запись по ID или возвращаем 404 если не найдена
    record = get_object_or_404(CashFlowRecord, pk=pk)
    
    if request.method == 'POST':
        # Создаем форму с данными из POST и существующей записью
        form = CashFlowRecordForm(request.POST, instance=record)
        if form.is_valid():
            # Сохраняем изменения в базу данных
            form.save()
            # Показываем сообщение об успехе
            messages.success(request, 'Запись денежного потока успешно обновлена!')
            # Перенаправляем на главную страницу
            return redirect('core:index')
    else:
        # Для GET запроса создаем форму с данными существующей записи
        form = CashFlowRecordForm(instance=record)
    
    # Подготавливаем контекст для шаблона
    context = {
        'form': form,
        'title': 'Редактировать запись денежного потока',
        'action': 'edit',  # Указываем действие для шаблона
        'record': record   # Передаем запись для дополнительной информации
    }
    return render(request, 'core/record_form.html', context)


def record_delete(request, pk):
    """
    Удаление записи денежного потока.
    
    Показывает страницу подтверждения удаления для GET запроса.
    Удаляет запись при POST запросе и перенаправляет на главную страницу.
    """
    # Получаем запись по ID или возвращаем 404 если не найдена
    record = get_object_or_404(CashFlowRecord, pk=pk)
    
    if request.method == 'POST':
        # Удаляем запись из базы данных
        record.delete()
        # Показываем сообщение об успехе
        messages.success(request, 'Запись денежного потока успешно удалена!')
        # Перенаправляем на главную страницу
        return redirect('core:index')
    
    # Для GET запроса показываем страницу подтверждения
    context = {
        'record': record,
        'title': 'Удалить запись денежного потока'
    }
    return render(request, 'core/record_confirm_delete.html', context)


def directory_management(request):
    """
    Страница управления справочниками.
    
    Отображает все справочные данные (статусы, типы, категории, подкатегории)
    с возможностью их создания, редактирования и удаления.
    """
    # Подготавливаем все справочные данные, отсортированные по алфавиту
    context = {
        'statuses': Status.objects.all().order_by('name'),
        'types': Type.objects.all().order_by('name'),
        'categories': Category.objects.all().order_by('name'),
        'subcategories': Subcategory.objects.all().order_by('category__name', 'name'),
    }
    return render(request, 'core/directory_management.html', context)


def status_create(request):
    """Create new status"""
    if request.method == 'POST':
        form = StatusForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Статус успешно создан!')
            return redirect('core:directory_management')
    else:
        form = StatusForm()
    
    context = {
        'form': form,
        'title': 'Создать статус',
        'action': 'create',
        'model_name': 'следующий статус'
    }
    return render(request, 'core/directory_form.html', context)


def status_edit(request, pk):
    """Edit existing status"""
    status = get_object_or_404(Status, pk=pk)
    
    if request.method == 'POST':
        form = StatusForm(request.POST, instance=status)
        if form.is_valid():
            form.save()
            messages.success(request, 'Статус успешно обновлен!')
            return redirect('core:directory_management')
    else:
        form = StatusForm(instance=status)
    
    context = {
        'form': form,
        'title': 'Редактировать статус',
        'action': 'edit',
        'model_name': 'следующий статус',
        'object': status
    }
    return render(request, 'core/directory_form.html', context)


def status_delete(request, pk):
    """Delete status"""
    status = get_object_or_404(Status, pk=pk)
    
    if request.method == 'POST':
        status.delete()
        messages.success(request, 'Статус успешно удален!')
        return redirect('core:directory_management')
    
    context = {
        'object': status,
        'title': 'Удаление статуса',
        'model_name': 'следующий статус'
    }
    return render(request, 'core/directory_confirm_delete.html', context)


def type_create(request):
    """Create new type"""
    if request.method == 'POST':
        form = TypeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Тип успешно создан!')
            return redirect('core:directory_management')
    else:
        form = TypeForm()
    
    context = {
        'form': form,
        'title': 'Создать тип',
        'action': 'create',
        'model_name': 'следующий тип'
    }
    return render(request, 'core/directory_form.html', context)


def type_edit(request, pk):
    """Edit existing type"""
    type_obj = get_object_or_404(Type, pk=pk)
    
    if request.method == 'POST':
        form = TypeForm(request.POST, instance=type_obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Тип успешно обновлен!')
            return redirect('core:directory_management')
    else:
        form = TypeForm(instance=type_obj)
    
    context = {
        'form': form,
        'title': 'Редактировать тип',
        'action': 'edit',
        'model_name': 'следующий тип',
        'object': type_obj
    }
    return render(request, 'core/directory_form.html', context)


def type_delete(request, pk):
    """Delete type"""
    type_obj = get_object_or_404(Type, pk=pk)
    
    if request.method == 'POST':
        type_obj.delete()
        messages.success(request, 'Тип успешно удален!')
        return redirect('core:directory_management')
    
    context = {
        'object': type_obj,
        'title': 'Удаление типа',
        'model_name': 'следующий тип'
    }
    return render(request, 'core/directory_confirm_delete.html', context)


def category_create(request):
    """Create new category"""
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Категория успешно создана!')
            return redirect('core:directory_management')
    else:
        form = CategoryForm()
    
    context = {
        'form': form,
        'title': 'Создать категорию',
        'action': 'create',
        'model_name': 'следующую категорию'
    }
    return render(request, 'core/directory_form.html', context)


def category_edit(request, pk):
    """Edit existing category"""
    category = get_object_or_404(Category, pk=pk)
    
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'Категория успешно обновлена!')
            return redirect('core:directory_management')
    else:
        form = CategoryForm(instance=category)
    
    context = {
        'form': form,
        'title': 'Редактировать категорию',
        'action': 'edit',
        'model_name': 'следующую категорию',
        'object': category
    }
    return render(request, 'core/directory_form.html', context)


def category_delete(request, pk):
    """Delete category"""
    category = get_object_or_404(Category, pk=pk)
    
    if request.method == 'POST':
        category.delete()
        messages.success(request, 'Категория успешно удалена!')
        return redirect('core:directory_management')
    
    context = {
        'object': category,
        'title': 'Удаление категории',
        'model_name': 'следующую категорию'
    }
    return render(request, 'core/directory_confirm_delete.html', context)


def subcategory_create(request):
    """Create new subcategory"""
    if request.method == 'POST':
        form = SubcategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Подкатегория успешно создана!')
            return redirect('core:directory_management')
    else:
        form = SubcategoryForm()
    
    context = {
        'form': form,
        'title': 'Создать подкатегорию',
        'action': 'create',
        'model_name': 'следующую подкатегорию'
    }
    return render(request, 'core/directory_form.html', context)


def subcategory_edit(request, pk):
    """Edit existing subcategory"""
    subcategory = get_object_or_404(Subcategory, pk=pk)
    
    if request.method == 'POST':
        form = SubcategoryForm(request.POST, instance=subcategory)
        if form.is_valid():
            form.save()
            messages.success(request, 'Подкатегория успешно обновлена!')
            return redirect('core:directory_management')
    else:
        form = SubcategoryForm(instance=subcategory)
    
    context = {
        'form': form,
        'title': 'Редактировать подкатегорию',
        'action': 'edit',
        'model_name': 'следующую подкатегорию',
        'object': subcategory
    }
    return render(request, 'core/directory_form.html', context)


def subcategory_delete(request, pk):
    """Delete subcategory"""
    subcategory = get_object_or_404(Subcategory, pk=pk)
    
    if request.method == 'POST':
        subcategory.delete()
        messages.success(request, 'Подкатегория успешно удалена!')
        return redirect('core:directory_management')
    
    context = {
        'object': subcategory,
        'title': 'Удаление подкатегории',
        'model_name': 'следующую подкатегорию'
    }
    return render(request, 'core/directory_confirm_delete.html', context)


# AJAX представления для динамической фильтрации
@require_http_methods(["GET"])
def get_categories_by_type(request, type_id):
    """
    Получение категорий, отфильтрованных по типу.
    
    AJAX endpoint для динамического обновления списка категорий
    при выборе типа. Возвращает JSON с ID и названиями категорий.
    """
    # Получаем категории для выбранного типа
    categories = Category.objects.filter(type_id=type_id).order_by('name')
    # Формируем JSON данные для JavaScript
    data = [{'id': cat.id, 'name': cat.name} for cat in categories]
    return JsonResponse(data, safe=False)


@require_http_methods(["GET"])
def get_subcategories_by_category(request, category_id):
    """
    Получение подкатегорий, отфильтрованных по категории.
    
    AJAX endpoint для динамического обновления списка подкатегорий
    при выборе категории. Возвращает JSON с ID и названиями подкатегорий.
    """
    # Получаем подкатегории для выбранной категории
    subcategories = Subcategory.objects.filter(category_id=category_id).order_by('name')
    # Формируем JSON данные для JavaScript
    data = [{'id': sub.id, 'name': sub.name} for sub in subcategories]
    return JsonResponse(data, safe=False)
