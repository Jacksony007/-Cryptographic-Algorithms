var share_message_form = document.getElementById("share-message-form"),
    share_message_modal_container = document.getElementById("share-message-modal-container"),
    share_message_button = document.getElementById("share-message"),

    share_message_receiver = document.getElementById("share-message-username"),
    share_message_message = document.getElementById("share-message-message"),
    share_message_private_key = document.getElementById("share-message-private-key"),

    share_image_form = document.getElementById("share-image-form"),
    share_image_modal_container = document.getElementById("share-image-modal-container"),
    share_image_button = document.getElementById("share-image"),

    share_image_receiver = document.getElementById("share-image-username"),
    share_image_image = document.getElementById("share-image-image"),
    share_image_message = document.getElementById("share-image-message"),
    share_image_private_key = document.getElementById("share-image-private-key")
;

function displayShareMessageModalContainer() {
    share_message_modal_container.style.display = 'block';
}

function displayShareImageModalContainer() {
    share_image_modal_container.style.display = 'block';
}

function closeShareMessageModalContainer() {
    share_message_modal_container.style.display = 'none';
}

function closeShareImageModalContainer() {
    share_image_modal_container.style.display = 'none';
}

function submitShareMessageForm(event) {
    event.preventDefault();

    if (receiver.value && message.value && private_key.value) {
        share_message_form.submit();
    }
}

function submitShareImageForm(event) {
    event.preventDefault();

    if (receiver.value && image.value && message.value && private_key.value) {
        share_image_form.submit();
    }
}

window.onclick = function (event) {
    if (event.target == share_message_modal_container) {
        closeShareMessageModalContainer();
    } else if (event.target == share_image_modal_container) {
        closeShareImageModalContainer();
    }
}

if (share_message_form) {
    share_message_form.addEventListener("submit", function (event) {
        submitShareMessageForm(event);
    });
}

if (share_image_form) {
    share_image_form.addEventListener("submit", function (event) {
        submitShareImageForm(event);
    });
}