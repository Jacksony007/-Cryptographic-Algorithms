import { customFetch, handleUnauthenticatedRequest } from "./token_middleware.js";

const shareImageForm = document.getElementById('share-image-form');
const shareImageResponse = document.getElementById('share-image-responses');
const imageOptions = document.getElementsByName("image-option");
const imagePreview = document.getElementById("image-preview");
const shareImageButton = document.getElementById("share-image");


imageOptions.forEach(function(option) {
    option.addEventListener("change", function() {
        const selectedValue = option.value;

        const imageSources = {
            apple: "../assets/images/Apple.jpg",
            bear: "../assets/images/Bear.jpg",
            boy: "../assets/images/Boy.jpg",
            girl: "../assets/images/Girl.jpg",
            lena: "../assets/images/Lena.jpg",
            man: "../assets/images/Man.jpg",
            test: "../assets/images/test.jpg",
        };

        if (selectedValue in imageSources) {
            imagePreview.src = imageSources[selectedValue];
        }
    });
});


shareImageButton.addEventListener('click', async (event) => {
    event.preventDefault();

    // fetch the image specified in imagePreview.src
    fetch(imagePreview.src)
        .then(response => response.blob())
        .then(async blob => {
            // create a File object from the blob
            const fileName = imagePreview.src.split('/').pop();
            const file = new File([blob], fileName, { type: 'image/png' });

            // create a FormData object for the form
            const formData = new FormData(shareImageForm);

            // add the file to the FormData with the key "image"
            formData.append('image', file);

            // update the form's data
            shareImageForm.formData = formData;

            // submit the form
            try {
                const response = await customFetch('http://127.0.0.1:8000/api/messaging/send_image/', {
                    method: 'POST',
                    body: formData
                });
        
                if (response.status === 201) {
                    const responseData = await response.json();
        
                    window.location.href = '../../Frontend/Account/dashboard.html?image_id=' + responseData.id;
                } else if (response.status === 401) {
                    // redirect user to login page
                    handleUnauthenticatedRequest();
                } else {
                    const errorText = await response.text();
                    shareImageResponse.textContent = errorText;
                    shareImageResponse.style.color = 'red';
                }
        
            } catch (error) {
                shareImageResponse.textContent = error.message;
                shareImageResponse.style.color = 'red';
            }
        })
        .catch(error => {
            console.error('Error uploading image:', error);
        });
});