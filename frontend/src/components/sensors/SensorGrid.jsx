/**
 * SensorGrid.jsx — responsive 2–4 column grid of all SensorCards.
 */
import SensorCard from './SensorCard'
import { SENSOR_KEYS } from '../../utils/constants'

export default function SensorGrid({ reading }) {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
      {SENSOR_KEYS.map((key) => (
        <SensorCard key={key} sensorKey={key} value={reading?.[key]} />
      ))}
    </div>
  )
}
