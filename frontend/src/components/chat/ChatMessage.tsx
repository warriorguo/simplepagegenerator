import type { ChatMessage as ChatMessageType } from '../../types/chat'

interface Props {
  message: ChatMessageType
}

export default function ChatMessage({ message }: Props) {
  return (
    <div className={`chat-message ${message.role}`}>
      <div className="chat-message-header">
        <span className="chat-role">{message.role}</span>
        <span className="chat-time">
          {new Date(message.created_at).toLocaleTimeString()}
        </span>
      </div>
      <div className="chat-message-content">{message.content}</div>
    </div>
  )
}
