import json
import traceback
from django.http import HttpResponse
from django.conf import settings

class DebugMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Process the request
        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        if settings.DEBUG:
            # Print the exception details
            print("\n\n=== EXCEPTION DETAILS ===")
            print(f"Exception Type: {type(exception).__name__}")
            print(f"Exception Message: {str(exception)}")
            print(f"Request Path: {request.path}")
            print(f"Request Method: {request.method}")
            
            # Print request data
            print("\n=== REQUEST DATA ===")
            print(f"GET Parameters: {request.GET}")
            
            if request.method == 'POST':
                print("\n=== POST DATA ===")
                for key, value in request.POST.items():
                    # Limit the output length for large values
                    if isinstance(value, str) and len(value) > 1000:
                        print(f"{key}: {value[:1000]}... (truncated)")
                    else:
                        print(f"{key}: {value}")
            
            # Print traceback
            print("\n=== TRACEBACK ===")
            traceback.print_exc()
            print("=====================\n\n")
            
            # Return a detailed error response in development
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return HttpResponse(
                    json.dumps({
                        'error': str(exception),
                        'type': type(exception).__name__,
                        'traceback': traceback.format_exc()
                    }),
                    content_type='application/json',
                    status=500
                )
        
        # Let Django handle the exception
        return None
