from django.apps import AppConfig


class BaseConfig(AppConfig):
    name = 'base'

    def ready(self):
        from . import checks  # noqa: F401 — registra checar_dados_institucionais
