from django.urls import path
from app.views import current_user_view, marker_view, my_markers_view, register_view, user_list_view, user_markers_view
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('marker/', marker_view, name='marker_view'),
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/register/', register_view, name='register'),
    path('users/', user_list_view),
    path('markers/user/<int:user_id>/', user_markers_view),
    path("auth/me/", current_user_view),
    path('my-markers/', my_markers_view, name='my-markers'),
]
