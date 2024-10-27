from rest_framework.permissions import BasePermission

class IsAuthenticatedOrToken(BasePermission):
    def has_permission(self, request, view):
        return bool(request.auth)