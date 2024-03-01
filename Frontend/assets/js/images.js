import { customFetch, handleUnauthenticatedRequest } from "./token_middleware.js";

const imageContainer = document.getElementById('image-objects-container');
var message_container = document.getElementById('message-container');
var message = document.getElementById('message');

// fetch user images
try {
    // make retrieve images request
    const response = await customFetch('http://127.0.0.1:8000/api/messaging/retrieve_images/', {
        method: 'GET',
    });

    if (response.status === 200) {
        const responseData = await response.json();

        if (responseData.length > 0) {
            // loop through the array of images and create elements for each image
            responseData.forEach(image => {
                // create elements for each image
                const imageObject = document.createElement('div');
                imageObject.classList.add('image-object');

                const imageImage = document.createElement('div');
                imageImage.classList.add('image-container');
                const imageItem = document.createElement('img');
                imageItem.src = "../../../CryptoLibrary/media/images/" + image.image_path;
                console.log("IMAGE PATH:" + imageItem.src)
                imageImage.appendChild(imageItem);

                const imageMeta = document.createElement('div');
                imageMeta.classList.add('image-meta');

                const imageSender = document.createElement('div');
                imageSender.classList.add('sender-info');

                const senderProfileImage = document.createElement('div');
                senderProfileImage.classList.add('sender-profile-image');
                const profileImage = document.createElement('img');
                profileImage.src = '../assets/images/Pastor Edwin.jpg';

                const senderUsername = document.createElement('div');
                senderUsername.classList.add('sender-username');
                senderUsername.textContent = image.sender;

                senderProfileImage.appendChild(profileImage);
                imageSender.appendChild(senderProfileImage);
                imageSender.appendChild(senderUsername);

                const imageDate = document.createElement('div');
                imageDate.classList.add('image-date');
                const date = new Date(image.time_sent);
                const options = { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' };
                imageDate.textContent = date.toLocaleDateString('en-US', options);

                imageMeta.appendChild(imageSender);
                imageMeta.appendChild(imageDate);

                imageObject.appendChild(imageImage);
                imageObject.appendChild(imageMeta);

                imageObject.setAttribute('image-id', image.id);

                imageContainer.appendChild(imageObject);
            });
        }
    } else if (response.status === 404) {
        imageContainer.textContent = 'No images have been shared with you!';
    } else if (response.status === 401) {
        // redirect user to login page
        handleUnauthenticatedRequest();
    }  else {
        const errorText = await response.text();
        imageContainer.style.display = 'flex';
        imageContainer.textContent = errorText;
        imageContainer.style.color = 'red';
    }
} catch (error) {
    message_container.style.display = 'flex';
    message.textContent = error.message;
    message.style.color = 'red';
}


// IMAGE OBJECTS
var image_objects = document.querySelectorAll('.image-object');
var image_object_modal = document.getElementById('image-object-modal-container');
var image_object_responses = document.getElementById('image-object-responses');
var decrypt_image_form = document.getElementById('decrypt-image-form');
var private_key_data = document.getElementById('private-key-data');
var compressed_message_huffman = document.getElementById('compressed-message-huffman');
var compressed_message_huffman_data = document.getElementById('compressed-message-huffman-data');
var encrypted_message = document.getElementById('encrypted-message-lsb');
var encrypted_message_data = document.getElementById('encrypted-message-lsb-data');
var message_cipher = document.getElementById('message-cipher');
var message_cipher_label = document.getElementById('message-cipher-label');
var message_cipher_data = document.getElementById('message-cipher-data');
var decrypt_button = document.getElementById('decrypt');
var analyse_button = document.getElementById('analyse');
var cancel_button = document.getElementById('cancel');


function openImageObjectModalContainer() {
    image_object_modal.style.display = 'block';
}


function closeImageObjectModalContainer() {
    image_object_modal.style.display = 'none';
    document.getElementById('image-analysis').style.display = 'none';
    message_cipher_data.style.color = 'black';
    decrypt_button.style.display = 'block';
    decrypt_button.textContent = 'Reveal';
}


image_objects.forEach(image_object => {
    image_object.addEventListener('click', async (event) => {
        // clear image modal form of previous responses
        decrypt_image_form.reset();

        // clear previous decrypted images
        message_cipher.style.display = 'none';

        // set the decrypt button type to button
        decrypt_button.type = 'button';

        var image_id = image_object.getAttribute('image-id');

        // make retrieve image request
        try {
            const response = await customFetch('http://127.0.0.1:8000/api/messaging/retrieve_image/' + image_id + '/', {
                method: 'GET',
            });

            if (response.status === 200) {
                const responseData = await response.json();

                openImageObjectModalContainer();

                // set image data
                document.getElementById('sender-data').textContent = responseData.sender;
                document.getElementById('receiver-data').textContent = responseData.receiver;
                document.getElementById('stego-image-image').src = "../../../CryptoLibrary/media/images/" + responseData.image_path;
                decrypt_button.setAttribute('image-id', responseData.id);

                const dateTime = new Date(responseData.time_sent);
                const options = { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' };
                document.getElementById('time-sent-data').textContent = dateTime.toLocaleDateString('en-US', options);

                if (decrypt_button.disabled) {
                    decrypt_button.disabled = false;
                }
            } else if (response.status === 401) {
                // redirect user to login page
                handleUnauthenticatedRequest();
            } else {
                const errorText = await response.text();
                image_object_responses.textContent = errorText;
                image_object_responses.style.color = 'red';
            }
        } catch (error) {
            image_object_responses.textContent = error.message;
            image_object_responses.style.color = 'red';
        }
    });
});


// checking if the url contains an image id and triggering a click event
const urlParams = new URLSearchParams(window.location.search);
const imageIDParam = urlParams.get('image_id');

if (imageIDParam !== null && !isNaN(imageIDParam)) {
    const imageObject = document.querySelector(`[image-id="${imageIDParam}"]`);
    
    if (imageObject) {
        // Trigger a click event on the message object
        const clickEvent = new Event('click', {
            bubbles: true,
            cancelable: true,
        });
        imageObject.dispatchEvent(clickEvent);
    }
}


decrypt_button.addEventListener('click', async (event) => {

    if (decrypt_button.type === 'button' && decrypt_button.textContent.replace(/\s/g, '') === 'Decrypt') {
        // display decrypt image form
        private_key_data.style.display = 'block';
        decrypt_button.type = 'submit';
    } else if (decrypt_button.type === 'button' && decrypt_button.textContent.replace(/\s/g, '') === 'Reveal') {
        // make request to reveal encrypted message behind image object
        // and set the button's inner HTML to Decrypt if successful

        var image_id = decrypt_button.getAttribute('image-id');

        try {
            const response = await customFetch('http://127.0.0.1:8000/api/messaging/retrieve_message_lsb/' + image_id + '/', {
                method: 'GET',
            });

            if (response.status === 200) {
                const responseData = await response.json();

                // replace data in compressed message tag
                compressed_message_huffman.style.display = 'block';
                compressed_message_huffman_data.textContent = responseData.compressed_message;

                // replace data in encrypted message tag
                encrypted_message.style.display = 'block';
                encrypted_message_data.textContent = responseData.encrypted_message;

                // change button text to decrypt
                decrypt_button.textContent = 'Decrypt';

            } else if (response.status === 401) {
                // redirect user to login page
                handleUnauthenticatedRequest();
            } else {
                const errorText = await response.text();
                image_object_responses.textContent = errorText;
                image_object_responses.style.color = 'red';
            }
        } catch (error) {
            image_object_responses.textContent = error.message;
            image_object_responses.style.color = 'red';
        }
    }
});


cancel_button.addEventListener('click', async (event) => {
    closeImageObjectModalContainer();
});


window.addEventListener('click', async (event) => {
    if (event.target === image_object_modal) {
        closeImageObjectModalContainer();
    }
});


function getCSRFToken() {
    const csrfCookie = document.cookie.split(';').find(cookie => cookie.trim().startsWith('csrftoken='));
    if (csrfCookie) {
        return csrfCookie.split('=')[1];
    }
    return null;
}



decrypt_image_form.addEventListener('submit', async (event) => {
    event.preventDefault();

    // disable the decrypt button
    decrypt_button.disabled = true;

    // remove previous responses
    image_object_responses.textContent = '';

    const formData = new FormData(decrypt_image_form);
    var image_id = decrypt_button.getAttribute('image-id');

    try {
        const response = await customFetch('http://127.0.0.1:8000/api/messaging/decrypt_image/' + image_id + '/', {
            method: 'POST',
            body: formData
        });

        if (response.ok) {
            const responseData = await response.json();

            private_key_data.style.display = 'none'
            encrypted_message.style.display = 'none';
            message_cipher.style.display = 'block';
            message_cipher_label.textContent = 'Decrypted Message:';
            message_cipher_data.textContent = responseData.message;
            message_cipher_data.style.color = 'green';
            decrypt_button.style.display = 'none';

        } else if (response.status == 401) {
            // redirect user to login page
            handleUnauthenticatedRequest();
        } else {
            const errorText = await response.text();
            image_object_responses.textContent = errorText;
            image_object_responses.style.color = 'red';
            decrypt_button.disabled = false;
        }
    } catch (error) {
        image_object_responses.textContent = error.message;
        image_object_responses.style.color = 'red';
        decrypt_button.disabled = false;
    }
});


analyse_button.addEventListener('click', async (event) => {
    // make request to perform analysis on image
    var image_id = decrypt_button.getAttribute('image-id');

    try {
        const response = await customFetch('http://127.0.0.1:8000/api/messaging/perform_analysis/' + image_id + '/', {
            method: 'GET',
        });
        
        if (response.ok) {
            const responseData = await response.json();

            // get analysis attributes and replace data in tags
            document.getElementById('ssim-r-data').textContent = responseData.ssim_r;
            document.getElementById('ssim-g-data').textContent = responseData.ssim_g;
            document.getElementById('ssim-b-data').textContent = responseData.ssim_b;
            document.getElementById('ssim-avg-data').textContent = responseData.ssim_avg;
            document.getElementById('cr-data').textContent = responseData.cr;
            document.getElementById('ct-data').textContent = responseData.ct;
            document.getElementById('cs-data').textContent = responseData.cs;
            document.getElementById('sp-data').textContent = responseData.sp;
            document.getElementById('bpp-data').textContent = responseData.bpp;
            document.getElementById('mse-data').textContent = responseData.mse;
            document.getElementById('psnr-data').textContent = responseData.psnr;
            document.getElementById('graph-image').src = "../../../CryptoLibrary/media/plots/" + responseData.graph_path;

            // display analysis div
            document.getElementById('image-analysis').style.display = 'block';

        } else if (response.status == 401) {
            // redirect user to login page
            handleUnauthenticatedRequest();
        } else {
            const errorText = await response.text();
            image_object_responses.textContent = errorText;
            image_object_responses.style.color = 'red';
        }

    } catch (error) {
        image_object_responses.textContent = error.message;
        image_object_responses.style.color = 'red';
    }
});