from django.db import models
from Account.models import Account


class SharedKey(models.Model):
    """defines the attributes a SharedKey object

    Args:
        - sender (Account): the user sharing the AES key
        - receiver (Account): the user receiving the AES key
        - sender_aes (AES): the encrypted AES key by the sender's public RSA Key
        - receiver_aes (AES): the encrypted AES key by the receiver's public RSA Key
        - time_shared (datetime): the time the AES key was shared
        - is_active (bool): whether the AES key is active
    """
    
    sender = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="sender")
    receiver = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="receiver")
    sender_aes = models.CharField(max_length=1000, blank=True)
    receiver_aes = models.CharField(max_length=1000, blank=True)
    time_shared = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    

class Steganography(models.Model):
    """
    defines the attributes of a Steganography object
    
    Args:
        - sender (Account): the user sending the message
        - receiver (Account): the user receiving the message
        - shared_key (SharedKey): the shared key used to encrypt the message
        - image_path (str): the path to the Steganographic image
        - time_sent (datetime): the time the message was sent
    """
    
    sender = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="steganography_sender", blank=True)
    receiver = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="steganography_receiver")
    shared_key = models.ForeignKey(SharedKey, on_delete=models.CASCADE, related_name="steganography_encryption_key")
    image_path = models.CharField(max_length=255, blank=True)
    message_size = models.IntegerField(default=0)                   # in bytes
    compressed_message_size = models.IntegerField(default=0)        # in bytes
    compression_time = models.FloatField(default=0)                 # in seconds
    time_sent = models.DateTimeField(auto_now_add=True)