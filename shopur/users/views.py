from rest_framework import viewsets
from django.contrib.auth import get_user_model
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import translation

from .models import UserSettings, Favorite
from .serializers import UserSerializer, UserSettingsSerializer
from .forms import CustomUserCreationForm
from .forms_profile import ProfileForm, UserSettingsForm
from catalog.models import ShopProduct


User = get_user_model()


LANGUAGE_SESSION_KEY = 'django_language'


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class UserSettingsViewSet(viewsets.ModelViewSet):
    queryset = UserSettings.objects.all()
    serializer_class = UserSettingsSerializer


def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Регистрация прошла успешно. Проверьте почту.')
            return redirect('login')
        else:
            messages.error(request, 'Ошибка при регистрации. Проверьте данные.')
    else:
        form = CustomUserCreationForm()
    return render(request, 'users/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        identifier = request.POST.get('username', '')
        password = request.POST.get('password', '')
        email_login = identifier
        if '@' not in identifier:
            u = User.objects.filter(username=identifier).order_by('id').first()
            if u:
                email_login = u.email or identifier

        user = authenticate(request, username=email_login, password=password)
        if user:
            login(request, user)
            if user.role == 'ROLE_ADMIN':
                return redirect('/admin/')
            return redirect('/')
        messages.error(request, 'Неверный логин или пароль.')
    return render(request, 'users/login.html')


def logout_view(request):
    logout(request)
    return redirect('/')


@login_required
def profile_view(request):
    settings = getattr(request.user, 'usersettings', None)
    return render(request, 'users/profile.html', {'user': request.user, 'settings': settings})


@login_required
def favorites_list(request):
    favs = Favorite.objects.filter(user=request.user).select_related(
        'shop_product', 'shop_product__product', 'shop_product__material'
    )
    return render(request, 'users/favorites.html', {'favorites': favs})


@login_required
@require_POST
def toggle_favorite(request, product_id):
    user = request.user
    product = get_object_or_404(ShopProduct, id=product_id)
    obj, created = Favorite.objects.get_or_create(user=user, shop_product=product)
    if not created:
        obj.delete()
        return JsonResponse({'added': False})
    return JsonResponse({'added': True})


@login_required
def profile_edit_view(request):
    user = request.user
    settings, _ = UserSettings.objects.get_or_create(user=user)
    if request.method == 'POST':
        profile_form = ProfileForm(request.POST, instance=user)
        settings_form = UserSettingsForm(request.POST, instance=settings)
        if profile_form.is_valid() and settings_form.is_valid():
            profile_form.save()
            settings_form.save()
            # Активируем язык
            language = settings_form.cleaned_data['language']
            theme = settings_form.cleaned_data['theme']
            translation.activate(language)
            request.session[LANGUAGE_SESSION_KEY] = language
            # Устанавливаем язык и тему в HTTP header для будущих запросов
            response = redirect('profile')
            response.set_cookie('django_language', language, max_age=3600*24*365)
            response.set_cookie('django_theme', theme, max_age=3600*24*365)
            messages.success(request, 'Профиль обновлён.' if language == 'ru' else 'Profile updated.')
            return response
    else:
        profile_form = ProfileForm(instance=user)
        settings_form = UserSettingsForm(instance=settings)
    return render(request, 'users/profile_edit.html', {
        'form': profile_form,
        'settings_form': settings_form,
    })


def set_language_view(request, language):
    """Устанавливает язык пользователя и сохраняет его в профиле"""
    if language not in dict(UserSettings.LANGUAGE_CHOICES):
        language = 'ru'
    
    # Если пользователь аутентифицирован, сохраняем в профиль
    if request.user.is_authenticated:
        user = request.user
        settings, _ = UserSettings.objects.get_or_create(user=user)
        settings.language = language
        settings.save()
    
    # Активируем язык
    translation.activate(language)
    request.session[LANGUAGE_SESSION_KEY] = language
    
    # Создаём ответ
    next_page = request.GET.get('next', '/')
    response = redirect(next_page)
    response.set_cookie('django_language', language, max_age=3600*24*365)
    
    return response


@login_required
def set_theme_view(request, theme):
    """Устанавливает тему пользователя и сохраняет её в профиле"""
    if theme not in dict(UserSettings.THEME_CHOICES):
        theme = 'light'
    
    user = request.user
    settings, _ = UserSettings.objects.get_or_create(user=user)
    settings.theme = theme
    settings.save()
    
    # Создаём ответ
    next_page = request.GET.get('next', '/')
    response = redirect(next_page)
    response.set_cookie('django_theme', theme, max_age=3600*24*365)
    
    return response
