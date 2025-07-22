# app/serializer.py

from rest_framework import serializers
from app.models import Marker

class MarkerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Marker
        fields = ['id', 'lat', 'lng', 'created_by', 'created_at']
        read_only_fields = ['created_by', 'created_at']
