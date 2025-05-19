from django.core.management.base import BaseCommand
from django.contrib.sessions.models import Session
from django.utils import timezone
from datetime import timedelta
from django.db import connection, transaction
from django.contrib.auth import get_user_model
import logging

# إعداد التسجيل
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'تنظيف جلسات المستخدمين القديمة والمكررة والتحقق من المستخدمين المكررين'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=1,
            help='حذف الجلسات الأقدم من هذا العدد من الأيام'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='عرض التغييرات دون تنفيذها'
        )
        parser.add_argument(
            '--fix-users',
            action='store_true',
            help='إصلاح المستخدمين المكررين أيضًا'
        )

    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']
        fix_users = options['fix_users']

        self.stdout.write(f'جاري تنظيف الجلسات...')

        # حذف الجلسات المنتهية الصلاحية
        self.stdout.write(f'جاري حذف الجلسات الأقدم من {days} يوم...')

        # حساب التاريخ المستهدف
        cutoff_date = timezone.now() - timedelta(days=days)

        # حذف الجلسات المنتهية الصلاحية
        expired_sessions = Session.objects.filter(expire_date__lt=cutoff_date)
        count = expired_sessions.count()

        if not dry_run:
            expired_sessions.delete()
            self.stdout.write(self.style.SUCCESS(f'تم حذف {count} جلسة منتهية الصلاحية'))
        else:
            self.stdout.write(self.style.WARNING(f'سيتم حذف {count} جلسة منتهية الصلاحية (وضع المحاكاة)'))

        # البحث عن الجلسات المكررة
        self.stdout.write('جاري البحث عن الجلسات المكررة...')

        # استخدام استعلام SQL مباشر للبحث عن الجلسات المكررة
        with connection.cursor() as cursor:
            cursor.execute("""
            SELECT session_key, COUNT(*) as count
            FROM django_session
            GROUP BY session_key
            HAVING COUNT(*) > 1
            """)
            duplicate_sessions = cursor.fetchall()

        if duplicate_sessions:
            self.stdout.write(f'تم العثور على {len(duplicate_sessions)} جلسة مكررة')

            duplicate_count = 0
            for session_key, count in duplicate_sessions:
                sessions = Session.objects.filter(session_key=session_key).order_by('-expire_date')

                # الاحتفاظ بأحدث جلسة وحذف البقية
                if sessions.count() > 1:
                    primary_session = sessions.first()
                    duplicate_sessions_to_delete = sessions.exclude(id=primary_session.id)

                    if not dry_run:
                        duplicate_sessions_to_delete.delete()
                        duplicate_count += duplicate_sessions_to_delete.count()
                    else:
                        duplicate_count += duplicate_sessions_to_delete.count()

            if not dry_run:
                self.stdout.write(self.style.SUCCESS(f'تم حذف {duplicate_count} جلسة مكررة'))
            else:
                self.stdout.write(self.style.WARNING(f'سيتم حذف {duplicate_count} جلسة مكررة (وضع المحاكاة)'))
        else:
            self.stdout.write(self.style.SUCCESS('لا يوجد جلسات مكررة'))

        # إحصائيات نهائية
        remaining_count = Session.objects.count()
        self.stdout.write(f'عدد الجلسات المتبقية: {remaining_count}')

        # التحقق من المستخدمين المكررين إذا تم طلب ذلك
        if fix_users:
            self.stdout.write('جاري البحث عن المستخدمين المكررين...')
            logger.info('بدء عملية إصلاح المستخدمين المكررين')

            User = get_user_model()

            try:
                # استخدام استعلام SQL مباشر للبحث عن المستخدمين المكررين
                with connection.cursor() as cursor:
                    cursor.execute("""
                    SELECT username, COUNT(*) as count
                    FROM accounts_user
                    GROUP BY username
                    HAVING COUNT(*) > 1
                    """)
                    duplicate_users = cursor.fetchall()

                if duplicate_users:
                    self.stdout.write(f'تم العثور على {len(duplicate_users)} مستخدم مكرر')
                    logger.warning(f'تم العثور على {len(duplicate_users)} مستخدم مكرر')

                    # معالجة كل مستخدم مكرر على حدة
                    for username, count in duplicate_users:
                        self.stdout.write(f'معالجة المستخدم المكرر: {username} (عدد التكرارات: {count})')

                        # الحصول على جميع نسخ المستخدم مرتبة حسب تاريخ آخر تسجيل دخول
                        users = User.objects.filter(username=username).order_by('-last_login')

                        if users.count() > 1:
                            # الاحتفاظ بأحدث مستخدم (أول عنصر في القائمة)
                            primary_user = users.first()
                            duplicate_users_to_delete = users.exclude(id=primary_user.id)

                            self.stdout.write(f'الاحتفاظ بالمستخدم {primary_user.id} وحذف {duplicate_users_to_delete.count()} نسخة مكررة')

                            if not dry_run:
                                with transaction.atomic():
                                    # حذف المستخدمين المكررين
                                    for user in duplicate_users_to_delete:
                                        user.delete()

                                    self.stdout.write(self.style.SUCCESS(f'تم حذف {duplicate_users_to_delete.count()} نسخة مكررة للمستخدم {username}'))
                            else:
                                self.stdout.write(self.style.WARNING(f'سيتم حذف {duplicate_users_to_delete.count()} نسخة مكررة للمستخدم {username} (وضع المحاكاة)'))

                    # إعادة تعيين كلمة مرور المستخدم الافتراضي إذا كان موجوداً
                    try:
                        admin_user = User.objects.filter(username='admin').first()
                        if admin_user:
                            if not dry_run:
                                admin_user.set_password('admin')
                                admin_user.is_active = True
                                admin_user.is_staff = True
                                admin_user.is_superuser = True
                                admin_user.save()
                                self.stdout.write(self.style.SUCCESS('تم إعادة تعيين كلمة مرور المستخدم الافتراضي (admin)'))
                            else:
                                self.stdout.write(self.style.WARNING('سيتم إعادة تعيين كلمة مرور المستخدم الافتراضي (admin) (وضع المحاكاة)'))
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'خطأ أثناء إعادة تعيين كلمة مرور المستخدم الافتراضي: {str(e)}'))
                        logger.error(f'خطأ أثناء إعادة تعيين كلمة مرور المستخدم الافتراضي: {str(e)}')
                else:
                    self.stdout.write(self.style.SUCCESS('لا يوجد مستخدمين مكررين'))
                    logger.info('لا يوجد مستخدمين مكررين')
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'خطأ أثناء إصلاح المستخدمين المكررين: {str(e)}'))
                logger.error(f'خطأ أثناء إصلاح المستخدمين المكررين: {str(e)}')
