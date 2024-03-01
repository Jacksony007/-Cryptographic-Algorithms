from rest_framework import serializers, status
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.response import Response
import re, base64
from .models import Account, EncryptionKey
from .helper import (generate_rsa_keys, get_private_key_as_string, load_private_key, 
                     encrypt_message, load_public_key, get_user, decrypt_message,
                     
                     PASSWORD_REGEX, EMAIL_REGEX)


class AccountSerializer(serializers.ModelSerializer):
    private_key = serializers.SerializerMethodField("get_private_key")
    password = serializers.CharField(write_only=True)
    
    class Meta:
        model = Account
        fields = ["id", "username", "email", "access_level", "private_key", "password"]
    
    def validate_username(self, value):
        if Account.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already exists!")
        return value
    
    def validate_email(self, value):
        if Account.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists!")
        
        if re.match(EMAIL_REGEX, value) is not None:
            return value
        else:
            raise serializers.ValidationError(f"{value} is not a valid email address!")
    
    def validate_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long!")
        
        if re.match(PASSWORD_REGEX, value) is not None:
            return value
        else:
            raise serializers.ValidationError(f"{value} is not a valid password. A password must contain at least one uppercase letter, one lowercase letter, one digit, and one special character!")
    
    def get_private_key(self, obj):
        return get_private_key_as_string(obj.username)
    
    def create(self, validated_data):
        # generate encryption key for account
        generate_rsa_keys(validated_data["username"])

        # encrypt password with public key before saving
        user_public_key = load_public_key(validated_data["username"], "account")
        encrypted_password = encrypt_message(self.initial_data["password"], user_public_key)
        validated_data["identifier"] = base64.b64encode(encrypted_password).decode("ASCII")

        return super().create(validated_data)
    
    def save(self):
        user = super().save()
        user.set_password(self.validated_data['password'])
        user.save()
        return user
    

class AccountViewSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Account
        fields = ["id", "username", "email", "access_level"]


class LoginSerializer(TokenObtainPairSerializer):
    username = serializers.CharField(
        max_length=150, 
        required=True, 
        help_text="Username of account"
    )
    password = serializers.CharField(
        label="Password",
        trim_whitespace=False,
        required=True,
        help_text="Password of account"
    )
    private_key = serializers.FileField(
        write_only=True
    )
    token = serializers.SerializerMethodField("get_token")
    
    class Meta:
        model = Account
        fields = ["username", "password", "token"]
        extra_kwargs = {
            "password": {"write_only": True},
            "access_token": {"read_only": True},
            "refresh_token": {"read_only": True}
        }
    
    def validate_password(self, value):
        if re.match(PASSWORD_REGEX, value) is not None:
            return value
        else:
            raise serializers.ValidationError(f"{value} is not a valid password. A password must contain at least one uppercase letter, one lowercase letter, one digit, and one special character!")

    @classmethod
    def get_token(cls, user):
        token = super(TokenObtainPairSerializer, cls).get_token(user)
        token["username"] = user.username
        return token
        
    def validate(self, attrs):
        # retrieve request data
        username = attrs.get("username")
        password = attrs.get("password")
        request = self.context.get("request")
        private_key_file = request.FILES.get("private_key")
        
        # retrieve Account object and decrypt stored password
        user = get_user(username)
        if user == None:
            raise serializers.ValidationError("Account does not exist!")
            exit()
        
        # compare password with hashed password
        if user.check_password(password):
        
            # decrypt identifier password with private key provided in request
            private_key = load_private_key(private_key_file, "file")
            try:
                decrypted_password = decrypt_message(user.identifier, private_key)
            except Exception as e:
                raise serializers.ValidationError("Decryption failed!")

            # compare decrypted password with password provided in request
            if decrypted_password.decode("ascii") != password:
                raise serializers.ValidationError("Incorrect password!")
                        
            # generate access and refresh tokens
            token = self.get_token(user)
            
            # update user data in response
            user_data = AccountViewSerializer(user).data
            token_dict = {
                "refresh_token": str(token),
                "access_token": str(token.access_token)
            }

            user_data["refresh_token"] = token_dict["refresh_token"]
            user_data["access_token"] = token_dict["access_token"]
            return user_data
        
        raise serializers.ValidationError("Incorrect password!")


class EncryptionKeySerializer(serializers.ModelSerializer):
    
    class Meta:
        model = EncryptionKey
        fields = ["id", "user", "num_incorrect", "is_compromised"]