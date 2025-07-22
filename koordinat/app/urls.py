from django.urls import path
from app.views import marker_view, register_view
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('marker/', marker_view, name='marker_view'),
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/register/', register_view, name='register'),
    # path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
