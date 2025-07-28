from django.apps import AppConfig

class AppConfig(AppConfig):  # Class adı senin app adına göre olabilir ama AppConfig olmalı
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app'  # bu senin uygulama klasörünün adıyla aynı olmalı

    def ready(self):
        import app.signals
