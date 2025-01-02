from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.models import User
from django.http import JsonResponse
from support.models import SupportSession

class SupportSessionMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # Ensure the user is authenticated
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=401)

        # Check if the user already has an active support session
        support_session = SupportSession.objects.filter(user=request.user, is_active=True).first()
        if not support_session:
            # Create a new session if none exists
            support_session = SupportSession.objects.create(user=request.user)

        # Attach the session to the request for further use
        request.support_session = support_session
