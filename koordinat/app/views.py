from django.shortcuts import render
from rest_framework.response import Response
from app.models import Marker
from app.serializer import MarkerSerializer
from rest_framework.decorators import api_view

@api_view(['GET', 'POST'])
def marker_view(request):
    if request.method == 'GET':
        markers = Marker.objects.all()
        serializer = MarkerSerializer(markers, many=True)
        return Response(serializer.data)
    elif request.method == 'POST':
        serializer = MarkerSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'status': 'saved'})
        return Response(serializer.errors, status=400)
