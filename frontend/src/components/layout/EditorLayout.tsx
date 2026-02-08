import type { ReactNode } from 'react'

interface Props {
  preview: ReactNode
  chat: ReactNode
}

export default function EditorLayout({ preview, chat }: Props) {
  return (
    <div className="editor-layout">
      <div className="editor-preview">{preview}</div>
      <div className="editor-chat">{chat}</div>
    </div>
  )
}
