import base64
import os
import pickle
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.conf import settings

from .models import SharedKey, Steganography
from .serializers import SharedKeySerializer, LSBSteganographySerializer
from .helper import decrypt_text
from .analysis import determine_psnr, determine_pvd, determine_ssim_values, determine_bpp
from Huffman.histogram_shift import Image_Decoder
from Huffman.huffman import decodeHuffman
from Account.helper import get_user, load_private_key, decrypt_message, deliver_email
from Account.permissions import IsBlacklistedToken


class ShareAESKeyView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated, IsBlacklistedToken]
    serializer_class = SharedKeySerializer

    def post(self, request, *args, **kwargs):
        # ensure receiver doesn't already have an active key
        other_party = get_user(request.data["receiver"])
        if (SharedKey.objects.filter(sender=request.user, receiver=other_party, is_active=True).exists() or
                SharedKey.objects.filter(sender=other_party, receiver=request.user, is_active=True).exists()):
            return Response({"error": f"you already have an active key with {other_party}"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.serializer_class(
            data=request.data, context={"request": request})

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DisableSharedKeyView(APIView):
    permission_classes = [IsAuthenticated, IsBlacklistedToken]

    def patch(self, request, key_id, *args, **kwargs):
        # ensure key exists
        if not SharedKey.objects.filter(id=key_id).exists():
            return Response({"error": "key does not exist"}, status=status.HTTP_400_BAD_REQUEST)

        # ensure key belongs to user
        key = SharedKey.objects.get(id=key_id)
        if key.sender != request.user or request.user.is_superuser:
            return Response({"error": "You do not have permission to the requested resource"}, status=status.HTTP_400_BAD_REQUEST)

        # disable key
        key.is_active = False
        key.save()

        return Response({"message": "key disabled"}, status=status.HTTP_200_OK)


class SendImageView(APIView):
    permission_classes = [IsAuthenticated, IsBlacklistedToken]

    def post(self, request, *args, **kwargs):
        # ensure an active key exists between sender and desired receiver
        receiver = get_user(request.data["receiver"])
        if receiver == None:
            return Response({"error": "User does not exist!"}, status=status.HTTP_400_BAD_REQUEST)

        if not (SharedKey.objects.filter(sender=request.user, receiver=receiver.id, is_active=True).exists()
                or SharedKey.objects.filter(sender=receiver.id, receiver=request.user, is_active=True).exists()):
            return Response({"error": "no active key exists between sender and receiver"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = LSBSteganographySerializer(
            data=request.data, context={"request": request})
        if serializer.is_valid():
            # response_data = serializer.data
            # subject = f'CryptographyLibra Message From {request.user.username}'
            # message = f"Dear {response_data['receiver'].capitalize()}, you have received a message from {receiver.username} on CryptographyLibra. "
            # message += f"Please click <a href='http://127.0.0.1:5500/Frontend/Account/dashboard.html?image_id={response_data['id']}'>here</a> to access it."
            # sender = 'projectile.webgeeks@gmail.com'
            # recipient = receiver.email

            # email_sent = deliver_email(subject, message, sender, recipient)
            # if email_sent == None:
            #     return Response("Failed to send email to user!", status=status.HTTP_400_BAD_REQUEST)

            return Response({"success": "image has been sent"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RetrieveImagesView(APIView):
    permission_classes = [IsAuthenticated, IsBlacklistedToken]

    def get(self, request, *args, **kwargs):
        # retrieve all images sent and received by user
        try:
            sent_images = Steganography.objects.filter(
                sender=request.user, shared_key__is_active=True)
        except Steganography.DoesNotExist:
            sent_images = Steganography.objects.none()

        try:
            received_images = Steganography.objects.filter(
                receiver=request.user, shared_key__is_active=True)
        except Steganography.DoesNotExist:
            sent_images = Steganography.objects.none()

        images = sent_images.union(received_images)
        all_images = list()

        # retrieve username of sender
        for image in images:
            image_dict = LSBSteganographySerializer(image).data
            image_dict["sender"] = image.sender.username
            all_images.append(image_dict)

        # order images by date sent, new to old
        all_images.sort(key=lambda x: x["time_sent"], reverse=True)

        if images.count() == 0:
            return Response({"error": "no images found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(all_images, status=status.HTTP_200_OK)


class RetrieveImageView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated, IsBlacklistedToken]
    queryset = Steganography.objects.filter(shared_key__is_active=True)
    serializer_class = LSBSteganographySerializer
    lookup_field = "pk"

    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        sender = get_user(instance.sender)
        serializer = self.get_serializer(instance).data
        serializer["sender"] = sender.username
        return Response(serializer, status=status.HTTP_200_OK)


class RetrieveEncryptedMessageLSBView(APIView):
    permission_classes = [IsAuthenticated, IsBlacklistedToken]

    def get(self, request, image_id, *args, **kwargs):
        # ensure the image exists
        if not Steganography.objects.filter(id=image_id).exists():
            return Response({"error": "image does not exist"}, status=status.HTTP_400_BAD_REQUEST)

        # retrieve the image object
        image = Steganography.objects.get(id=image_id)

        # ensure the image belongs to the user
        if image.sender == request.user or image.receiver == request.user:
            pass
        else:
            return Response({"error": "You do not have permission to the requested resource"}, status=status.HTTP_400_BAD_REQUEST)

        # ensure the key used to encrypt the image is active
        if not image.shared_key.is_active:
            return Response({"error": "key used to encrypt image is no longer active"}, status=status.HTTP_400_BAD_REQUEST)

        # retrieve encoded message hidden in image
        image_path = os.path.join(
            settings.MEDIA_ROOT, "images", image.image_path)
        image_enc_data_pkl = os.path.join(
            settings.MEDIA_ROOT, "lsb", f"{image.image_path.split('.')[0]}_enc_data.pkl")

        compressed_data = Image_Decoder(image_path, image_enc_data_pkl)

        freq_file = os.path.join(settings.MEDIA_ROOT, "data_freq",
                                 f"{image.image_path.split('modified')[0]}data_freq.pkl")
        with open(freq_file, 'rb') as f:
            data_freq = pickle.load(f)

        encrypted_message = decodeHuffman(compressed_data, data_freq)
        return Response(
            {"compressed_message": compressed_data,
                "encrypted_message": encrypted_message},
            status=status.HTTP_200_OK
        )


class PerformAnalysisView(APIView):
    permission_classes = [IsAuthenticated, IsBlacklistedToken]

    def get(self, request, image_id, *args, **kwargs):
        # ensure image exists
        if not Steganography.objects.filter(id=image_id).exists():
            return Response({"error": "image does not exist"}, status=status.HTTP_400_BAD_REQUEST)

        # retrieve image object
        image = Steganography.objects.get(id=image_id)

        # ensure image belongs to user
        if image.sender == request.user or image.receiver == request.user:
            pass
        else:
            return Response({"error": "You do not have permission to the requested resource"}, status=status.HTTP_400_BAD_REQUEST)

        # get encoded image path
        encoded_image_path = os.path.join(
            settings.MEDIA_ROOT, "images", image.image_path)

        # get original image path
        original_image_path = os.path.join(
            settings.MEDIA_ROOT, "image_choices", f"{image.image_path.split('_')[2]}.{image.image_path.split('.')[-1]}")
        
        # perform analysis
        psnr = determine_psnr(original_image_path, encoded_image_path)
        
        mse, graph_path = determine_pvd(original_image_path, encoded_image_path)
        
        ssim_r, ssim_g, ssim_b, ssim_avg = determine_ssim_values(original_image_path, encoded_image_path)
        
        cr = image.message_size / image.compressed_message_size                 # compression ratio
        cs = image.message_size / image.compression_time                        # compression speed
        sp = (image.message_size / image.compressed_message_size) * 100   # saving percentage
    
        bpp = determine_bpp(encoded_image_path)            # bits per pixel
        
        return Response({
                "psnr": f"{round(psnr, 3)} dB",       
                "mse": round(mse, 3),
                "cr": round(cr, 3),
                "ct": round(image.compression_time, 3),
                "cs": round(cs, 2),
                "sp": f"{round(sp, 2)}%",
                "bpp": round(bpp, 2),
                "graph_path": graph_path.split("\\")[-1],
                "ssim_r": round(ssim_r, 3),
                "ssim_g": round(ssim_g, 3),
                "ssim_b": round(ssim_b, 3),
                "ssim_avg": round(ssim_avg, 3)},
            status=status.HTTP_200_OK
        )


class DecryptImageView(APIView):
    permission_classes = [IsAuthenticated, IsBlacklistedToken]

    def post(self, request, image_id, *args, **kwargs):
        # ensure user has uploaded their private key
        if not request.FILES.get("private_key"):
            return Response({"error": "private key not found"}, status=status.HTTP_400_BAD_REQUEST)

        # ensure the image exists
        if not Steganography.objects.filter(id=image_id).exists():
            return Response({"error": "image does not exist"}, status=status.HTTP_400_BAD_REQUEST)

        # retrieve the image object
        image = Steganography.objects.get(id=image_id)

        # ensure the image belongs to the user
        if image.sender == request.user or image.receiver == request.user:
            pass
        else:
            return Response({"error": "You do not have permission to the requested resource"}, status=status.HTTP_400_BAD_REQUEST)

        # ensure the key used to encrypt the image is active
        if not image.shared_key.is_active:
            return Response({"error": "key used to encrypt image is no longer active"}, status=status.HTTP_400_BAD_REQUEST)

        # retrieve encoded message hidden in image
        image_path = os.path.join(
            settings.MEDIA_ROOT, "images", image.image_path)
        image_enc_data_pkl = os.path.join(
            settings.MEDIA_ROOT, "lsb", f"{image.image_path.split('.')[0]}_enc_data.pkl")

        compressed_data = Image_Decoder(image_path, image_enc_data_pkl)

        freq_file = os.path.join(settings.MEDIA_ROOT, "data_freq",
                                 f"{image.image_path.split('modified')[0]}data_freq.pkl")
        with open(freq_file, 'rb') as f:
            data_freq = pickle.load(f)

        encrypted_message = decodeHuffman(compressed_data, data_freq)

        # load sender's / receiver's private key
        try:
            private_key = load_private_key(
                request.FILES.get("private_key"), "file")
        except ValueError:
            return Response({"error": "invalid private key"}, status=status.HTTP_400_BAD_REQUEST)
        except FileNotFoundError:
            return Response({"error": "private key file not found"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # decrypt sender's / receiver's shared key
        if image.shared_key.sender == request.user:
            encrypted_message_key = base64.b64decode(
                image.shared_key.sender_aes)
        elif image.shared_key.receiver == request.user:
            encrypted_message_key = base64.b64decode(
                image.shared_key.receiver_aes)
        else:
            return Response({"error": "You do not have permission to the requested resource"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            message_key = decrypt_message(encrypted_message_key, private_key)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # decrypt message
        decrypted_message = decrypt_text(
            encrypted_message.encode('utf-8'), message_key)
        
        if decrypted_message == -1:
            return Response({"error": "decryption failed"}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"message": decrypted_message}, status=status.HTTP_200_OK)
