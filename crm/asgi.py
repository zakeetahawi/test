"""
ASGI config for CRM project.
"""

import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm.settings')

application = get_asgi_application()

# تكوين Mangum للاستخدام في بيئات serverless (AWS Lambda / Netlify Functions) فقط
# يتم تشغيل هذا الجزء فقط إذا تم استدعاء التطبيق من بيئة serverless
try:
    from mangum import Mangum
    # تحقق ما إذا كنا نعمل في بيئة AWS Lambda أو Netlify Functions
    import os
    if 'AWS_LAMBDA_FUNCTION_NAME' in os.environ or 'NETLIFY' in os.environ:
        handler = Mangum(
            application,
            lifespan="off",
            api_gateway_base_path=None
        )
except ImportError:
    # في حالة عدم تثبيت Mangum، نستمر بشكل طبيعي
    pass
