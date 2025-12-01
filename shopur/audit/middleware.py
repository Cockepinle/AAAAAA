from django.utils.deprecation import MiddlewareMixin
from .metrics import update_business_metrics


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
        except Exception:
            pass

        return None

   