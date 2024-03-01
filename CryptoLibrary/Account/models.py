from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin


class CustomAccountManager(BaseUserManager):
    
    def create_user(self, username, email, password, **other_fields):
        """creates a user account

        Args:
            username (str): username of account
            email (str): email of account
            password (password): password of account

        Returns:
            user (Account): user account

        Raises:
            ValueError: if username or email is not provided
        """

        if not username:
            raise ValueError("Username is required!")

        if not email:
            raise ValueError("You must provide a valid email!")

        if not password:
            raise ValueError("You must provide a valid password!")

        other_fields.setdefault("is_active", True)
        other_fields.setdefault("access_level", 0)
        other_fields.setdefault("is_staff", False)
        other_fields.setdefault("is_superuser", False)

        email = self.normalize_email(email)
        user = self.model(
            username=username,
            email=email,
            **other_fields
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password, **other_fields):
        
        other_fields.setdefault("is_active", True)
        other_fields.setdefault("access_level", 28)
        other_fields.setdefault("is_staff", True)
        other_fields.setdefault("is_superuser", True)
        
        if other_fields.get("is_staff") is not True:
            raise ValueError("Superuser must be assigned to is_staff=True!")
        
        if other_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must be assigned to is_superuser=True!")
        
        return self.create_user(username, email, password, **other_fields)
        

class Account(AbstractBaseUser, PermissionsMixin):
    """defines attributes of an Account object

    Args:
        username (str): username of account
        email (str): email of account
        password (str): password of account
        access_level (int): access level of account
    """
    
    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField(max_length=254, unique=True)
    identifier = models.CharField(max_length=1000, blank=True)
    access_level = models.IntegerField(default=0, blank=True)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    
    objects = CustomAccountManager()
    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email", "password"]
    
    def __str__(self, *args, **kwargs):
        return self.username


class EncryptionKey(models.Model):
    """defines attributes of an EncryptionKey object

    Args:
        user (Account): account associated with encryption key
        num_incorrect (int): number of times the user has entered the wrong public key
        is_compromised (bool): whether or not the user's public key has been compromised
    """
    
    user = models.ForeignKey(Account, on_delete=models.CASCADE)
    num_incorrect = models.IntegerField(default=0, blank=True)
    is_compromised = models.BooleanField(default=False)
    
    def __str__(self, *args):
        return f"{self.user.username} : {self.num_incorrect}"
    

class BlacklistedToken(models.Model):
    """defines attributes of a BlacklistedToken object
    
    Args:
        user (Account): account associated with token
        token (str): token to be blacklisted
        blacklisted_at (datetime): time at which token was blacklisted
    """
    
    user = models.ForeignKey(Account, on_delete=models.CASCADE)
    token = models.TextField(unique=True)
    blacklisted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Blacklisted Tokens"