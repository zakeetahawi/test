import os
import sys
import logging
from django.core.asgi import get_asgi_application
from mangum import Mangum

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('django_asgi')

# Set up Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm.settings')
logger.info("Initializing ASGI application")

try:
    # Get the ASGI application
    django_asgi_app = get_asgi_application()
    logger.info("Successfully initialized Django ASGI application")

    # Create Mangum handler with custom settings
    handler = Mangum(
        django_asgi_app,
        lifespan="off",
        api_gateway_base_path=None,
        enable_lifespan=False,
        http_keep_alive=False
    )
    logger.info("Successfully created Mangum handler")

    # Export handler for AWS Lambda / Netlify Functions
    application = handler

except Exception as e:
    logger.error(f"Failed to initialize ASGI application: {str(e)}", exc_info=True)
    raise
