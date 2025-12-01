from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'settings', UserSettingsViewSet)

urlpatterns = [
  path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('profile/', profile_view, name='profile'),
    path('profile/edit/', profile_edit_view, name='profile_edit'),
    path('favorites/', favorites_list, name='favorites'),
    path('favorites/toggle/<int:product_id>/', toggle_favorite, name='toggle_favorite'),
    path('set-language/<str:language>/', set_language_view, name='set_language'),
    path('set-theme/<str:theme>/', set_theme_view, name='set_theme'),
    # password reset
    path('password-reset/', 
         __import__('django.contrib.auth.views').contrib.auth.views.PasswordResetView.as_view(template_name='users/password_reset_form.html'), 
         name='password_reset'),
    path('password-reset/cancel/',
         __import__('django.views.generic').views.generic.TemplateView.as_view(template_name='users/password_reset_cancel.html'),
         name='password_reset_cancel'),
    path('password-reset/done/', 
         __import__('django.contrib.auth.views').contrib.auth.views.PasswordResetDoneView.as_view(template_name='users/password_reset_done.html'), 
         name='password_reset_done'),
    path('reset/<uidb64>/<token>/', 
         __import__('django.contrib.auth.views').contrib.auth.views.PasswordResetConfirmView.as_view(template_name='users/password_reset_confirm.html'), 
         name='password_reset_confirm'),
    path('reset/done/', 
         __import__('django.contrib.auth.views').contrib.auth.views.PasswordResetCompleteView.as_view(template_name='users/password_reset_complete.html'), 
         name='password_reset_complete'),
    ]
