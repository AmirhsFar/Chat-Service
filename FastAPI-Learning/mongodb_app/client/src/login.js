import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

export const Login = ({ onLogin }) => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    try {
        const response = await fetch(`${process.env.REACT_APP_API_URL}/token`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
            'username': email,
            'password': password,
        }),
        });

        if (response.ok) {
        const data = await response.json();
        localStorage.setItem('token', data.access_token);
        onLogin();
        navigate('/chat');
        } else {
        setError('Invalid email or password');
        }
    } catch (err) {
        setError('An error occurred. Please try again.');
    }
    };

    return (
    <div className="login-container">
        <h2>Login</h2>
        <form onSubmit={handleSubmit}>
        <div>
            <label htmlFor="email">Email:</label>
            <input
            type="email"
            id="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            />
        </div>
        <div>
            <label htmlFor="password">Password:</label>
            <input
            type="password"
            id="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            />
        </div>
        {error && <p className="error">{error}</p>}
        <button type="submit">Login</button>
        </form>
    </div>
    );
};
