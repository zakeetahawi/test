from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()

class Command(BaseCommand):
    help = 'إنشاء مستخدم افتراضي للنظام'

    def handle(self, *args, **options):
        username = 'admin'
        password = 'admin'
        email = 'admin@example.com'

        try:
            with transaction.atomic():
                # التحقق من وجود المستخدم
                if User.objects.filter(username=username).exists():
                    self.stdout.write(self.style.WARNING(f'المستخدم {username} موجود بالفعل'))
                    return

                # إنشاء المستخدم
                user = User.objects.create_superuser(
                    username=username,
                    email=email,
                    password=password
                )

                self.stdout.write(self.style.SUCCESS(f'تم إنشاء المستخدم {username} بنجاح'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'حدث خطأ أثناء إنشاء المستخدم: {str(e)}'))
