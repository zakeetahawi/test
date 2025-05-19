from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'إنشاء مستخدم مسؤول افتراضي إذا لم يكن هناك مستخدمين في النظام'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='إنشاء المستخدم حتى لو كان هناك مستخدمين آخرين',
        )

    def handle(self, *args, **options):
        force = options.get('force', False)
        
        try:
            with transaction.atomic():
                # التحقق مما إذا كان هناك مستخدمين في النظام
                if force or User.objects.count() == 0:
                    # إنشاء مستخدم مسؤول افتراضي
                    if not User.objects.filter(username='admin').exists():
                        User.objects.create_superuser('admin', 'admin@example.com', 'admin')
                        self.stdout.write(self.style.SUCCESS('تم إنشاء مستخدم مسؤول افتراضي بنجاح (اسم المستخدم: admin، كلمة المرور: admin)'))
                        logger.info('تم إنشاء مستخدم مسؤول افتراضي بنجاح')
                    else:
                        self.stdout.write(self.style.WARNING('المستخدم admin موجود بالفعل'))
                        logger.info('المستخدم admin موجود بالفعل')
                else:
                    self.stdout.write(self.style.WARNING('يوجد مستخدمين في النظام بالفعل، لم يتم إنشاء مستخدم مسؤول افتراضي'))
                    logger.info('يوجد مستخدمين في النظام بالفعل، لم يتم إنشاء مستخدم مسؤول افتراضي')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'حدث خطأ أثناء إنشاء المستخدم المسؤول: {str(e)}'))
            logger.error(f'حدث خطأ أثناء إنشاء المستخدم المسؤول: {str(e)}')
