export const Message = ({message}) => {
    if (message.type === 'join') return <p>{`${message.sid} just joined`}</p>;
    if (message.type === 'chat') {
        const date = new Date(message.timestamp);
        const formattedDate = date.toLocaleString();
        return <p>{`${message.user_id} (${formattedDate}): ${message.content}`}</p>;
    }
};