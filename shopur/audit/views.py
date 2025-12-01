from rest_framework import viewsets
from .models import ReportLog, AuditLog
from .serializers import *

class ReportLogViewSet(viewsets.ModelViewSet):
    queryset = ReportLog.objects.all()
    serializer_class = ReportLogSerializer

class AuditLogViewSet(viewsets.ModelViewSet):
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
