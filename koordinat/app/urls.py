from django.urls import path
from app.views import current_user_view, marker_view, my_markers_view, register_view, user_list_view, user_markers_view
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from .views_tower import towers_in_bbox

schema_view = get_schema_view(
   openapi.Info(
      title="Your API Title",
      default_version='v1',
      description="Test description",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="contact@yourapi.local"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
)

urlpatterns = [
    path('marker/', marker_view, name='marker_view'),
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/register/', register_view, name='register'),
    path('users/', user_list_view),
    path('markers/user/<int:user_id>/', user_markers_view),
    path("auth/me/", current_user_view),
    path('my-markers/', my_markers_view, name='my-markers'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('towers/', towers_in_bbox, name='towers-in-bbox')
]
