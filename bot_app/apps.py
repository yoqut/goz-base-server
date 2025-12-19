# apps.py
from django.apps import AppConfig



class BotAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'bot_app'

    def ready(self):
        import bot_app.signals
        print("Signals imported")
