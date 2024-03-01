from rest_framework.permissions import BasePermission, SAFE_METHODS
from rest_framework.exceptions import AuthenticationFailed
from .models import BlacklistedToken


class IsBlacklistedToken(BasePermission):

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True

        access_token = request.META.get("HTTP_AUTHORIZATION").split(' ')[1]
        
        if BlacklistedToken.objects.filter(user=request.user.id, token=access_token).exists():
                raise AuthenticationFailed("User not authenticated")    
        return True