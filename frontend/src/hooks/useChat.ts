import { useEffect } from 'react'
import { getMessages } from '../api/chat'
import { useStore } from '../store'

export function useChat(projectId: string | undefined) {
  const { messages, setMessages } = useStore()

  useEffect(() => {
    if (!projectId) return
    let cancelled = false
    getMessages(projectId).then((msgs) => {
      if (!cancelled) setMessages(msgs)
    })
    return () => {
      cancelled = true
    }
  }, [projectId, setMessages])

  return messages
}
