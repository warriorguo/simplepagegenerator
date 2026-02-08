import { useCallback, useRef } from 'react'
import { sendMessage } from '../api/chat'
import { useStore } from '../store'

export function useSSE(projectId: string) {
  const abortRef = useRef<AbortController | null>(null)
  const {
    resetStreaming,
    appendToken,
    setStage,
    addToolCall,
    setBuildStatus,
    setStreamDone,
    refreshPreview,
    setIsSending,
  } = useStore()

  const send = useCallback(
    async (message: string) => {
      abortRef.current?.abort()
      const controller = new AbortController()
      abortRef.current = controller

      resetStreaming()
      setIsSending(true)

      try {
        await sendMessage(
          projectId,
          message,
          (event, data) => {
            switch (event) {
              case 'stage_change':
                setStage((data as { stage: string }).stage)
                break
              case 'token':
                appendToken((data as { token: string }).token)
                break
              case 'tool_call':
                addToolCall(
                  (data as { tool: string }).tool,
                  (data as { args: Record<string, string> }).args,
                )
                break
              case 'build_status':
                setBuildStatus(
                  (data as { success: boolean }).success,
                  (data as { errors: string[] }).errors || [],
                )
                break
              case 'done':
                setStreamDone()
                refreshPreview()
                break
              case 'error':
                appendToken(`\nError: ${(data as { message: string }).message}`)
                break
            }
          },
          controller.signal,
        )
      } catch (err) {
        if ((err as Error).name !== 'AbortError') {
          appendToken(`\nError: ${(err as Error).message}`)
        }
      } finally {
        setIsSending(false)
        setStreamDone()
      }
    },
    [projectId, resetStreaming, appendToken, setStage, addToolCall, setBuildStatus, setStreamDone, refreshPreview, setIsSending],
  )

  const cancel = useCallback(() => {
    abortRef.current?.abort()
    setIsSending(false)
  }, [setIsSending])

  return { send, cancel }
}
