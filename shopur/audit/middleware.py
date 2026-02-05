from django.utils.deprecation import MiddlewareMixin
from .metrics import update_business_metrics
from .metrics_influx import push_to_influx


class BusinessMetricsMiddleware(MiddlewareMixin):
    IGNORED_PATH_PREFIXES = (
        "/static/",
        "/media/",
        "/metrics",  
    )

    def process_request(self, request):
        path = request.path

        if any(path.startswith(p) for p in self.IGNORED_PATH_PREFIXES):
            return None

        try:
            update_business_metrics()

            push_to_influx()

        except Exception as e:
            print("Ошибка обновления/отправки метрик:", e)

        return None
