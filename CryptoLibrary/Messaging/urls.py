from django.urls import path
from .views import (
    ShareAESKeyView, DisableSharedKeyView, 
    SendImageView, RetrieveImagesView, RetrieveImageView, RetrieveEncryptedMessageLSBView, 
    PerformAnalysisView, DecryptImageView,
)

urlpatterns = [
    path("share_key/", ShareAESKeyView.as_view(), name="share-aes-key"),
    path("disable_key/<int:key_id>/", DisableSharedKeyView.as_view(), name="disable-shared-key"),
    
    path("send_image/", SendImageView.as_view(), name="send-image"),
    path("retrieve_images/", RetrieveImagesView.as_view(), name="retrieve-images"),
    path("retrieve_image/<int:pk>/", RetrieveImageView.as_view(), name="retrieve-image"),
    path("retrieve_message_lsb/<int:image_id>/", RetrieveEncryptedMessageLSBView.as_view(), name="retrieve-message-lsb"),
    path("perform_analysis/<int:image_id>/", PerformAnalysisView.as_view(), name="perform-analysis"),
    path("decrypt_image/<int:image_id>/", DecryptImageView.as_view(), name="decrypt-image"),
]