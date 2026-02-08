interface Props {
  text: string
}

export default function StreamingText({ text }: Props) {
  return (
    <div className="streaming-text">
      {text}
      <span className="cursor" />
    </div>
  )
}
