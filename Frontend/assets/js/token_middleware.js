import AuthenticationError from "./errors.js";


// Function to get the refresh token from cookies
function getRefreshToken() {
    const cookies = document.cookie.split('; ');
    console.log(cookies)
    for (const cookie of cookies) {
        const [name, value] = cookie.split('=');
        if (name === 'refresh_token') {
            console.log(value);
            return value;
        }
    }
    return null;
}


// Function to update the access token in cookies
function updateAccessToken(newAccessToken) {
    document.cookie = `access_token=${newAccessToken}; path=/`; // Update the 'access_token' cookie
}


// Function to handle refresh token errors
function handleRefreshTokenError() {
    // Redirect to the login page
    window.location.href = '../../Frontend/Account/login.html';
}


// Function to get the access token from cookies
function getAccessToken() {
    const cookies = document.cookie.split('; ');
    for (const cookie of cookies) {
        const [name, value] = cookie.split('=');
        if (name === 'access_token') {
            return value;
        }
    }
    return null;
}


// Function to handle unauthenticated requests
function handleUnauthenticatedRequest() {
    // Redirect to the login page
    window.location.href = '../../Frontend/Account/login.html';
}


// Function to refresh the access token using the refresh token
const refreshAccessToken = async () => {
    const refreshToken = getRefreshToken();
    if (!refreshToken) {
        handleRefreshTokenError();
        return null;
    }

    try {
        const response = await fetch('http://127.0.0.1:8000/api/account/token/generate_access/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ refresh: refreshToken }),
        });

        if (response.ok) {
            const data = await response.json();
            const newAccessToken = data.access_token;
            updateAccessToken(newAccessToken);
            return newAccessToken;
        } else {
            handleRefreshTokenError();
            return null;
        }
    } catch (error) {
        handleRefreshTokenError();
        return null;
    }
};


const customFetch = async (url, options) => {
    const accessToken = getAccessToken();

    if (!accessToken) {
        handleUnauthenticatedRequest();
        return null;
    }

    try {
        return await fetch(url, {
            ...options,
            headers: {
                ...options.headers,
                Authorization: `Bearer ${accessToken}`,
            },
        });
    } catch (error) {
        if (error instanceof AuthenticationError) {
            const newAccessToken = await refreshAccessToken();

            if (newAccessToken) {
                options.headers.Authorization = `Bearer ${newAccessToken}`;
                return await fetch(url, options);
            }
        }
        throw error;
    }
};

export { customFetch, handleUnauthenticatedRequest };