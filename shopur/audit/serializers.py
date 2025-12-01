from rest_framework import serializers
from .models import ReportLog, AuditLog

class ReportLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportLog
        fields = '__all__'

class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = '__all__'
