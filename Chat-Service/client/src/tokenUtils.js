import { jwtDecode } from 'jwt-decode';

export const refreshToken = async () => {
    const token = localStorage.getItem('token');
    if (!token) return null;

    const decodedToken = jwtDecode(token);
    const currentTime = Date.now() / 1000;

    if (decodedToken.exp < currentTime) {
        try {
            const response = await fetch(`${process.env.REACT_APP_API_URL}/refresh-token`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                localStorage.setItem('token', data.access_token);
                return data.access_token;
            } else {
                localStorage.removeItem('token');
                return null;
            }
        } catch (error) {
            console.error('Error refreshing token:', error);
            localStorage.removeItem('token');
            return null;
        }
    }

    return token;
};
