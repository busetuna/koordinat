import random
from django.db import models
from django.contrib.auth.models import User

class Marker(models.Model):
    lat = models.FloatField()
    lng = models.FloatField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE) #userId
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Marker({self.lat}, {self.lng}, {self.msisdn})"

#related name old.için admin.admin_access şeklinde ulaşılır.
class AdminAccess(models.Model):
    admin = models.ForeignKey(User, on_delete=models.CASCADE, related_name='admin_access')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='accessible_by')

    class Meta:
        unique_together = ('admin', 'user')

    def __str__(self):
        return f"{self.admin.username} takip ediyor: {self.user.username}"


def generate_msisdn():
    return "905" + "".join([str(random.randint(0, 9)) for _ in range(9)])


#user.profile.msisdn şeklinde erişilir.
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    msisdn = models.CharField(max_length=20, unique=True, default=generate_msisdn)

    def __str__(self):
        return f"{self.user.username} - {self.msisdn}"