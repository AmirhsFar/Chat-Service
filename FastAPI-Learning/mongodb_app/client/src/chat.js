import React, { useEffect, useState, useRef } from 'react';
import { io } from 'socket.io-client';
import { Message } from "./Message";

const socket = io(process.env.REACT_APP_API_URL);

export const Chat = () => {
    const [messages, setMessages] = useState([]);
    const [message, setMessage] = useState('');
    const [isConnected, setIsConnected] = useState(socket.connected);
    const messagesEndRef = useRef(null);
    const chatContainerRef = useRef(null);

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

    const sendMessage = () => {
        if(message && message.length) {
            socket.emit('chat', message);
        }
        setMessage('');
    };

    return (
        <>
            <h2>status: {isConnected ? 'connected': 'disconnected'}</h2>
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
                onKeyPress={(event) => {
                    if (event.key === 'Enter') {
                        sendMessage();
                    }
                }}
            />
            <button onClick={sendMessage}>Send</button>
        </>
    );
};
