from django.contrib import admin
from .models import Marker, UserProfile  # Marker modelini de ekliyoruz

class MarkerAdmin(admin.ModelAdmin):
    list_display = ('lat', 'lng', 'get_msisdn', 'created_at')
    list_filter = ('created_by__profile__msisdn',)
    search_fields = ('created_by__profile__msisdn',)

    def get_msisdn(self, obj):
        return obj.created_by.profile.msisdn
    get_msisdn.short_description = 'MSISDN'


admin.site.register(Marker, MarkerAdmin)
admin.site.register(UserProfile)
