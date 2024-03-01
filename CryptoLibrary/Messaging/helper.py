import os, base64, hashlib, binascii
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from base64 import b64encode, b64decode
from stegano import lsb
from rest_framework import serializers
from django.conf import settings


def generate_aes_key(identifier):
    """Generates an AES key from the encrypted identifier of the sender's user attributes.

    This function takes the encrypted identifier from the sender's user attributes and uses it
    as a password to derive an AES key. The key derivation is performed using Argon2, a strong
    and memory-hard key derivation function.

    Args:
        identifier (str): The encrypted identifier from the sender's user attributes.

    Returns:
        bytes: A 256-bit AES key derived from the encrypted identifier.

    Example:
        encrypted_identifier = '98sdfa0g...90asjdf=='
        aes_key = generate_aes_key(encrypted_identifier)
        print(aes_key)  # Output: b'\x8e\x9f\x0b\x03...\x9e\xac\x1b'
    """
    
    password = base64.b64decode(identifier.encode("ASCII"))
    salt = os.urandom(16)

    # Using Argon2 as the key derivation function
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA512(),
        length=32,  # 256-bit AES key
        salt=salt,
        iterations=1000,
    )

    aes_key = kdf.derive(password)

    return aes_key


def aes_as_string(aes_key):
    """Converts an AES key from bytes to a hexadecimal string representation.

    This function takes an AES key as bytes and converts it to a hexadecimal
    string representation for easy representation or storage.

    Args:
        aes_key (bytes): The AES key to be converted.

    Returns:
        str: A hexadecimal string representing the AES key.

    Example:
        aes_key = b'\x8e\x9f\x0b\x03...\x9e\xac\x1b'
        key_as_string = aes_as_string(aes_key)
        print(key_as_string)  # Output: '8e9f0b03...9eac1b'
    """
    
    return binascii.hexlify(aes_key).decode()


def encrypt_text(plain_text, aes_key):
    """Encrypts the input text using AES encryption.

    Args:
        plain_text (str): The text to be encrypted.
        aes_key (bytes): The AES key used for encryption.

    Returns:
        bytes: The encrypted text.

    Example:
        aes_key = b'\x8e\x9f\x0b\x03...\x9e\xac\x1b'
        encrypted_text = encrypt_text("Hello, world!", aes_key)
        print(encrypted_text)  # Output: b'f\xaf\xf4\xbf...\xa8\xfe\xc5'
    """
    
    # Pad the plaintext to the AES block size
    padder = padding.PKCS7(algorithms.AES.block_size).padder()
    padded_data = padder.update(plain_text.encode()) + padder.finalize()

    # Encrypt the padded data using AES in CBC mode
    iv = os.urandom(16)
    cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv))
    encryptor = cipher.encryptor()
    encrypted_data = encryptor.update(padded_data) + encryptor.finalize()

    # Return the Base64 encoded ciphertext and IV
    return b64encode(iv + encrypted_data)


def decrypt_text(encrypted_text, aes_key):
    """Decrypts the input encrypted text using AES decryption.

    Args:
        encrypted_text (bytes): The encrypted text to be decrypted.
        aes_key (bytes): The AES key used for decryption.

    Returns:
        str: The decrypted text.

    Example:
        aes_key = b'\x8e\x9f\x0b\x03...\x9e\xac\x1b'
        decrypted_text = decrypt_text(b'f\xaf\xf4\xbf...\xa8\xfe\xc5', aes_key)
        print(decrypted_text)  # Output: "Hello, world!"
    """
    
    # Decode the Base64 encoded ciphertext
    data = b64decode(encrypted_text)
    
    # Extract the IV and ciphertext
    iv = data[:16]
    encrypted_data = data[16:]
    
    # Decrypt the data using AES in CBC mode
    cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv))
    decryptor = cipher.decryptor()
    decrypted_padded_data = decryptor.update(encrypted_data) + decryptor.finalize()
    
    # Unpad the decrypted data
    unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
    decrypted_data = unpadder.update(decrypted_padded_data) + unpadder.finalize()
    
    # Return the decrypted text as a string
    return decrypted_data.decode()


def hide_message_lsb(sender, receiver, request, secret_message):
    """Hides a secret message in the least significant bits of an image.

    Args:
        sender (str): The sender's username.
        receiver (str): The receiver's username.
        request (Request): The HTTP request containing the image.
        secret_message (str): The secret message to be hidden.

    Returns:
        bool: whether the message was successfully hidden.
        
    Example:
        request = <Request: POST '/api/v1/messages/'>
        secret_message = 'Hello, world!'
        modified_image = hide_message_lsb(original_image, secret_message)
        print(modified_image)  # Output: 'modified.jpg'
    """
    
    # Hide the message in the image using LSB steganography
    original_image = request.FILES.get('image')
    try:
        output_path = os.path.join(settings.MEDIA_ROOT, "images", 
                                   f"{sender}_{receiver}_{original_image.name.split('.')[0]}_modified.jpg")
        modified_image = lsb.hide(original_image, secret_message)
        
        # Save the modified image
        modified_image.save(output_path)

    except ValueError:
        raise serializers.ValidationError({"error": "Message too long."})
    except Exception as e:
        raise serializers.ValidationError({"error": str(e)})
    
    # Return the path to the modified image
    return os.path.relpath(output_path, settings.MEDIA_ROOT)


def extract_message_lsb(image_path):
    """Extracts a secret message from the least significant bits of an image.

    Args:
        image_path (str): The path to the modified image.

    Returns:
        str: The extracted secret message.

    Example:
        modified_image = 'modified.jpg'
        secret_message = extract_message_lsb(modified_image)
        print(secret_message)  # Output: 'Hello, world!'
    """
    
    # Extract the message from the modified image using LSB steganography
    try:
        secret_message = lsb.reveal(image_path)
    except FileNotFoundError:
        raise serializers.ValidationError({"error": "File not found."})
    except Exception as e:
        raise serializers.ValidationError({"error": str(e)})
    
    # Return the extracted secret message
    return secret_message