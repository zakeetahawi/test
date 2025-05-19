import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import dj_database_url
# import django

# Excluir Debug Toolbar cuando se ejecutan pruebas
TESTING = len(sys.argv) > 1 and sys.argv[1] == 'test'

# تحميل متغيرات البيئة من ملف .env
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
# تفعيل وضع التطوير بشكل دائم للكشف عن الأخطاء
DEBUG = os.environ.get('DEBUG', 'True').lower() in ['true', 't', '1', 'yes', 'y']

# تفعيل تتبع الأخطاء في الإنتاج
RAILWAY_DEBUG = os.environ.get('RAILWAY_DEBUG', 'True').lower() in ['true', 't', '1', 'yes', 'y']

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1,web-production-f91f.up.railway.app').split(',')

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',  # إضافة مكتبة التنسيق البشري
    'widget_tweaks',
    'accounts',
    'customers',
    'factory',
    'inspections',
    'installations',
    'inventory',
    'orders',
    'reports',
    'data_management.apps.DataManagementConfig',  # تطبيق إدارة البيانات الموحد
    'corsheaders',
    'django_apscheduler', # إضافة مكتبة جدولة المهام
    'dbbackup',  # إضافة تطبيق النسخ الاحتياطي
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist'  # إضافة دعم القائمة السوداء للتوكن
]

# Authentication backends
AUTHENTICATION_BACKENDS = [
    'accounts.backends.CustomModelBackend',
    'django.contrib.auth.backends.ModelBackend',
]


if not TESTING and DEBUG:
    INSTALLED_APPS += ['debug_toolbar']

AUTH_USER_MODEL = 'accounts.User'

# قائمة الوسطاء الأساسية
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'crm.middleware.CustomGZipMiddleware',  # وسيط الضغط المخصص
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'crm.middleware.PerformanceMiddleware',  # وسيط قياس وتحسين الأداء
    'crm.middleware.LazyLoadMiddleware',  # وسيط التحميل الكسول للصور
    'data_management.modules.db_manager.middleware.DefaultUserMiddleware',  # وسيط إنشاء المستخدم الافتراضي
    'data_management.middleware.RailwayDebugMiddleware',  # وسيط تتبع الأخطاء في Railway
]

if DEBUG:
    MIDDLEWARE.extend([
        'debug_toolbar.middleware.DebugToolbarMiddleware',
        'crm.middleware.QueryPerformanceMiddleware',
        'crm.middleware.PerformanceCookiesMiddleware',
    ])

ROOT_URLCONF = 'crm.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'accounts.context_processors.departments',
                'accounts.context_processors.notifications',
                'accounts.context_processors.company_info',
                'accounts.context_processors.footer_settings',
                'accounts.context_processors.system_settings',
                'data_management.context_processors.data_management_urls',
            ],
        },
    },
]

ASGI_APPLICATION = 'crm.asgi.application'
WSGI_APPLICATION = 'crm.wsgi.application'

# Channels configuration
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/0")],
        },
    },
}

# Database
# تحميل إعدادات قاعدة البيانات من الملف الخارجي
try:
    from data_management.db_settings import get_active_database_settings, reset_to_default_settings

    # الحصول على إعدادات قاعدة البيانات النشطة
    db_settings = get_active_database_settings()
    active_db_id = db_settings.get('active_db')

    if active_db_id and str(active_db_id) in db_settings.get('databases', {}):
        # استخدام إعدادات قاعدة البيانات النشطة
        active_db_settings = db_settings['databases'][str(active_db_id)]

        # تحقق من وجود معلمة reset_db في عنوان URL
        if os.environ.get('RESET_DB') == '1':
            # إعادة تعيين إعدادات قاعدة البيانات إلى الإعدادات الافتراضية
            reset_to_default_settings()
            print("تم إعادة تعيين إعدادات قاعدة البيانات إلى الإعدادات الافتراضية")

            # استخدام إعدادات قاعدة البيانات الافتراضية
            DATABASES = {
                'default': dj_database_url.config(
                    default=os.environ.get('DATABASE_URL', f"postgresql://{os.environ.get('DB_USER', 'crm_user')}:{os.environ.get('DB_PASSWORD', '5525')}@{os.environ.get('DB_HOST', 'localhost')}:{os.environ.get('DB_PORT', '5432')}/{os.environ.get('DB_NAME', 'crm_system')}"),
                    conn_max_age=600,
                    conn_health_checks=True,
                )
            }
        else:
            # استخدام إعدادات قاعدة البيانات النشطة
            DATABASES = {
                'default': {
                    'ENGINE': active_db_settings.get('ENGINE', 'django.db.backends.postgresql'),
                    'NAME': active_db_settings.get('NAME', 'crm_system'),
                    'USER': active_db_settings.get('USER', 'crm_user'),
                    'PASSWORD': active_db_settings.get('PASSWORD', '5525'),
                    'HOST': active_db_settings.get('HOST', 'localhost'),
                    'PORT': active_db_settings.get('PORT', '5432'),
                    'ATOMIC_REQUESTS': False,
                    'AUTOCOMMIT': True,
                    'CONN_MAX_AGE': 600,
                    'CONN_HEALTH_CHECKS': True,
                }
            }

            print(f"تم تحميل إعدادات قاعدة البيانات النشطة: {active_db_settings.get('NAME')}")
    else:
        # استخدام إعدادات قاعدة البيانات الافتراضية
        DATABASES = {
            'default': dj_database_url.config(
                default=os.environ.get('DATABASE_URL', f"postgresql://{os.environ.get('DB_USER', 'crm_user')}:{os.environ.get('DB_PASSWORD', '5525')}@{os.environ.get('DB_HOST', 'localhost')}:{os.environ.get('DB_PORT', '5432')}/{os.environ.get('DB_NAME', 'crm_system')}"),
                conn_max_age=600,
                conn_health_checks=True,
            )
        }

        print("تم تحميل إعدادات قاعدة البيانات الافتراضية")
except Exception as e:
    # في حالة حدوث خطأ، استخدم الإعدادات الافتراضية
    DATABASES = {
        'default': dj_database_url.config(
            default=os.environ.get('DATABASE_URL', f"postgresql://{os.environ.get('DB_USER', 'crm_user')}:{os.environ.get('DB_PASSWORD', '5525')}@{os.environ.get('DB_HOST', 'localhost')}:{os.environ.get('DB_PORT', '5432')}/{os.environ.get('DB_NAME', 'crm_system')}"),
            conn_max_age=600,
            conn_health_checks=True,
        )
    }

    print(f"حدث خطأ أثناء تحميل إعدادات قاعدة البيانات: {str(e)}")

    # محاولة إعادة تعيين إعدادات قاعدة البيانات إلى الإعدادات الافتراضية
    try:
        from data_management.db_settings import reset_to_default_settings
        reset_to_default_settings()
        print("تم إعادة تعيين إعدادات قاعدة البيانات إلى الإعدادات الافتراضية")
    except Exception as reset_error:
        print(f"حدث خطأ أثناء إعادة تعيين إعدادات قاعدة البيانات: {str(reset_error)}")

# إضافة إعدادات إضافية لقاعدة البيانات
DATABASES['default']['ATOMIC_REQUESTS'] = False
DATABASES['default']['AUTOCOMMIT'] = True

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'ar'
TIME_ZONE = 'Africa/Cairo'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]
# استخدام تخزين أبسط لتجنب مشاكل ملفات source map
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# إعدادات النسخ الاحتياطي
BACKUP_ROOT = os.path.join(BASE_DIR, 'backups')
os.makedirs(BACKUP_ROOT, exist_ok=True)

# استخدام نفس المجلد للملفات المؤقتة والنسخ الاحتياطية
DBBACKUP_TMP_DIR = BACKUP_ROOT
DBBACKUP_STORAGE = 'django.core.files.storage.FileSystemStorage'
DBBACKUP_STORAGE_OPTIONS = {'location': BACKUP_ROOT}
DBBACKUP_CLEANUP_KEEP = 5  # الاحتفاظ بآخر 5 نسخ احتياطية فقط

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Authentication settings
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# Cache settings
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
        'TIMEOUT': 300,  # 5 minutes
        'OPTIONS': {
            'MAX_ENTRIES': 500,  # تقليل عدد العناصر المخزنة لتوفير الذاكرة
            'CULL_FREQUENCY': 2,  # زيادة تكرار التنظيف
        }
    }
}

# REST Framework settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'crm.auth.CustomJWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'EXCEPTION_HANDLER': 'rest_framework.views.exception_handler',
}

# إعدادات JWT (Simple JWT)
from datetime import timedelta
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_COOKIE': 'access_token',
    'AUTH_COOKIE_HTTP_ONLY': True,
    'AUTH_COOKIE_PATH': '/',
    'AUTH_COOKIE_SAMESITE': 'Lax',
}

# Security Settings for Production
if not DEBUG and os.environ.get('ENABLE_SSL_SECURITY', 'false').lower() == 'true':
    # HTTPS/SSL Settings
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')  # مهم لـ Railway

    # Session and CSRF Settings
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    CSRF_COOKIE_HTTPONLY = True

    # HSTS Settings
    SECURE_HSTS_SECONDS = 31536000  # سنة واحدة
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

    # Content Security Settings
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'

    # Referrer Policy
    SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

    # Cross-Origin Opener Policy
    SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'

    # Additional Security Headers
    CSRF_TRUSTED_ORIGINS = [
        'https://*.up.railway.app',  # للسماح بالوصول من تطبيقات Railway
    ]

# CORS settings
CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',
    'http://127.0.0.1:3000',
    'http://localhost:5173',  # منفذ Vite الافتراضي
    'http://127.0.0.1:5173',  # منفذ Vite الافتراضي
    'http://localhost:8000',
    'http://127.0.0.1:8000',
    'https://*.up.railway.app',
    'https://*.railway.app'
]

# تعديل إعدادات CORS الإضافية
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True
CORS_EXPOSE_HEADERS = ['*']

CORS_ALLOW_HEADERS = [
    'Authorization',
    'Content-Type',
    'X-CSRFToken',
    'accept',
    'accept-encoding',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-requested-with',
    'x-request-id',  # إضافة هذا الرأس المطلوب
]

# تعطيل بعض إعدادات الأمان في بيئة التطوير
if DEBUG:
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
    CORS_ALLOW_ALL_ORIGINS = True
    CORS_ALLOW_CREDENTIALS = True
    JWT_AUTH_COOKIE_SECURE = False
    JWT_AUTH_SECURE = False

# Disable CSRF for /api/ endpoints in development
if DEBUG:
    CSRF_TRUSTED_ORIGINS = [
        'http://localhost:3000',
        'http://127.0.0.1:3000',
        'http://localhost:5173',  # منفذ Vite الافتراضي
        'http://127.0.0.1:5173',  # منفذ Vite الافتراضي
        'http://localhost:8000',
        'http://127.0.0.1:8000'
    ]

    class DisableCSRFMiddleware:
        def __init__(self, get_response):
            self.get_response = get_response

        def __call__(self, request):
            if request.path.startswith('/api/'):
                setattr(request, '_dont_enforce_csrf_checks', True)
            return self.get_response(request)

    MIDDLEWARE.insert(0, 'crm.settings.DisableCSRFMiddleware')

# Session settings
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_SECURE = False
SESSION_COOKIE_HTTPONLY = True

# DEBUG is set from environment variable at the top of the file
# Do not override it here

# تحديث إعدادات CSRF
CSRF_TRUSTED_ORIGINS = [
    'http://localhost:3000',
    'http://127.0.0.1:3000',
    'http://localhost:5173',  # منفذ Vite الافتراضي
    'http://127.0.0.1:5173',  # منفذ Vite الافتراضي
    'http://localhost:8000',
    'http://127.0.0.1:8000',
    'https://*.up.railway.app',
    'https://*.railway.app'
]

CSRF_COOKIE_SAMESITE = None
CSRF_COOKIE_HTTPONLY = False
CSRF_USE_SESSIONS = False
CSRF_COOKIE_SECURE = False

# تحديث إعدادات Session
SESSION_COOKIE_SAMESITE = None
SESSION_COOKIE_SECURE = False
SESSION_COOKIE_HTTPONLY = True

# إضافة إعدادات CORS_ORIGIN_WHITELIST
CORS_ORIGIN_WHITELIST = [
    'http://localhost:3000',
    'http://127.0.0.1:3000',
    'http://localhost:5173',  # منفذ Vite الافتراضي
    'http://127.0.0.1:5173',  # منفذ Vite الافتراضي
    'http://localhost:8000',
    'http://127.0.0.1:8000',
    'https://*.up.railway.app',
    'https://*.railway.app'
]

# Security Settings
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_HTTPONLY = False  # Must be False to allow JavaScript access
CSRF_COOKIE_SECURE = True if not DEBUG else False
SESSION_COOKIE_SECURE = True if not DEBUG else False

# إعدادات جدولة المهام
APSCHEDULER_DATETIME_FORMAT = "N j, Y, f:s a"
APSCHEDULER_RUN_NOW_TIMEOUT = 25  # Seconds

# تكوين المهام المجدولة
SCHEDULER_CONFIG = {
    "apscheduler.jobstores.default": {
        "class": "django_apscheduler.jobstores:DjangoJobStore"
    },
    "apscheduler.executors.processpool": {
        "type": "threadpool",
        "max_workers": 5
    },
    "apscheduler.job_defaults.coalesce": "false",
    "apscheduler.job_defaults.max_instances": "3",
    "apscheduler.timezone": TIME_ZONE,
}

# تكوين مهمة تنظيف الجلسات
SESSION_CLEANUP_SCHEDULE = {
    'days': 1,  # تنظيف الجلسات الأقدم من يوم واحد
    'fix_users': True,  # إصلاح المستخدمين المكررين أيضًا
    'frequency': 'daily',  # تنفيذ المهمة يوميًا
    'hour': 3,  # تنفيذ المهمة في الساعة 3 صباحًا
    'minute': 0,  # تنفيذ المهمة في الدقيقة 0
}

# إعدادات تحسين الأداء لـ Railway
if os.environ.get('RAILWAY_ENVIRONMENT') or 'railway' in os.environ.get('PGHOST', ''):
    # تقليل عدد الاستعلامات المسموح بها في صفحة واحدة
    DATA_UPLOAD_MAX_NUMBER_FIELDS = 1000

    # تعطيل التسجيل المفصل في الإنتاج
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': 'INFO',  # تغيير مستوى التسجيل إلى INFO للحصول على مزيد من المعلومات
            },
        },
        'loggers': {
            'django': {
                'handlers': ['console'],
                'level': 'INFO',
                'propagate': True,
            },
            'django.db.backends': {
                'handlers': ['console'],
                'level': 'WARNING',
                'propagate': False,
            },
            'data_management': {  # إضافة تسجيل خاص لتطبيق data_management
                'handlers': ['console'],
                'level': 'INFO',
                'propagate': True,
            },
        },
        'root': {
            'handlers': ['console'],
            'level': 'INFO',
        },
    }

    # تقليل عدد الاتصالات المتزامنة بقاعدة البيانات
    DATABASES['default']['CONN_MAX_AGE'] = 300  # 5 دقائق

    # تعطيل التصحيح التلقائي للمخطط
    DATABASES['default']['AUTOCOMMIT'] = True  # تمكين AUTOCOMMIT لتجنب مشاكل الاتصال

    # إعدادات قاعدة بيانات Railway
    # إذا كانت متغيرات البيئة متوفرة، استخدمها مباشرة
    if os.environ.get('PGHOST') and os.environ.get('PGDATABASE') and os.environ.get('PGUSER'):
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': os.environ.get('PGDATABASE', 'railway'),
                'USER': os.environ.get('PGUSER', 'postgres'),
                'PASSWORD': os.environ.get('PGPASSWORD') or os.environ.get('POSTGRES_PASSWORD', ''),
                'HOST': os.environ.get('PGHOST', 'postgres.railway.internal'),
                'PORT': os.environ.get('PGPORT', '5432'),
                'ATOMIC_REQUESTS': False,
                'AUTOCOMMIT': True,
                'CONN_MAX_AGE': 300,
                'CONN_HEALTH_CHECKS': True,
            }
        }
        print(f"تم تكوين قاعدة بيانات Railway: {os.environ.get('PGDATABASE')} على {os.environ.get('PGHOST')}")
    else:
        print("متغيرات بيئة Railway غير متوفرة، استخدام الإعدادات الافتراضية")
