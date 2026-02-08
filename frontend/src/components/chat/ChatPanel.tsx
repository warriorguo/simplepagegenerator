import { useRef, useEffect } from 'react'
import ChatMessage from './ChatMessage'
import ChatInput from './ChatInput'
import StreamingText from './StreamingText'
import ToolCallLog from './ToolCallLog'
import { useChat } from '../../hooks/useChat'
import { useSSE } from '../../hooks/useSSE'
import { useStore } from '../../store'
import '../../styles/chat.css'

interface Props {
  projectId: string
}

export default function ChatPanel({ projectId }: Props) {
  const messages = useChat(projectId)
  const { send, cancel } = useSSE(projectId)
  const streaming = useStore((s) => s.streaming)
  const isSending = useStore((s) => s.isSending)
  const addMessage = useStore((s) => s.addMessage)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, streaming.tokens])

  const handleSend = async (text: string) => {
    addMessage({
      id: Date.now(),
      thread_id: 0,
      role: 'user',
      content: text,
      created_at: new Date().toISOString(),
    })
    await send(text)
  }

  return (
    <div className="chat-panel">
      <div className="chat-messages">
        {messages.map((msg) => (
          <ChatMessage key={msg.id} message={msg} />
        ))}

        {streaming.tokens && (
          <div className="chat-message assistant">
            <div className="chat-message-header">
              <span className="chat-role">assistant</span>
              {streaming.stage && (
                <span className="chat-stage">[{streaming.stage}]</span>
              )}
            </div>
            <StreamingText text={streaming.tokens} />
            {streaming.toolCalls.length > 0 && (
              <ToolCallLog calls={streaming.toolCalls} />
            )}
            {streaming.buildStatus && (
              <div className={`build-status ${streaming.buildStatus.success ? 'success' : 'failed'}`}>
                {streaming.buildStatus.success
                  ? 'Build successful'
                  : `Build failed: ${streaming.buildStatus.errors.join(', ')}`}
              </div>
            )}
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      <ChatInput onSend={handleSend} disabled={isSending} onCancel={cancel} isSending={isSending} />
    </div>
  )
}
