import React, { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { refreshToken } from './tokenUtils';

export const ChatRooms = ({ onLogout }) => {
    const [groupChats, setGroupChats] = useState([]);
    const [privateChats, setPrivateChats] = useState([]);
    const [error, setError] = useState('');
    const navigate = useNavigate();

    const fetchChatRooms = useCallback(async () => {
        try {
            const newToken = await refreshToken();
            if (!newToken) {
                onLogout();
                navigate('/login');
                return;
            }

            const fetchRooms = async (isGroup) => {
                const response = await fetch(`${process.env.REACT_APP_API_URL}/user/submitted-chat-rooms`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${newToken}`
                    },
                    body: JSON.stringify({ is_group: isGroup })
                });

                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                return await response.json();
            };

            const [groupData, privateData] = await Promise.all([
                fetchRooms(true),
                fetchRooms(false)
            ]);

            setGroupChats(groupData);
            setPrivateChats(privateData);
        } catch (err) {
            console.error('Error fetching chat rooms:', err);
            setError('Failed to fetch chat rooms. Please try again.');
        }
    }, [navigate, onLogout]);

    useEffect(() => {
        fetchChatRooms();

        const refreshInterval = setInterval(async () => {
            const newToken = await refreshToken();
            if (!newToken) {
                onLogout();
                navigate('/login');
            }
        }, 5 * 60 * 1000); // Refresh every 5 minutes

        return () => clearInterval(refreshInterval);
    }, [fetchChatRooms, navigate, onLogout]);

    const handleChatRoomClick = async (chatRoomId) => {
        const newToken = await refreshToken();
        if (newToken) {
            navigate(`/chat/${chatRoomId}`);
        } else {
            onLogout();
            navigate('/login');
        }
    };

    const handleLogout = () => {
        onLogout();
        navigate('/login');
    };

    const renderChatList = (chats, title) => (
        <div>
            <h3>{title}</h3>
            {chats.length > 0 ? (
                <ul>
                    {chats.map((room) => (
                        <li key={room._id}>
                            <h4>{room.name}</h4>
                            <p>Created at: {new Date(room.created_at).toLocaleString()}</p>
                            <p>Last activity: {room.last_activity ? new Date(room.last_activity).toLocaleString() : 'N/A'}</p>
                            <p>Owner: {room.owner ? room.owner.username : 'N/A'}</p>
                            <button onClick={() => handleChatRoomClick(room._id)}>Join Chat</button>
                        </li>
                    ))}
                </ul>
            ) : (
                <p>No {title.toLowerCase()} available.</p>
            )}
        </div>
    );

    return (
        <div className="chat-rooms-container">
            <h2>Your Chat Rooms</h2>
            <button onClick={handleLogout}>Logout</button>
            {error && <p className="error">{error}</p>}
            {renderChatList(groupChats, "Group Chats")}
            {renderChatList(privateChats, "Private Chats")}
        </div>
    );
};
