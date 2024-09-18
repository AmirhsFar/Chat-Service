import React, { useEffect, useState, useRef } from 'react';
import { io } from 'socket.io-client';
import { Message } from "./Message";

const socket = io(process.env.REACT_APP_API_URL, {
    autoConnect: false
});

export const Chat = ({ onLogout }) => {
    const [messages, setMessages] = useState([]);
    const [message, setMessage] = useState('');
    const [isConnected, setIsConnected] = useState(socket.connected);
    const [file, setFile] = useState(null);
    const [userInfo, setUserInfo] = useState(null);
    const messagesEndRef = useRef(null);
    const chatContainerRef = useRef(null);
    const fileInputRef = useRef(null);

    useEffect(() => {
        const fetchUserInfo = async () => {
            try {
                const response = await fetch(`${process.env.REACT_APP_API_URL}/users/me`, {
                    headers: {
                        'Authorization': `Bearer ${localStorage.getItem('token')}`
                    }
                });
                if (response.ok) {
                    const data = await response.json();
                    setUserInfo(data);
                    socket.auth = { token: localStorage.getItem('token') };
                    socket.connect();
                } else {
                    onLogout();
                }
            } catch (error) {
                console.error('Error fetching user info:', error);
                onLogout();
            }
        };

        fetchUserInfo();

        return () => {
            socket.disconnect();
        };
    }, [onLogout]);

    useEffect(() => {
        socket.on('connect', () => {
            setIsConnected(socket.connected);
        });

        socket.on('disconnect', () => {
            setIsConnected(false);
        });

        socket.on('join', (data) => {
            setMessages((prevMessages) => [...prevMessages, {...data, type: 'join'}]);
        });

        socket.on('chat', (data) => {
            setMessages((prevMessages) => [...prevMessages, {...data.message, type: 'chat'}]);
        });

        socket.on('initial_messages', (initialMessages) => {
            setMessages(initialMessages.map(msg => ({...msg, type: 'chat'})));
        });

        socket.on('more_messages', (olderMessages) => {
            setMessages((prevMessages) => [...olderMessages.map(msg => ({...msg, type: 'chat'})), ...prevMessages]);
        });

        return () => {
            socket.off('connect');
            socket.off('disconnect');
            socket.off('join');
            socket.off('chat');
            socket.off('initial_messages');
            socket.off('more_messages');
        };
    }, []);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    const handleScroll = () => {
        if (chatContainerRef.current.scrollTop === 0 && messages.length > 0) {
            socket.emit('get_more_messages', { oldest_message_id: messages[0].id });
        }
    };

    const sendMessage = async () => {
        if (message.trim() || file) {
            const messageData = {
                content: message,
                message_type: file ? (file.type.startsWith('image/') ? 'image' : 'file') : 'text',
                user_email: userInfo.email,
                username: userInfo.username,
            };

            if (file) {
                messageData.file_name = file.name;
                messageData.file = await file.arrayBuffer();
            }

            socket.emit('chat', messageData);
            setMessage('');
            setFile(null);
            if (fileInputRef.current) {
                fileInputRef.current.value = '';
            }
        }
    };

    const handleFileChange = (event) => {
        setFile(event.target.files[0]);
    };

    return (
        <>
            <h2>status: {isConnected ? 'connected': 'disconnected'}</h2>
            <button onClick={onLogout}>Logout</button>
            <div 
                ref={chatContainerRef}
                onScroll={handleScroll}
                style={{
                    height: '500px',
                    overflowY: 'scroll',
                    border: 'solid black 1px',
                    padding: '10px',
                    marginTop: '15px',
                    display: 'flex',
                    flexDirection: 'column',
                }}
            >
                {messages.map((message, index) => (
                    <Message message={message} key={message.id || index} />
                ))}
                <div ref={messagesEndRef} />
            </div>
            <input
                type={'text'}
                value={message}
                onChange={(event) => setMessage(event.target.value)}
                onKeyDown={(event) => {
                    if (event.key === 'Enter') {
                        sendMessage();
                    }
                }}
            />
            <input
                type="file"
                onChange={handleFileChange}
                ref={fileInputRef}
            />
            <button onClick={sendMessage}>Send</button>
        </>
    );
};
