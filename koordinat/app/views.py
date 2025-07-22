from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from app.models import Marker
from app.serializer import MarkerSerializer
from django.contrib.auth.models import User
from rest_framework import status

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def marker_view(request):
    user = request.user

    if request.method == 'GET':
        try:
            if user.is_superuser:
                markers = Marker.objects.all()
            else:
                markers = Marker.objects.filter(created_by=user)

            serializer = MarkerSerializer(markers, many=True)
            return Response(serializer.data)
        except Exception as e:
            print("❌ Marker GET hatası:", e)
            return Response({'error': 'Internal server error'}, status=500)

    elif request.method == 'POST':
        serializer = MarkerSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(created_by=user)
            return Response({'status': 'saved'})
        return Response(serializer.errors, status=400)


@api_view(['POST'])
def register_view(request):
    username = request.data.get('username')
    password = request.data.get('password')

    if not username or not password:
        return Response({'error': 'Kullanıcı adı ve şifre gerekli'}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(username=username).exists():
        return Response({'error': 'Bu kullanıcı adı zaten kullanılıyor'}, status=status.HTTP_400_BAD_REQUEST)

    user = User.objects.create_user(username=username, password=password)
    return Response({'message': '✅ Kayıt başarılı'}, status=status.HTTP_201_CREATED)
