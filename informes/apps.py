from django.apps import AppConfig


class InformesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "informes"

    def ready(self):
        # Registrar modelos adicionales para que Django los descubra
        import informes.models_demo  # noqa: F401
