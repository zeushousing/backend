from rest_framework.views import exception_handler
from rest_framework.exceptions import ValidationError, AuthenticationFailed, PermissionDenied

def custom_exception_handler(exc, context):
    # Call the default DRF exception handler first
    response = exception_handler(exc, context)

    # If no response (unhandled exception), create one
    if response is None:
        return response

    # Customize the response format
    error_response = {
        'status': 'error',
        'message': str(exc),
        'code': response.status_code,
    }

    # Handle specific exceptions with custom messages
    if isinstance(exc, ValidationError):
        error_response['message'] = 'Validation failed'
        error_response['details'] = response.data
    elif isinstance(exc, AuthenticationFailed):
        error_response['message'] = 'Authentication failed. Please check your credentials.'
    elif isinstance(exc, PermissionDenied):
        error_response['message'] = 'You do not have permission to perform this action.'

    response.data = error_response
    return response