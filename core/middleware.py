"""
Middleware для защиты от SQL-инъекций и других атак
"""
import re
import logging
from django.http import HttpResponseForbidden
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings

logger = logging.getLogger(__name__)


class SQLInjectionProtectionMiddleware(MiddlewareMixin):
    """
    Middleware для защиты от SQL-инъекций и других атак
    
    Проверяет все входящие запросы на наличие подозрительных паттернов
    и блокирует потенциально опасные запросы.
    """
    
    def __init__(self, get_response):
        super().__init__(get_response)
        # Паттерны для обнаружения SQL-инъекций
        self.sql_patterns = [
            r'(\b(union|select|insert|update|delete|drop|create|alter|exec|execute)\b)',
            r'(\b(or|and)\s+\d+\s*=\s*\d+)',
            r'(\b(or|and)\s+\w+\s*=\s*\w+)',
            r'(\'|\"|;|--|\/\*|\*\/)',
            r'(\b(script|javascript|vbscript|onload|onerror)\b)',
            r'(\<|\>|&lt;|&gt;)',
            r'(\b(union\s+select|select\s+.*\s+from|insert\s+into|update\s+.*\s+set|delete\s+from)\b)',
            r'(\b(load_file|into\s+outfile|into\s+dumpfile)\b)',
            r'(\b(concat|substring|ascii|char|hex|unhex)\b)',
            r'(\b(version|user|database|schema|table_name|column_name)\b)',
        ]
        
        # Паттерны для обнаружения XSS атак
        self.xss_patterns = [
            r'(\<script\b[^>]*\>.*?\</script\>)',
            r'(\<iframe\b[^>]*\>.*?\</iframe\>)',
            r'(\<object\b[^>]*\>.*?\</object\>)',
            r'(\<embed\b[^>]*\>)',
            r'(\<link\b[^>]*\>)',
            r'(\<meta\b[^>]*\>)',
            r'(\<style\b[^>]*\>.*?\</style\>)',
            r'(\<link\b[^>]*\>)',
            r'(\<img\b[^>]*\>)',
            r'(\<svg\b[^>]*\>.*?\</svg\>)',
        ]
        
        # Паттерны для обнаружения попыток обхода аутентификации
        # Более специфичные паттерны, чтобы не блокировать легитимные случаи
        self.auth_bypass_patterns = [
            r'(\b(admin|administrator|root|sa|guest|test|demo)\s*[\'\"])',  # Только с кавычками
            r'(\b(password|passwd|pwd|secret|key|token)\s*[\'\"])',       # Только с кавычками
            r'(\b(login|logon|signin|signon)\s*[\'\"])',                  # Только с кавычками
            r'(\b(auth|authentication|authorization)\s*[\'\"])',          # Только с кавычками
            r'(\b(admin|administrator|root|sa|guest|test|demo)\s*[=<>])', # С операторами
            r'(\b(password|passwd|pwd|secret|key|token)\s*[=<>])',        # С операторами
        ]
    
    def process_request(self, request):
        """
        Обработка входящего запроса для проверки на атаки
        """
        # Отключаем middleware в режиме отладки, если указано в настройках
        if getattr(settings, 'DISABLE_SECURITY_MIDDLEWARE', False):
            return None
        
        # Исключаем только статические файлы из проверки
        excluded_paths = [
            '/static/',
            '/media/',
            '/favicon.ico',
            '/robots.txt',
        ]
        
        # Проверяем, не является ли путь исключенным
        for excluded_path in excluded_paths:
            if request.path.startswith(excluded_path):
                return None
        
        # Получаем все параметры запроса
        all_params = {}
        
        # GET параметры
        if request.GET:
            all_params.update(dict(request.GET))
        
        # POST параметры
        if request.POST:
            all_params.update(dict(request.POST))
        
        # Проверяем каждый параметр
        for param_name, param_values in all_params.items():
            if isinstance(param_values, list):
                for value in param_values:
                    if self._check_for_attacks(str(value)):
                        self._log_attack_attempt(request, param_name, value)
                        return HttpResponseForbidden(
                            "Доступ запрещен: обнаружена попытка атаки"
                        )
            else:
                if self._check_for_attacks(str(param_values)):
                    self._log_attack_attempt(request, param_name, param_values)
                    return HttpResponseForbidden(
                        "Доступ запрещен: обнаружена попытка атаки"
                    )
        
        return None
    
    def _check_for_attacks(self, value):
        """
        Проверка значения на наличие атак
        """
        if not value:
            return False
        
        value_lower = value.lower()
        
        # Проверяем SQL-инъекции
        for pattern in self.sql_patterns:
            if re.search(pattern, value_lower, re.IGNORECASE):
                return True
        
        # Проверяем XSS атаки
        for pattern in self.xss_patterns:
            if re.search(pattern, value_lower, re.IGNORECASE):
                return True
        
        # Проверяем попытки обхода аутентификации
        for pattern in self.auth_bypass_patterns:
            if re.search(pattern, value_lower, re.IGNORECASE):
                return True
        
        return False
    
    def _log_attack_attempt(self, request, param_name, param_value):
        """
        Логирование попытки атаки
        """
        logger.warning(
            f"Попытка атаки обнаружена: "
            f"IP={request.META.get('REMOTE_ADDR', 'Unknown')}, "
            f"User-Agent={request.META.get('HTTP_USER_AGENT', 'Unknown')}, "
            f"URL={request.get_full_path()}, "
            f"Parameter={param_name}, "
            f"Value={param_value[:100]}..."  # Ограничиваем длину для лога
        )


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Middleware для добавления заголовков безопасности
    """
    
    def process_response(self, request, response):
        """
        Добавление заголовков безопасности к ответу
        """
        # Защита от XSS
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        
        # Защита от MIME-type sniffing
        response['X-Content-Type-Options'] = 'nosniff'
        
        # Защита от clickjacking
        response['X-Frame-Options'] = 'DENY'
        
        # Строгая транспортная безопасность (если используется HTTPS)
        if request.is_secure():
            response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        # Политика реферера
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Политика разрешений
        response['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        
        return response

