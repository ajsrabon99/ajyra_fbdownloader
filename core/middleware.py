# middleware.py
from .models import Visitor
import datetime

class VisitorTrackingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        ip = request.META.get("REMOTE_ADDR")
        ua = request.META.get("HTTP_USER_AGENT", "")
        if ip:
            Visitor.objects.create(ip_address=ip, user_agent=ua)
        return self.get_response(request)
