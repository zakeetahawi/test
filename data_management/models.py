"""
نماذج تطبيق إدارة البيانات
"""

from django.db import models
from django.utils.translation import gettext_lazy as _

# استيراد النماذج من الوحدات الفرعية
from .modules.import_export.models import *
from .modules.backup.models import *
from .modules.db_manager.models import *
