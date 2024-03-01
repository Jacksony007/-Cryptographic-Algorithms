import base64, cv2, os, timeit, re
from rest_framework import serializers
from django.conf import settings
from .models import SharedKey, Steganography
from .helper import generate_aes_key, encrypt_text, hide_message_lsb
from .analysis import plot_histograms
from Huffman.histogram_shift import Image_Encoder
from Account.helper import get_user, load_public_key, load_private_key, encrypt_message, decrypt_message
from Huffman.huffman import encodeHuffman


class SharedKeySerializer(serializers.ModelSerializer):
    receiver = serializers.CharField()
    sender = serializers.SerializerMethodField("get_sender")
    aes_key = serializers.SerializerMethodField("get_aes_key")
    sender_aes = serializers.CharField(required=False, write_only=True)
    receiver_aes = serializers.CharField(required=False, write_only=True)
    is_active = serializers.ReadOnlyField()
    time_shared = serializers.ReadOnlyField()
    
    class Meta:
        model = SharedKey
        fields = ["id", "sender", "receiver", "time_shared", "is_active", 
                  "aes_key", "sender_aes", "receiver_aes", "is_active", "time_shared"]
    
    def validate_receiver(self, value):
        try:
            receiver = get_user(value)
            if receiver == None:
                raise serializers.ValidationError("User does not exist!")
            else:
                return receiver
        except ValueError:
            raise serializers.ValidationError("User does not exist!")
        
    def get_sender(self, obj):
        return self.context["request"].user.username
    
    def get_aes_key(self, obj):
        try:
            receiver = self.validated_data.get("receiver")
        except ValueError:
            raise serializers.ValidationError("User does not exist!")
        
        # generate AES key
        aes_key = generate_aes_key(receiver.identifier)
        
        # encrypt the AES key with sender's public key
        sender_public_key = load_public_key(self.context["request"].user.username, "account")
        sender_aes = encrypt_message(aes_key, sender_public_key)
        
        # encrypt AES key with receiver's public key
        receiver_public_key = load_public_key(receiver.username, "account")
        receiver_aes = encrypt_message(aes_key, receiver_public_key)
        
        # Store the encrypted AES key in the database
        self.context["sender_aes"] = sender_aes
        self.context["receiver_aes"] = receiver_aes
        
        return "*" * len(aes_key)
    
    def create(self, validated_data):
        receiver = validated_data.pop("receiver")
        aes_key = self.get_aes_key(validated_data)
        
        shared_key = SharedKey.objects.create(
            sender=self.context["request"].user,
            receiver=receiver,
            sender_aes=base64.b64encode(self.context["sender_aes"]).decode("ASCII"),
            receiver_aes=base64.b64encode(self.context["receiver_aes"]).decode("ASCII"),
            **validated_data,
        )
        
        return shared_key


class LSBSteganographySerializer(serializers.ModelSerializer):
    receiver = serializers.CharField()
    
    class Meta:
        model = Steganography
        fields = ["id", "sender", "receiver", "image_path", "message_size", 
                  "compressed_message_size", "compression_time", "time_sent"]
    
    def validate_sender(self, obj):
        try:
            sender = get_user(self.context["request"].user.username)
            return sender
        except ValueError:
            raise serializers.ValidationError("User does not exist!")
    
    def validate_receiver(self, value):
        try:
            receiver = get_user(value)
            return receiver
        except ValueError:
            raise serializers.ValidationError("User does not exist!")
    
    def validate_image_path(self, value):
        try:
            # attempt to read the image using OpenCV
            image = cv2.imread(value)
            if image is None:
                raise serializers.ValidationError("Invalid image file. Please provide a valid image.")
            
            # image is valid, return the original value
            return value
        except Exception as e:
            raise serializers.ValidationError(f"Error while validating image: {e}")
    
    def validate(self, attrs):
        receiver = get_user(attrs.get("receiver"))        
        sender_private_key_file = self.context.get("request").FILES.get("private_key")
        image_file = self.context.get("request").FILES.get("image")
        message = self.context.get("request").data.get("message")
        
        if message == "":
            raise serializers.ValidationError("Message cannot be empty!")
        
        # ensure an image with the same name does not exist
        image_path = os.path.join("images", 
                                  f"{self.context.get('request').user.username}_{receiver.username}_{image_file.name.split('.')[0]}_modified.jpg")
        if Steganography.objects.filter(image_path=image_path).exists():
            raise serializers.ValidationError("An image with the same name already exists!")
                
        # read sender's private key
        try:
            sender_private_key = load_private_key(sender_private_key_file, "file")
        except ValueError:
            raise serializers.ValidationError("Invalid private key!")
        except FileNotFoundError:
            raise serializers.ValidationError("Private key not found!")
        except Exception:
            raise serializers.ValidationError("Something went wrong!")
        
        # retrieve and decrypt sender_aes using sender's private key
        shared_key = SharedKey.objects.filter(sender=self.context["request"].user, receiver=receiver, is_active=True).first()

        if shared_key == None:
            is_receiver = True
            shared_key = SharedKey.objects.filter(sender=receiver, receiver=self.context["request"].user, is_active=True).first()
        else:
            is_receiver = False
        
        try:
            if not is_receiver:
                decrypted_aes = decrypt_message(shared_key.sender_aes, sender_private_key)
            else:
                decrypted_aes = decrypt_message(shared_key.receiver_aes, sender_private_key)
        except Exception as e:
            raise serializers.ValidationError("Decryption failed. Invalid private key!")
        
        # encrypt the message using the AES key
        encrypted_message = encrypt_text(message, decrypted_aes).decode('utf-8')
        
        # compress the message using huffman coding

        # Replace consecutive spaces with a single space
        text = re.sub('\s{2,}', ' ', encrypted_message)
		# Append lines with a space and remove newlines and new paragraphs
        text = re.sub('\n|\r\n|\r|\n\n+', ' ', text)
        filename = f"{self.context.get('request').user.username}_{receiver.username}_{image_file.name.split('.')[0]}.txt"
        encoded_message = encodeHuffman(text, filename)
        compression_time = timeit.timeit(lambda: encodeHuffman(text, filename), number=10)
        
        # call the new Encoder for the LSB
        original_image = self.context["request"].FILES.get('image')
        image_path = os.path.join(settings.MEDIA_ROOT, "image_choices", original_image.name)
        print(image_path)
        print(1)
        output_path = os.path.join(settings.MEDIA_ROOT, "images",
                                   f"{self.context.get('request').user.username}_{receiver.username}_{original_image.name.split('.')[0]}_modified.jpg")
        print(2)
        print(output_path)
        modified_image = Image_Encoder(image_path, encoded_message, output_path)
        print(3)
        
        if not modified_image:
            raise serializers.ValidationError("Something went wrong while hiding the message!")
        
        # create the Steganography object
        steganographic_image = Steganography.objects.create(
            sender=self.context["request"].user,
            receiver=receiver,
            shared_key=shared_key,
            image_path=modified_image.split("\\")[-1],
            message_size = str(len(message)),
            compressed_message_size = len(encoded_message.encode('utf-8')),
            compression_time = compression_time
        )
        
        encoded_image_path = os.path.join(
            settings.MEDIA_ROOT, "images", steganographic_image.image_path)

        # get original image path
        original_image_path = os.path.join(
            settings.MEDIA_ROOT, "image_choices", f"{steganographic_image.image_path.split('_')[2]}.{steganographic_image.image_path.split('.')[-1]}")

        # plot the histograms
        plot_histograms(original_image_path, encoded_image_path)

        return steganographic_image