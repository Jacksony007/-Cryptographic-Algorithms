import { customFetch, handleUnauthenticatedRequest } from "./token_middleware.js";

const logout_button = document.getElementById('logout');
var message_container = document.getElementById('message-container');
var message = document.getElementById('message');


async function logout() {
    try {
        // make logout request to API endpoint
        const response = await customFetch('http://127.0.0.1:8000/api/account/logout/', {
            method: 'POST',
            body: {}
        });

        if (response.status === 204) {
            // remove data stored on localStorage
            localStorage.removeItem('username');
            localStorage.removeItem('id');
            localStorage.removeItem('access_level');

            // redirect user to login page
            window.location.href = '../../Frontend/Account/login.html';
        } else if (response.status === 401) {
            // redirect user to login page
            handleUnauthenticatedRequest();
        }  else {
            const errorText = await response.text();
            message_container.style.display = 'flex';
            message.textContent = errorText;
            message.style.color = 'red';
        }
    } catch (error) {
        message_container.style.display = 'flex';
        message.textContent = error.message;
        message.style.color = 'red';
    } finally {
        // change logout button text
        logout_button.textContent = 'Logout';
    }
};

logout_button.addEventListener('click', () => {
    logout_button.textContent = "Signing out ..."

    // delay for 5 seconds before making logout request
    setTimeout(logout, 2000);
});