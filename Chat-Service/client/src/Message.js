import React from 'react';
import { useNavigate } from 'react-router-dom';

export const Message = ({ message, isGroupChat, currentUserId }) => {
    const navigate = useNavigate();

    const handleUsernameClick = async () => {
        if (isGroupChat && message.type === 'chat' && message.user_id !== currentUserId) {
            try {
                const response = await fetch(`${process.env.REACT_APP_API_URL}/pv-chat-room`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${localStorage.getItem('token')}`
                    },
                    body: JSON.stringify({ addressed_users_id: message.user_id })
                });

                if (response.ok) {
                    const data = await response.json();
                    navigate(`/chat/${data.chat_room.id}`);
                } else {
                    console.error('Failed to create private chat room');
                }
            } catch (error) {
                console.error('Error creating private chat room:', error);
            }
        }
    };

    if (message.type === 'join') return <p>{`${message.username || message.sid} just joined`}</p>;
    if (message.type === 'chat') {
        const date = new Date(message.timestamp);
        const formattedDate = date.toLocaleString();

        let content;
        switch (message.message_type) {
            case 'image':
                content = <img 
                    src={`${process.env.REACT_APP_API_URL}/uploads/${message.file_name}`} 
                    alt="Uploaded content" 
                    style={{maxWidth: '200px', maxHeight: '200px'}} 
                />;
                break;
            case 'file':
                content = <a 
                    href={`${process.env.REACT_APP_API_URL}/uploads/${message.file_name}`} 
                    target="_blank" 
                    rel="noopener noreferrer"
                >{message.file_name}</a>;
                break;
            default:
                content = message.content;
        }

        return (
            <div>
                <p>
                    <span 
                        onClick={handleUsernameClick} 
                        style={{ 
                            cursor: (isGroupChat && message.user_id !== currentUserId) ? 'pointer' : 'default', 
                            color: (isGroupChat && message.user_id !== currentUserId) ? 'blue' : 'inherit' 
                        }}
                    >
                        {message.username}
                    </span>
                    {` (${formattedDate}):`}
                </p>
                {content}
            </div>
        );
    }
};
