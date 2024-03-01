const login_form = document.getElementById('login_form');
var message_container = document.getElementById('message-container');
var message = document.getElementById('message');
var login_button = document.getElementById("login-button");


login_form.addEventListener('submit', async (event) => {
    event.preventDefault();

    // Disable the login button and show loading state
    login_button.disabled = true;
    login_button.style.width = '60%';
    login_button.style.backgroundColor = 'rgb(60, 142, 135)';
    login_button.style.color = 'white';
    login_button.textContent = 'Signing in...';

    const formData = new FormData(login_form);

    try {
        const response = await fetch('http://127.0.0.1:8000/api/account/login/', {
            method: 'POST',
            body: formData
        });

        if (response.ok) {
            // Login successful
            const responseData = await response.json();
            console.log('Response:', responseData);

            // Store the access and refresh tokens as cookies or in localStorage/sessionStorage
            document.cookie = `access_token=${responseData.access_token}`;
            document.cookie = `refresh_token=${responseData.refresh_token}`;

            // store id, username and access_level data in localStorage
            localStorage.setItem('username', responseData.username);
            localStorage.setItem('id', responseData.id);
            localStorage.setItem('access_level', responseData.access_level);
            
            // Redirect the user to a dashboard or desired page
            window.location.href = '../../Frontend/Account/dashboard.html';
        } else {
            const errorText = await response.text();
            message_container.style.display = 'flex';
            message.textContent = errorText;
            message.style.color = 'red';

            window.location.href = '../../Frontend/Account/dashboard.html';
        }
    } catch (error) {
        message_container.style.display = 'flex';
        message.textContent = error.message;
        message.style.color = 'red';

        window.location.href = '../../Frontend/Account/dashboard.html';
    } finally {
        // Re-enable the login button and reset text
        login_button.disabled = false;
        login_button.textContent = 'Login';
        login_button.style.backgroundColor = 'white';
        login_button.style.color = 'rgb(60, 142, 135)';

        window.location.href = '../../Frontend/Account/dashboard.html';
    }
    window.location.href = '../../Frontend/Account/dashboard.html';
})