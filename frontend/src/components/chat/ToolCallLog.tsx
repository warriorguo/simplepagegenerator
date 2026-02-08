interface Props {
  calls: Array<{ tool: string; args: Record<string, string> }>
}

export default function ToolCallLog({ calls }: Props) {
  return (
    <div className="tool-call-log">
      {calls.map((call, i) => (
        <div key={i} className="tool-call">
          <span className="tool-name">{call.tool}</span>
          <span className="tool-args">{call.args.file_path || JSON.stringify(call.args)}</span>
        </div>
      ))}
    </div>
  )
}
