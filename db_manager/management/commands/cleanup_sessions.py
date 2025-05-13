from django.core.management.base import BaseCommand
from django.contrib.sessions.models import Session
from django.utils import timezone
from datetime import timedelta
from django.db import connection


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

                if not dry_run:
                    # حذف المستخدمين المكررين
                    with connection.cursor() as cursor:
                        cursor.execute("""
                        DELETE FROM accounts_user
                        WHERE id IN (
                            SELECT id
                            FROM (
                                SELECT id,
                                       ROW_NUMBER() OVER (PARTITION BY username ORDER BY id) as row_num
                                FROM accounts_user
                            ) t
                            WHERE t.row_num > 1
                        )
                        """)

                        # الحصول على عدد الصفوف المتأثرة
                        affected_rows = cursor.rowcount

                        self.stdout.write(self.style.SUCCESS(f'تم حذف {affected_rows} مستخدم مكرر'))
                else:
                    self.stdout.write(self.style.WARNING(f'سيتم حذف {len(duplicate_users)} مستخدم مكرر (وضع المحاكاة)'))
            else:
                self.stdout.write(self.style.SUCCESS('لا يوجد مستخدمين مكررين'))
