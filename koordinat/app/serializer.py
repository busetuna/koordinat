from rest_framework import serializers
from .models import Marker

class MarkerSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='created_by.username', read_only=True)

    class Meta:
        model = Marker
        fields = ['id', 'lat', 'lng', 'created_at', 'username']
