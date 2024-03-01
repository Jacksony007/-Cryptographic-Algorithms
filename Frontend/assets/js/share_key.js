import { customFetch } from "./token_middleware.js";

const share_key_form = document.getElementById('share-key-form');
const share_key_button = document.getElementById('share-key-button');
var message_container = document.getElementById('message-container');
var message = document.getElementById('message');

function enableShareKeyButton() {
    share_key_button.disabled = false;
    share_key_button.textContent = 'Share';
    share_key_button.style.width = '30%';
    share_key_button.style.backgroundColor = 'white';
    share_key_button.style.color = 'rgb(60, 142, 135)';
    share_key_button.style.color = 'black';
}

function disableShareKeyButton() {
    share_key_button.disabled = true;
    share_key_button.style.width = '60%';
    share_key_button.style.backgroundColor = 'rgb(60, 142, 135)';
    share_key_button.style.color = 'white';
    share_key_button.textContent = 'Sharing key...';
}

share_key_form.addEventListener('submit', async (event) => {
    event.preventDefault();

    // disable the share key button and show loading state
    disableShareKeyButton();

    const formData = new FormData(share_key_form);

    if (formData.get('receiver') === localStorage.getItem('username')) {
        message_container.style.display = 'flex';
        message.textContent = 'You cannot share a key with yourself';
        message.style.color = 'red';
        enableShareKeyButton();
        return;
    }

    if (formData.get('receiver') === '') {
        message_container.style.display = 'flex';
        message.textContent = 'Please enter a receiver';
        message.style.color = 'red';
        enableShareKeyButton();
        return;
    }

    try {
        const response = await customFetch('http://127.0.0.1:8000/api/messaging/share_key/', {
            method: 'POST',
            body: formData
        });

        if (response.status === 201) {
            const responseData = await response.json();

            localStorage.setItem('key_share_success', true);
            message_container.style.display = 'flex';
            message.textContent = responseData.message;
            message.style.color = 'green';
            enableShareKeyButton();

        } else if (response.status === 401) {
            // redirect user to login page
            handleUnauthenticatedRequest();
        } else if (!response.ok) {
            const errorText = await response.text();
            message_container.style.display = 'flex';
            message.textContent = errorText;
            message.style.color = 'red';
            enableShareKeyButton();
        }
    } catch (error) {
        message_container.style.display = 'flex';
        message.textContent = error.message;
        message.style.color = 'red';
    }
});