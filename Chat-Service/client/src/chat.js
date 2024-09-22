import React, { useEffect, useState, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { io } from 'socket.io-client';
import { Message } from "./Message";
import { refreshToken } from './tokenUtils';

export const Chat = () => {
    const { chatRoomId } = useParams();
    const navigate = useNavigate();
    const [messages, setMessages] = useState([]);
    const [message, setMessage] = useState('');
    const [isConnected, setIsConnected] = useState(false);
    const [file, setFile] = useState(null);
    const [userInfo, setUserInfo] = useState(null);
    const [isGroupChat, setIsGroupChat] = useState(true);
    const [chatRoomName, setChatRoomName] = useState('');
    const [onlineUsers, setOnlineUsers] = useState([]);
    const messagesEndRef = useRef(null);
    const chatContainerRef = useRef(null);
    const fileInputRef = useRef(null);
    const socketRef = useRef(null);

    useEffect(() => {
        const fetchUserInfo = async () => {
            try {
                const newToken = await refreshToken();
                if (!newToken) {
                    navigate('/login');
                    return;
                }

                const response = await fetch(`${process.env.REACT_APP_API_URL}/users/me`, {
                    headers: {
                        'Authorization': `Bearer ${newToken}`
                    }
                });
                if (response.ok) {
                    const data = await response.json();
                    setUserInfo(data);

                    if (chatRoomId) {
                        const chatRoomResponse = await fetch(`${process.env.REACT_APP_API_URL}/chat-room/${chatRoomId}`, {
                            headers: {
                                'Authorization': `Bearer ${localStorage.getItem('token')}`
                            }
                        });
                        if (chatRoomResponse.ok) {
                            const chatRoomData = await chatRoomResponse.json();
                            setIsGroupChat(chatRoomData.is_group);
                            setChatRoomName(chatRoomData.name);
                        }

                        socketRef.current = io(process.env.REACT_APP_API_URL, {
                            auth: { token: localStorage.getItem('token'), chat_room_id: chatRoomId }
                        });

                        socketRef.current.on('connect', () => {
                            setIsConnected(true);
                            console.log('Connected to socket');
                        });

                        socketRef.current.on('disconnect', () => {
                            setIsConnected(false);
                            console.log('Disconnected from socket');
                        });

                        socketRef.current.on('join', (data) => {
                            setMessages((prevMessages) => [...prevMessages, {...data, type: 'join'}]);
                            setOnlineUsers((prevUsers) => [...prevUsers, data.username]);
                        });

                        socketRef.current.on('leave', (data) => {
                            setOnlineUsers((prevUsers) => prevUsers.filter(user => user !== data.username));
                        });

                        socketRef.current.on('chat', (data) => {
                            setMessages((prevMessages) => [...prevMessages, {...data.message, type: 'chat'}]);
                        });

                        socketRef.current.on('initial_messages', (initialMessages) => {
                            setMessages(initialMessages.map(msg => ({...msg, type: 'chat'})));
                        });

                        socketRef.current.on('more_messages', (olderMessages) => {
                            setMessages((prevMessages) => [...olderMessages.map(msg => ({...msg, type: 'chat'})), ...prevMessages]);
                        });

                        socketRef.current.on('online_users', (users) => {
                            setOnlineUsers(users);
                        });
                    } else {
                        console.error('Chat Room ID is undefined');
                        navigate('/chat-rooms');
                    }

                } else {
                    navigate('/login');
                }
            } catch (error) {
                console.error('Error fetching user info:', error);
                navigate('/login');
            }
        };

        fetchUserInfo();

        const refreshInterval = setInterval(async () => {
            const newToken = await refreshToken();
            if (!newToken) {
                navigate('/login');
            }
        }, 5 * 60 * 1000); // Refresh every 5 minutes

        return () => {
            if (socketRef.current) {
                socketRef.current.disconnect();
            }
            clearInterval(refreshInterval);
        };
    }, [chatRoomId, navigate]);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    const handleScroll = () => {
        if (chatContainerRef.current.scrollTop === 0 && messages.length > 0) {
            socketRef.current.emit('get_more_messages', { oldest_message_id: messages[0].id, chat_room_id: chatRoomId });
        }
    };

    const sendMessage = async () => {
        if (message.trim() || file) {
            const messageData = {
                content: message,
                message_type: file ? (file.type.startsWith('image/') ? 'image' : 'file') : 'text',
                user_email: userInfo.email,
                username: userInfo.username,
                chat_room_id: chatRoomId,
            };

            if (file) {
                messageData.file_name = file.name;
                messageData.file = await file.arrayBuffer();
            }

            socketRef.current.emit('chat', messageData);
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

    const handleExit = () => {
        if (socketRef.current) {
            socketRef.current.disconnect();
        }
        navigate('/chat-rooms');
    };

    return (
        <>
            <div style={{ display: 'flex' }}>
                <div style={{ flex: 3 }}>
                    <h1>{chatRoomName}</h1>
                    <h2>status: {isConnected ? 'connected': 'disconnected'}</h2>
                    <button onClick={handleExit}>Exit Chat Room</button>
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
                            <Message 
                                message={message} 
                                key={message.id || index} 
                                isGroupChat={isGroupChat} 
                                currentUserId={userInfo._id} 
                            />
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
                </div>
                <div style={{ flex: 1, marginLeft: '20px', borderLeft: '1px solid #ccc', paddingLeft: '20px' }}>
                    <h3>Online Users</h3>
                    <ul>
                        {onlineUsers.map((user, index) => (
                            <li key={index}>{user}</li>
                        ))}
                    </ul>
                </div>
            </div>
        </>
    );
};
