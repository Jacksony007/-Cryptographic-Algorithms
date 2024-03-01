const form = document.getElementById('registrationForm');
var message_container = document.getElementById('message-container');
var message = document.getElementById('message');
var register_button = document.getElementById("register-button");
var username = document.getElementById("username");


if (form) {
    form.addEventListener('submit', async (event) => {
        event.preventDefault();
    
        // Disable the register button and show loading state
        register_button.disabled = true;
        register_button.style.width = '50%';
        register_button.style.backgroundColor = 'rgb(60, 142, 135)';
        register_button.style.color = 'white';
        register_button.textContent = 'Registering...';
    
        const formData = new FormData(form);
        // store username of potential user
        localStorage.setItem('register_username', username.value);
    
    
        try {
            const response = await fetch('http://127.0.0.1:8000/api/account/register/', {
                method: 'POST',
                body: formData
            });
    
            if (response.status === 201) {
                // Resource created successfully
                const responseData = await response.json();
    
                // Redirect to register_success page with username as query parameter
                window.location.href = `../../Account/register_success.html?username=${responseData.username}`;
    
            } else if (!response.ok) {
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
            // Re-enable the register button and reset text
            register_button.disabled = false;
            register_button.textContent = 'Register';
            register_button.style.backgroundColor = 'white';
            register_button.style.color = 'rgb(60, 142, 135)';
        }
    });
}