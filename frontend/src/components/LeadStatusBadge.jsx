import { Phone, Clock, CheckCircle2, XCircle, AlertTriangle, Loader2, HelpCircle } from 'lucide-react'

const STATUS_CONFIG = {
  PENDING: {
    label: 'Pending',
    className: 'badge-pending',
    icon: Clock,
    dot: 'bg-slate-400',
  },
  CALL_INITIATED: {
    label: 'Calling...',
    className: 'badge-call-initiated',
    icon: Phone,
    dot: 'bg-blue-400 animate-pulse',
  },
  QUALIFIED: {
    label: 'Qualified',
    className: 'badge-qualified',
    icon: CheckCircle2,
    dot: 'bg-emerald-400',
  },
  NOT_INTERESTED: {
    label: 'Not Interested',
    className: 'badge-not-interested',
    icon: XCircle,
    dot: 'bg-rose-400',
  },
  FAILED: {
    label: 'Failed',
    className: 'badge-failed',
    icon: AlertTriangle,
    dot: 'bg-orange-400',
  },
  NEEDS_REVIEW: {
    label: 'Needs Review',
    className: 'badge-needs-review',
    icon: HelpCircle,
    dot: 'bg-amber-400',
  },
}

export default function LeadStatusBadge({ status }) {
  const config = STATUS_CONFIG[status] || STATUS_CONFIG.PENDING

  return (
    <span className={config.className}>
      <span className={`w-1.5 h-1.5 rounded-full ${config.dot}`} />
      {config.label}
    </span>
  )
}

export { STATUS_CONFIG }
