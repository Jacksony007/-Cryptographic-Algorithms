import { customFetch, handleUnauthenticatedRequest } from "./token_middleware.js";

var messageContainer = document.getElementById('message-objects-container');
var message_container = document.getElementById('message-container');
var message = document.getElementById('message');

// fetch user messages
try {
    // make retrieve messages request
    const response = await customFetch('http://127.0.0.1:8000/api/messaging/retrieve_messages/', {
        method: 'GET',
    });

    if (response.status === 200) {
        const responseData = await response.json();

        if (responseData.length > 0) {
            // loop through the array of messages and create elements for each message
            responseData.forEach(message => {
                // create elements for each message
                const messageObject = document.createElement('div');
                messageObject.classList.add('message-object');

                const messageImage = document.createElement('div');
                messageImage.classList.add('message-image');

                const senderProfileImage = document.createElement('div');
                senderProfileImage.classList.add('sender-profile-image');
                const profileImage = document.createElement('img');
                profileImage.src = '../assets/images/Pastor Edwin.jpg';

                senderProfileImage.appendChild(profileImage);
                messageImage.appendChild(senderProfileImage);

                const messageData = document.createElement('div');
                messageData.classList.add('message-data');

                const senderUsername = document.createElement('div');
                senderUsername.classList.add('sender-username');
                senderUsername.textContent = message.sender;

                const textDateFlex = document.createElement('div');
                textDateFlex.classList.add('text-date-flex');

                const messageCipher = document.createElement('div');
                messageCipher.classList.add('message-cipher');
                
                // check if the message is longer than 50 characters
                if (message.message.length > 50) {
                    // if it's longer, truncate it and add an ellipsis
                    messageCipher.textContent = message.message.slice(0, 40) + '...';
                } else {
                    // if it's not longer, use the original message text
                    messageCipher.textContent = message.message;
                }

                const messageDate = document.createElement('div');
                messageDate.classList.add('message-date');
                const dateTime = new Date(message.time_sent);
                const options = { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' };
                messageDate.textContent  = dateTime.toLocaleString('en-US', options);

                textDateFlex.appendChild(messageCipher);
                textDateFlex.appendChild(messageDate);

                messageData.appendChild(senderUsername);
                messageData.appendChild(textDateFlex);

                messageObject.appendChild(messageImage);
                messageObject.appendChild(messageData);

                messageObject.setAttribute('message-id', message.id);

                messageContainer.appendChild(messageObject);
            });
        }
    } else if (response.status === 404) {
        messageContainer.textContent = 'No messages have been shared with you!';
    } else if (response.status === 401) {
        // redirect user to login page
        handleUnauthenticatedRequest();
    } else {
        const errorText = await response.text();
        messageContainer.style.display = 'flex';
        messageContainer.textContent = errorText;
        messageContainer.style.color = 'red';
    }
} catch (error) {
    message_container.style.display = 'flex';
    message.textContent = error.message;
    message.style.color = 'red';
}


// MESSAGE OBJECTS
var message_objects = document.querySelectorAll('.message-object');
var message_object_modal = document.getElementById('message-object-modal-container');
var message_object_responses = document.getElementById('message-object-responses');
var decrypt_message_form = document.getElementById('decrypt-message-form');
var private_key_data = document.getElementById('decrypt-private-key');
var message_cipher_label = document.getElementById('message-cipher-label');
var message_cipher_data = document.getElementById('message-cipher-data');
var decrypt_button = document.getElementById('decrypt');
var cancel_button = document.getElementById('cancel');


function openMessageObjectModalContainer() {
    message_object_modal.style.display = 'block';
}


function closeMessageObjectModalContainer() {
    message_object_modal.style.display = 'none';
    message_cipher_data.style.color = 'black'
    message_cipher_label.textContent = 'Message Cipher:';
}


message_objects.forEach(message_object => {
    message_object.addEventListener('click', async () => {
        // clear modal form of previous data
        decrypt_message_form.reset();

        // set decrypt button type to button
        decrypt_button.type = 'button';

        var message_id = message_object.getAttribute('message-id');

        // fetch message
        try {
            // make retrieve message request
            const response = await customFetch('http://127.0.0.1:8000/api/messaging/retrieve_message/' + message_id + '/', {
                method: 'GET'
            });

            if (response.status === 200) {
                const responseData = await response.json();

                openMessageObjectModalContainer();
                document.getElementById('sender-data').textContent = responseData.sender;
                document.getElementById('receiver-data').textContent = responseData.receiver;
                document.getElementById('message-cipher-data').textContent = responseData.message;
                decrypt_button.setAttribute('message-id', responseData.id);

                const dateTime = new Date(responseData.time_sent);
                const options = { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' };
                document.getElementById('time-sent-data').textContent = dateTime.toLocaleString('en-US', options);

                if (decrypt_button.disabled) {
                    decrypt_button.disabled = false;
                }
            } else if (response.status === 401) {
                // redirect user to login page
                handleUnauthenticatedRequest();
            } else {
                const errorText = await response.text();
                message_object_responses.textContent = errorText;
                message_object_responses.style.color = 'red';
            }
        } catch (error) {
            message_object_responses.textContent = error.message;
            message_object_responses.style.color = 'red';
        }
    });
});


// checking if the url contains a message id and triggering a click event
const urlParams = new URLSearchParams(window.location.search);
const messageIDParam = urlParams.get('message_id');

if (messageIDParam !== null && !isNaN(messageIDParam)) {
    const messageObject = document.querySelector(`[message-id="${messageIDParam}"]`);
    
    if (messageObject) {
        // Trigger a click event on the message object
        const clickEvent = new Event('click', {
            bubbles: true,
            cancelable: true,
        });
        messageObject.dispatchEvent(clickEvent);
    }
}


decrypt_button.addEventListener('click', async (event) => {    
    if (decrypt_button.type === 'submit') {
        // Prevent the default form submission action
        event.preventDefault();

        // Trigger the form's submit event
        const submitEvent = new Event('submit', {
            bubbles: true,
            cancelable: true,
        });

        decrypt_message_form.dispatchEvent(submitEvent);
    } else {
        // display private key form
        decrypt_message_form.style.display = 'block';
        decrypt_button.type = 'submit';
    }
});


cancel_button.addEventListener('click', () => {
    closeMessageObjectModalContainer();
});


window.onclick = function(event) {
    if (event.target == message_object_modal) {
        closeMessageObjectModalContainer();
    }
}


decrypt_message_form.addEventListener('submit', async (event) => {
    event.preventDefault();

    // disable the decrypt button
    decrypt_button.disabled = true;

    // remove previous responses
    message_object_responses.textContent = '';

    const formData = new FormData(decrypt_message_form);
    formData.append('private_key', private_key_data.files[0]);
    var message_id = decrypt_button.getAttribute('message-id');
 
    try {
        // make retrieve message request
        const response = await customFetch('http://127.0.0.1:8000/api/messaging/decrypt_message/' + message_id + '/', {
            method: 'POST',
            body: formData
        });

        if (response.ok) {
            const responseData = await response.json();

            decrypt_message_form.style.display = 'none'
            message_cipher_label.textContent = 'Decrypted Message:';
            message_cipher_data.textContent = responseData.message;
            message_cipher_data.style.color = 'green';
        } else if (response.status == 401) {
            // redirect user to login page
            handleUnauthenticatedRequest();
        } else {
            const errorText = await response.text();
            message_object_responses.textContent = errorText;
            message_object_responses.style.color = 'red';
            decrypt_button.disabled = false;
        }
    } catch (error) {
        message_object_responses.textContent = error.message;
        message_object_responses.style.color = 'red';
        decrypt_button.disabled = false;
    }
});