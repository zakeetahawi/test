from mangum import Mangum
from crm.wsgi import application

handler = Mangum(application)