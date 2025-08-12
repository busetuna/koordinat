from django.http import JsonResponse
import requests
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from app.models import Marker, AdminAccess
from app.serializer import MarkerSerializer
from django.contrib.auth.models import User
from rest_framework import status
from django.apps import AppConfig
from datetime import datetime
import os
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

@api_view(['GET', 'POST', 'PATCH']) #Marker 
@permission_classes([IsAuthenticated])
def marker_view(request):
    user = request.user

    if request.method == 'GET':
        try:
            if user.is_superuser:
                markers = Marker.objects.all()
            else:
                followed_user_ids = AdminAccess.objects.filter(admin=user).values_list('user_id', flat=True)
                if followed_user_ids.exists():
                    markers = Marker.objects.filter(created_by__in=list(followed_user_ids) + [user.id])
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

    elif request.method == 'PATCH':
        marker_id = request.data.get('id')
        if not marker_id:
            return Response({'error': 'Marker ID gerekli'}, status=400)

        try:
            marker = Marker.objects.get(id=marker_id)
            if marker.created_by != user and not user.is_superuser:
                return Response({'error': 'Bu marker sizin değil'}, status=403)

            lat = request.data.get('lat')
            lng = request.data.get('lng')
            if lat is not None: marker.lat = lat
            if lng is not None: marker.lng = lng
            marker.save()

            return Response({'message': '✅ Marker güncellendi'})
        except Marker.DoesNotExist:
            return Response({'error': 'Marker bulunamadı'}, status=404)


@api_view(['POST']) #user
def register_view(request):
    username = request.data.get('username')
    password = request.data.get('password')

    if not username or not password:
        return Response({'error': 'Kullanıcı adı ve şifre gerekli'}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(username=username).exists():
        return Response({'error': 'Bu kullanıcı adı zaten kullanılıyor'}, status=status.HTTP_400_BAD_REQUEST)

    user = User.objects.create_user(username=username, password=password)
    return Response({'message': '✅ Kayıt başarılı'}, status=status.HTTP_201_CREATED)


@api_view(['POST']) #admin
@permission_classes([IsAuthenticated])
def add_access(request):
    if not request.user.is_staff:
        return Response({'error': 'Yetkisiz kullanıcı'}, status=403)

    target_username = request.data.get('username')
    try:
        target_user = User.objects.get(username=target_username)
        AdminAccess.objects.get_or_create(admin=request.user, user=target_user)
        return Response({'message': f"{target_username} erişime eklendi"})
    except User.DoesNotExist:
        return Response({'error': 'Kullanıcı bulunamadı'}, status=404)
    

@api_view(['GET']) #admin
@permission_classes([IsAuthenticated])
def user_list_view(request):
    if not request.user.is_staff and not request.user.is_superuser:
        return Response({'error': 'Yetkisiz erişim'}, status=403)

    users = User.objects.all().select_related('profile').values('id', 'username', 'profile__msisdn')
    return Response(list(users))



@api_view(['GET']) #admin
@permission_classes([IsAuthenticated])
def user_markers_view(request, user_id):
    if not request.user.is_staff and not request.user.is_superuser:
        return Response({'error': 'Yetkisiz erişim'}, status=403)

    try:
       
        start = request.GET.get('start')
        end = request.GET.get('end')

       
        markers = Marker.objects.filter(created_by__id=user_id)

      
        if start:
            try:
                start_date = datetime.fromisoformat(start)
                markers = markers.filter(created_at__gte=start_date)
            except ValueError:
                return Response({'error': 'Geçersiz start tarihi'}, status=400)

        if end:
            try:
                end_date = datetime.fromisoformat(end)
                markers = markers.filter(created_at__lte=end_date)
            except ValueError:
                return Response({'error': 'Geçersiz end tarihi'}, status=400)

        serializer = MarkerSerializer(markers, many=True)
        return Response(serializer.data)

    except Exception as e:
        print("❌ Marker filtreleme hatası:", e)
        return Response({'error': 'Markerlar alınamadı'}, status=500)

@api_view(['GET']) #user
@permission_classes([IsAuthenticated])
def my_markers_view(request):
    user = request.user

    try:
       
        start = request.GET.get('start')
        end = request.GET.get('end')

     
        if user.is_staff or user.is_superuser:
            markers = Marker.objects.all()
        else:
            markers = Marker.objects.filter(created_by=user)

      
        if start:
            try:
                start_date = datetime.fromisoformat(start)
                markers = markers.filter(created_at__gte=start_date)
            except ValueError:
                return Response({'error': 'Geçersiz start tarihi'}, status=400)

        if end:
            try:
                end_date = datetime.fromisoformat(end)
                markers = markers.filter(created_at__lte=end_date)
            except ValueError:
                return Response({'error': 'Geçersiz end tarihi'}, status=400)

        serializer = MarkerSerializer(markers, many=True)
        return Response(serializer.data)

    except Exception as e:
        print("❌ Marker filtreleme hatası:", e)
        return Response({'error': 'Veriler alınamadı'}, status=500)


@api_view(['GET']) #user
@permission_classes([IsAuthenticated])
def current_user_view(request):
    user = request.user
    return Response({
        'id': user.id,
        'username': user.username,
        'is_staff': user.is_staff,
        'is_superuser': user.is_superuser
    })

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Add custom claims
        token['username'] = user.username
        token['is_staff'] = user.is_staff
        return token

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class AppConfig(AppConfig):                                  
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app' 

    def ready(self):
        import app.signals
        import app.views                                                        


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def towers_in_bbox(request):
    OCID_KEY = os.environ.get("OCID_KEY") 
    bbox = request.GET.get('bbox')
    if not bbox:
        return JsonResponse({'error': 'bbox gerekli'}, status=400)
    try:
        r = requests.get(
            "https://opencellid.org/cell/getInArea",
            params={'key': OCID_KEY, 'BBOX': bbox, 'format': 'json'},
            timeout=10
        )
        return JsonResponse(r.json(), status=r.status_code, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=502)
