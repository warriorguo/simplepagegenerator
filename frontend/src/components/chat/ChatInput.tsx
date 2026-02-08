import { useState, useRef } from 'react'

interface Props {
  onSend: (text: string) => void
  disabled: boolean
  onCancel: () => void
  isSending: boolean
}

export default function ChatInput({ onSend, disabled, onCancel, isSending }: Props) {
  const [text, setText] = useState('')
  const inputRef = useRef<HTMLTextAreaElement>(null)

  const handleSubmit = () => {
    const trimmed = text.trim()
    if (!trimmed || disabled) return
    onSend(trimmed)
    setText('')
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  return (
    <div className="chat-input-container">
      <textarea
        ref={inputRef}
        className="chat-input"
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Describe what you want to build..."
        disabled={disabled}
        rows={2}
      />
      <div className="chat-input-actions">
        {isSending ? (
          <button className="chat-btn cancel" onClick={onCancel}>
            Cancel
          </button>
        ) : (
          <button className="chat-btn send" onClick={handleSubmit} disabled={!text.trim()}>
            Send
          </button>
        )}
      </div>
    </div>
  )
}
