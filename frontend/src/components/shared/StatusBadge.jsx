/**
 * StatusBadge.jsx — colour-coded health/urgency badge.
 */
import { HEALTH_BADGE } from '../../utils/constants'

export default function StatusBadge({ status }) {
  const cls = HEALTH_BADGE[status] || 'badge-info'
  return <span className={cls}>{status}</span>
}
