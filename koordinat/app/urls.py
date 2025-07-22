from django.urls import path
from app.views import marker_view

urlpatterns = [
    path('marker/', marker_view, name='marker_view'),
   # path('marker/save/', save_marker, name='save_marker'),
   
]
