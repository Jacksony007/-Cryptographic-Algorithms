from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
import django.utils.timezone as timezone
from django.conf import settings

from .models import Account, EncryptionKey, BlacklistedToken
from .serializers import AccountSerializer, LoginSerializer
from .permissions import IsBlacklistedToken
from .helper import get_user, deliver_email


class RegisterAccountView(APIView):
    permission_classes = [AllowAny]
    serializer_class = AccountSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()

            # create EncryptionKey object for account
            EncryptionKey.objects.create(
                user=Account.objects.get(username=serializer.validated_data["username"]),
                num_incorrect=0
            )

            # send email containing private key to user
            response_data = serializer.data
            private_key_path = f'{settings.MEDIA_ROOT}\keys\private_keys\{response_data["username"]}_private_key.pem'

            subject = f'CryptographyLibra Private Key for {response_data["username"].capitalize()}'
            message = f"Dear {response_data['username'].capitalize()}, please find attach your private key. \nYou'll need your private key to login and share messages with your friends and allies alike."
            sender = 'projectile.webgeeks@gmail.com'
            recipient = response_data["email"]

            email_sent = deliver_email(subject, message, sender, recipient, private_key_path)
            if email_sent == None:
                return Response("Failed to send email to user!", status=status.HTTP_400_BAD_REQUEST)

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class AccountLoginView(TokenObtainPairView):
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer
    
    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        response = super().post(request, *args, **kwargs)
        
        if response.status_code == status.HTTP_200_OK:

            response.set_cookie('refresh_token', response.data['refresh_token'], httponly=True)
            response.set_cookie('access_token', response.data['access_token'], httponly=True)
            
            # update last login
            user = get_user(request.data["username"])
            user.last_login = timezone.now()
            user.save()
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        return response


class AccountLogoutView(APIView):
    permission_classes = [IsAuthenticated, IsBlacklistedToken]
    
    def post(self, request):
        refresh_token = request.COOKIES.get('refresh_token')
        access_token = request.COOKIES.get('access_token')
        
        try:
            rtoken = RefreshToken(refresh_token)
            rtoken.blacklist()
        except ValueError:
            return Response({"message": "Invalid refresh token"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            atoken = AccessToken(access_token)
            
            if BlacklistedToken.objects.filter(token=atoken).exists():
                return Response({"message": "Access token already blacklisted"}, status=status.HTTP_200_OK)
            
            BlacklistedToken.objects.create(user=request.user, token=atoken)
        except ValueError:
            return Response({"message": "Invalid access token"}, status=status.HTTP_400_BAD_REQUEST)
        
        response = Response({"message": "Logout successful"}, status=status.HTTP_204_NO_CONTENT)
        response.delete_cookie('refresh_token')
        response.delete_cookie('access_token')
        return response