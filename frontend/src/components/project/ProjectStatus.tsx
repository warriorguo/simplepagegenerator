interface Props {
  status: string
}

export default function ProjectStatus({ status }: Props) {
  return <span className={`status-badge status-${status}`}>{status}</span>
}
