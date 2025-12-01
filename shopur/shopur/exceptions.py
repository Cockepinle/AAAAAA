import logging
from django.core.exceptions import PermissionDenied
from django.db import DatabaseError, IntegrityError
from django.http import Http404
from rest_framework import status
from rest_framework.exceptions import NotFound, ParseError, ValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

logger = logging.getLogger(__name__)


def _humanize_details(details):
    if isinstance(details, list):
        return ', '.join(str(item) for item in details)
    if isinstance(details, dict):
        flattened = []
        for field, value in details.items():
            if isinstance(value, (list, tuple)):
                flattened.append(f'{field}: {value[0]}')
            else:
                flattened.append(f'{field}: {value}')
        return '; '.join(flattened)
    return str(details)


def custom_exception_handler(exc, context):
    response = drf_exception_handler(exc, context)

    if isinstance(exc, ValidationError):
        message = 'Данные не прошли проверку. Исправьте ошибки и повторите запрос.'
        code = status.HTTP_400_BAD_REQUEST
        details = exc.detail
    elif isinstance(exc, ParseError):
        message = 'Не удалось разобрать JSON. Проверьте синтаксис запроса.'
        code = status.HTTP_400_BAD_REQUEST
        details = {'detail': str(exc)}
    elif isinstance(exc, NotFound):
        message = 'Запрашиваемый ресурс не найден.'
        code = status.HTTP_404_NOT_FOUND
        details = {'detail': str(exc)}
    elif response is not None and response.status_code == status.HTTP_404_NOT_FOUND:
        message = 'Запрашиваемый ресурс не найден.'
        code = response.status_code
        details = response.data
    elif response is not None:
        message = {
            status.HTTP_401_UNAUTHORIZED: 'Требуется авторизация.',
            status.HTTP_403_FORBIDDEN: 'Недостаточно прав для выполнения операции.',
        }.get(response.status_code, _humanize_details(response.data.get('detail', response.data)))
        code = response.status_code
        details = response.data
    elif isinstance(exc, (IntegrityError, DatabaseError)):
        logger.exception('Database error: %s', exc)
        message = 'Произошла внутренняя ошибка базы данных. Повторите запрос позже.'
        code = status.HTTP_500_INTERNAL_SERVER_ERROR
        details = {'detail': str(exc)}
    elif isinstance(exc, PermissionDenied):
        message = 'Недостаточно прав для выполнения операции.'
        code = status.HTTP_403_FORBIDDEN
        details = {}
    elif isinstance(exc, Http404):
        message = 'Запрашиваемый ресурс не найден.'
        code = status.HTTP_404_NOT_FOUND
        details = {}
    else:
        logger.exception('Unhandled API exception: %s', exc)
        message = 'Неизвестная ошибка сервера. Мы уже работаем над её исправлением.'
        code = status.HTTP_500_INTERNAL_SERVER_ERROR
        details = {'detail': str(exc)}

    return Response(
        {'error_code': code, 'message': message, 'details': details},
        status=code,
    )
