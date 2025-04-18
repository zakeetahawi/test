from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _
from .models import Notification, Department, User

def send_notification(
    title, 
    message, 
    sender, 
    sender_department_code, 
    target_department_code, 
    target_branch=None, 
    priority='medium', 
    related_object=None
):
    """
    Send a notification from one department to another
    
    Args:
        title (str): Notification title
        message (str): Notification message
        sender (User): User sending the notification
        sender_department_code (str): Code of the sender's department
        target_department_code (str): Code of the target department
        target_branch (Branch, optional): Target branch. Defaults to None.
        priority (str, optional): Notification priority. Defaults to 'medium'.
        related_object (Model, optional): Related object. Defaults to None.
    
    Returns:
        Notification: The created notification
    """
    try:
        # Get departments
        sender_department = Department.objects.get(code=sender_department_code)
        target_department = Department.objects.get(code=target_department_code)
        
        # Create notification
        notification = Notification(
            title=title,
            message=message,
            priority=priority,
            sender=sender,
            sender_department=sender_department,
            target_department=target_department,
            target_branch=target_branch
        )
        
        # Add related object if provided
        if related_object:
            content_type = ContentType.objects.get_for_model(related_object)
            notification.content_type = content_type
            notification.object_id = related_object.pk
        
        notification.save()
        return notification
    
    except Department.DoesNotExist:
        # Log error
        print(f"Error: Department not found. Sender: {sender_department_code}, Target: {target_department_code}")
        return None
    except Exception as e:
        # Log error
        print(f"Error sending notification: {str(e)}")
        return None

def get_user_notifications(user, department_code=None, unread_only=False, limit=None):
    """
    Get notifications for a user
    
    Args:
        user (User): User to get notifications for
        department_code (str, optional): Filter by department code. Defaults to None.
        unread_only (bool, optional): Only return unread notifications. Defaults to False.
        limit (int, optional): Limit number of notifications. Defaults to None.
    
    Returns:
        QuerySet: Notifications for the user
    """
    # Base query - get notifications for user's departments
    if user.is_superuser:
        # Superuser can see all notifications
        notifications = Notification.objects.all()
    else:
        # Regular user can only see notifications for their departments
        user_departments = user.departments.filter(is_active=True)
        notifications = Notification.objects.filter(target_department__in=user_departments)
        
        # If user has a branch, also filter by branch
        if user.branch:
            branch_notifications = Notification.objects.filter(
                target_branch=user.branch
            )
            # Combine department and branch notifications
            notifications = (notifications | branch_notifications).distinct()
    
    # Apply filters
    if department_code:
        try:
            department = Department.objects.get(code=department_code)
            notifications = notifications.filter(target_department=department)
        except Department.DoesNotExist:
            # Return empty queryset if department doesn't exist
            return Notification.objects.none()
    
    if unread_only:
        notifications = notifications.filter(is_read=False)
    
    # Order by created_at (newest first)
    notifications = notifications.order_by('-created_at')
    
    # Apply limit if provided
    if limit:
        notifications = notifications[:limit]
    
    return notifications
