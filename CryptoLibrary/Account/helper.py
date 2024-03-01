import rsa, base64, magic, os
from cryptography.exceptions import UnsupportedAlgorithm
from rest_framework import serializers
from django.core.mail import EmailMultiAlternatives, BadHeaderError
from django.conf import settings
from .models import Account
from django.core.mail import EmailMultiAlternatives, BadHeaderError



EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
PASSWORD_REGEX = r'^(?=(.*[A-Z]){1,})(?=(.*[a-z]){1,})(?=.*\d)(?=.*[!@#$%^&()\-_<>.+]{0,}).{8,}$'


def generate_rsa_keys(user):
    """generates RSA keys for a user
    
    Args:
        user (Account): the user to generate keys for
    
    Returns:
        None
    """
    
    # generating keys
    public_key, private_key = rsa.newkeys(2048)
    
    private_key_dir = "media/keys/private_keys/"
    public_key_dir = "media/keys/public_keys/"

    # create directories if they don't exist
    os.makedirs(private_key_dir, exist_ok=True)
    os.makedirs(public_key_dir, exist_ok=True)

    try:
        # storing the private key
        with open(os.path.join(private_key_dir, f"{user}_private_key.pem"), "wb") as file:
            file.write(private_key.save_pkcs1("PEM"))

        # storing the public key
        with open(os.path.join(public_key_dir, f"{user}_public_key.pem"), "wb") as file:
            file.write(public_key.save_pkcs1("PEM"))

    except UnsupportedAlgorithm as e:
        # Handle the case where the algorithm is not supported for key serialization.
        raise serializers.ValidationError("Error: Unsupported Algorithm -", e)

    except IOError as e:
        # Handle Input/Output errors when writing to the files.
        raise serializers.ValidationError("Error: I/O Error -", e)

    except Exception as e:
        # Catch any other unexpected exceptions.
        raise serializers.ValidationError("Error:", e)


def load_public_key(value, method):
    """loads the public key pair from the keys folder
    
    Args:
        value (Account / filepath): the user to load public key for or
        the filepath to the private key uploaded by user
        method (string): determines whether value is an Account or filepath

    
    Returns:
        str: the public key
    """ 
    
    # load the public key
    try:
        if method == "account":
            with open(f"media/keys/public_keys/{value}_public_key.pem", "rb") as file:
                public_key = rsa.PublicKey.load_pkcs1(file.read())
        elif method == "file":
            with value.open(mode='rb') as file:
                public_key_data = file.read()
                if public_key_data:
                    public_key = rsa.PublicKey.load_pkcs1(public_key_data)
                else:
                    raise ValueError("Public key file is empty.")
        else:
            raise ValueError("Invalid method")

    except FileNotFoundError as e:
        # Handle the case where the public key file is not found.
        raise serializers.ValidationError("Error: Public key file not found -", e)

    except ValueError as e:
        # Handle ValueErrors that may occur during loading the public key.
        raise serializers.ValidationError("Error: Invalid public key data -", e)

    except Exception as e:
        # Catch any other unexpected exceptions.
        raise serializers.ValidationError("Error:", e)
        
    return public_key


def get_public_key_as_string(username):
    public_key = load_public_key(username, "account")
    return public_key.save_pkcs1().decode('utf-8')


def load_private_key(value, method):
    """loads the private key pair from the keys folder

    Args:
        value (Account / filepath): the user to load private key for or
        the filepath to the private key uploaded by user
        method (string): determines whether value is an Account or filepath
    
    Returns:
        str: the private key
    """
        
    # load the private key
    try:
        if method == "account":
            with open(f"media/keys/private_keys/{value}_private_key.pem", "rb") as file:
                private_key = rsa.PrivateKey.load_pkcs1(file.read())
                
        elif method == "file":
            with value.open(mode='rb') as file:
                private_key_data = file.read()
                file.close()
                if private_key_data:
                    private_key = rsa.PrivateKey.load_pkcs1(private_key_data)
                else:
                    raise ValueError("Private key file is empty.")
        else:
            raise ValueError("Invalid method")
            
    except FileNotFoundError as e:
        # Handle the case where the private key file is not found.
        raise serializers.ValidationError("Error: Private key file not found -", e)

    except ValueError as e:
        # Handle ValueErrors that may occur during loading the private key.
        raise serializers.ValidationError("Error: Invalid private key data -", e)

    except Exception as e:
        # Catch any other unexpected exceptions.
        raise serializers.ValidationError("Error:", e)
    
    return private_key


def get_private_key_as_string(username):
    private_key = load_private_key(username, "account")
    return private_key.save_pkcs1().decode('utf-8')


def encrypt_message(message, public_key):
    """encrypts a message using the public key
    
    Args:
        message (str): the message to encrypt
        public_key (pem): the public key to use for encryption
    
    Returns:
        str: the encrypted message
    """
    
    if isinstance(message, str):
        return rsa.encrypt(message.encode("ascii"), public_key)
    return rsa.encrypt(message, public_key)


def decrypt_message(ciphertext, private_key):
    """decrypts a message using the private key
    
    Args:
        ciphertext (str): the ciphertext to decrypt
        private_key (pem): the private key to use for decryption
    
    Returns:
        str or False: The decrypted message as a string if successful, False otherwise.
    """
    
    try:
        # Convert ciphertext to bytes if it's a string
        if isinstance(ciphertext, str):
            encrypted_data = base64.b64decode(ciphertext)
        else:
            encrypted_data = ciphertext

        # Decrypt the data and decode it using ASCII
        
        decrypted_data = rsa.decrypt(encrypted_data, private_key.encode('utf-8'))
        
        return decrypted_data
    except rsa.pkcs1.DecryptionError:
        raise serializers.ValidationError("Error: Decryption failed. Invalid ciphertext.")


def get_user(username):
    try:
        user = Account.objects.filter(username=username).first()
    except Account.DoesNotExist:
        return None
    
    return user


def deliver_email(subject, message, sender, recipient, attachment_path=None):

    try:
        email_object = EmailMultiAlternatives(subject, '', sender, [recipient])
        email_object.attach_alternative(message, 'text/html')

        if attachment_path:
            with open(attachment_path, 'rb') as file:
                file_content = file.read()
            
            mime_type = magic.from_buffer(file_content, mime=True)
            file_name = os.path.basename(attachment_path)
            email_object.attach(file_name, file_content, mime_type)

        email_object.send()
    except BadHeaderError:
        return None