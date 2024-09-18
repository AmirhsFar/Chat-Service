export const Message = ({message}) => {
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
                <p>{`${message.username} (${formattedDate}):`}</p>
                {content}
            </div>
        );
    }
};
