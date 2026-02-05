from django.conf import settings
from django.contrib import admin, messages
from django.core.management import call_command
from django.db.models.query import QuerySet
from django.shortcuts import redirect
from django.utils import timezone
from pathlib import Path
import tempfile
import os
import subprocess

from .models import ReportLog, AuditLog, BackupGuide


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('table_name', 'operation', 'user', 'timestamp', 'short_old', 'short_new')
    list_filter = ('table_name', 'operation', 'timestamp')
    search_fields = ('table_name', 'operation', 'old_value', 'new_value')
    readonly_fields = ('user', 'table_name', 'operation', 'timestamp', 'old_value', 'new_value')
    ordering = ('-timestamp',)

    def short_old(self, obj):
        return (obj.old_value or '')[:60] + ('…' if obj.old_value and len(obj.old_value) > 60 else '')

    short_old.short_description = 'До'

    def short_new(self, obj):
        return (obj.new_value or '')[:60] + ('…' if obj.new_value and len(obj.new_value) > 60 else '')

    short_new.short_description = 'После'


@admin.register(ReportLog)
class ReportLogAdmin(admin.ModelAdmin):
    list_display = ('report_name', 'report_type', 'user', 'created_at')
    readonly_fields = ('report_name', 'report_type', 'user', 'created_at', 'file_link')


@admin.register(BackupGuide)
class BackupGuideAdmin(admin.ModelAdmin):
    change_list_template = 'admin/backup_guide.html'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        return BackupGuide.objects.none()

    def changelist_view(self, request, extra_context=None):
        if request.method == 'POST':
            action = request.POST.get('action')
            if action == 'backup':
                self._run_backup(request)
                return redirect(request.path)
            if action == 'restore':
                self._run_restore(request)
                return redirect(request.path)
        context = extra_context or {}
        context['backup_files'] = self._list_backups()
        context['db_config'] = self._get_db_config()
        return super().changelist_view(request, extra_context=context)

    def _backup_dir(self):
        backup_dir = Path(settings.BASE_DIR) / 'backups'
        backup_dir.mkdir(exist_ok=True)
        return backup_dir

    def _list_backups(self):
        backup_dir = self._backup_dir()
        files = []
        for f in sorted(backup_dir.glob('backup_*.json'), reverse=True)[:5]:
            size = f.stat().st_size / (1024 * 1024)  # MB
            files.append({'name': f.name, 'size': f'{size:.1f}MB'})
        return files

    def _get_db_config(self):
        from django.db import connections
        db = connections.databases['default']
        return {
            'engine': db.get('ENGINE', ''),
            'name': db.get('NAME', ''),
            'user': db.get('USER', ''),
            'host': db.get('HOST', 'localhost'),
            'port': db.get('PORT', 5432),
        }

    def _run_backup(self, request):
        backup_dir = self._backup_dir()
        filename = backup_dir / f'backup_{timezone.now().strftime("%Y%m%d_%H%M%S")}.json'
        try:
            with open(filename, 'w', encoding='utf-8') as fh:
                call_command(
                    'dumpdata',
                    '--natural-foreign',
                    '--natural-primary',
                    '--exclude', 'contenttypes',
                    '--exclude', 'auth.Permission',
                    '--exclude', 'audit.BackupGuide',
                    stdout=fh,
                )
            messages.success(request, f'Бэкап успешно создан: <code>{filename.name}</code>')
        except Exception as exc:
            messages.error(request, f'Ошибка при создании бэкапа: {exc}')

    def _run_restore(self, request):
        uploaded = request.FILES.get('restore_file')
        if not uploaded:
            messages.error(request, 'Выберите файл с дампом для восстановления.')
            return
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.json', mode='w', encoding='utf-8') as tmp:
                for chunk in uploaded.chunks():
                    tmp.write(chunk.decode('utf-8'))
                tmp_path = tmp.name

            call_command('flush', '--noinput')

            request.session.flush()

            call_command('load_fixture_safe', tmp_path)

            call_command('fix_trigger')

            messages.success(request, 'Данные успешно восстановлены и триггеры БД исправлены. Пожалуйста, войдите снова.')
        except Exception as exc:
            messages.error(request, f'Ошибка при восстановлении: {exc}')
        finally:
            if 'tmp_path' in locals() and os.path.exists(tmp_path):
                os.remove(tmp_path)
