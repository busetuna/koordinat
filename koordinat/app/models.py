from django.db import models
from django.contrib.auth.models import User

class Marker(models.Model):
    lat = models.FloatField()
    lng = models.FloatField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Marker({self.lat}, {self.lng})"
    

class AdminAccess(models.Model):
    admin = models.ForeignKey(User, on_delete=models.CASCADE, related_name='admin_access')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='accessible_by')

    class Meta:
        unique_together = ('admin', 'user') 

    def __str__(self):
        return f"{self.admin.username} takip ediyor: {self.user.username}"
