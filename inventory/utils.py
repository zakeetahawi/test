from django.contrib.auth.models import Group
from .models import AuditLog

def user_is_inventory_manager(user):
    """
    Returns True if the user is a superuser or belongs to the 'مدير المخزون' group.
    """
    if user.is_superuser:
        return True
    return user.groups.filter(name='مدير المخزون').exists()


def log_audit_action(user, action, object_type, object_id, description=""):
    """
    Utility function to log audit actions for inventory operations.
    """
    AuditLog.objects.create(
        user=user if user.is_authenticated else None,
        action=action,
        object_type=object_type,
        object_id=str(object_id),
        description=description
    )
