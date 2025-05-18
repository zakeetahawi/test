"""
وسيط إنشاء المستخدم الافتراضي
"""

import logging
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.utils import OperationalError, ProgrammingError

logger = logging.getLogger(__name__)
User = get_user_model()

class DefaultUserMiddleware:
    """
    وسيط لإنشاء مستخدم افتراضي إذا لم يكن هناك مستخدمين في النظام
    """

    def __init__(self, get_response):
        self.get_response = get_response
        # تنفيذ عملية التهيئة مرة واحدة فقط عند بدء التطبيق
        self.initialized = False

    def __call__(self, request):
        # إنشاء المستخدم الافتراضي عند أول طلب فقط
        if not self.initialized:
            self.initialized = True
            self.create_default_user()

        response = self.get_response(request)
        return response

    def create_default_user(self):
        """
        إنشاء مستخدم افتراضي إذا لم يكن هناك مستخدمين في النظام
        """
        try:
            # التحقق من وجود مستخدمين في النظام
            user_count = User.objects.count()
            
            if user_count == 0:
                logger.info("لا يوجد مستخدمين في النظام. جاري إنشاء مستخدم افتراضي...")
                
                # إنشاء مستخدم افتراضي
                with transaction.atomic():
                    admin_user = User.objects.create_superuser(
                        username='admin',
                        email='admin@example.com',
                        password='admin',
                        first_name='مدير',
                        last_name='النظام'
                    )
                    
                logger.info(f"تم إنشاء مستخدم افتراضي بنجاح: {admin_user.username}")
            else:
                logger.info(f"يوجد {user_count} مستخدم في النظام. لا حاجة لإنشاء مستخدم افتراضي.")
        
        except (OperationalError, ProgrammingError) as e:
            # قد تحدث هذه الأخطاء إذا لم تكن الجداول موجودة بعد
            logger.warning(f"لم يتم إنشاء المستخدم الافتراضي: {str(e)}")
        except Exception as e:
            logger.error(f"حدث خطأ أثناء إنشاء المستخدم الافتراضي: {str(e)}")
