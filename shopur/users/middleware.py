from django.utils import translation
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin


class LanguageMiddleware(MiddlewareMixin):
    """
    Middleware для установки языка пользователя на основе его настроек
    """
    
    def process_request(self, request):
        # Если пользователь аутентифицирован, используем его язык из настроек
        if request.user.is_authenticated:
            try:
                user_settings = request.user.usersettings
                language = user_settings.language
                if language in dict(settings.LANGUAGES):
                    translation.activate(language)
                    request.LANGUAGE_CODE = language
                    request.session['django_language'] = language
                    return
            except Exception:
                pass
        
        # Попытаемся получить язык из сессии
        language = request.session.get('django_language')
        if language and language in dict(settings.LANGUAGES):
            translation.activate(language)
            request.LANGUAGE_CODE = language
            return
        
        # Попытаемся получить язык из cookie
        language = request.COOKIES.get('django_language')
        if language and language in dict(settings.LANGUAGES):
            translation.activate(language)
            request.LANGUAGE_CODE = language
            request.session['django_language'] = language
            return
        
        # Иначе используем язык браузера
        lang = translation.get_language_from_request(request)
        if lang in dict(settings.LANGUAGES):
            translation.activate(lang)
            request.LANGUAGE_CODE = lang
        else:
            # Используем язык по умолчанию
            translation.activate(settings.LANGUAGE_CODE)
            request.LANGUAGE_CODE = settings.LANGUAGE_CODE


class ThemeMiddleware(MiddlewareMixin):
    """
    Middleware для установки темы пользователя на основе его настроек
    """
    
    def process_request(self, request):
        # Если пользователь аутентифицирован, используем его тему из настроек
        if request.user.is_authenticated:
            try:
                user_settings = request.user.usersettings
                request.user_theme = user_settings.theme
                return
            except Exception:
                pass
        
        # Попытаемся получить тему из cookie
        theme = request.COOKIES.get('django_theme', 'light')
        if theme in dict(settings.THEME_CHOICES if hasattr(settings, 'THEME_CHOICES') else [('light', 'Light'), ('dark', 'Dark')]):
            request.user_theme = theme
            return
        
        # Используем светлую тему по умолчанию
        request.user_theme = 'light'
