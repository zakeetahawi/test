from django.apps import AppConfig
from django.db.models.signals import post_migrate


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'

    def ready(self):
        # Import signal handlers
        from . import signals  # noqa

        # Register post_migrate signal to create departments
        post_migrate.connect(self.create_departments, sender=self)

    def create_departments(self, *args, **kwargs):
        """
        Create departments after migration
        """
        from django.core.management import call_command
        try:
            # إنشاء الأقسام الأساسية
            from .core_departments import create_core_departments
            create_core_departments()
            print("Core departments created successfully after migration")

            # Call the create_departments command for any additional departments
            call_command('create_departments')
            print("Additional departments created successfully after migration")
        except Exception as e:
            print(f"Error creating departments: {e}")
