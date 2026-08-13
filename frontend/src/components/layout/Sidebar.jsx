/**
 * Sidebar.jsx — left navigation rail.
 */
import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard, FlaskConical, Sprout,
  Leaf, Droplets, History, Cpu,
} from 'lucide-react'

const NAV_ITEMS = [
  { to: '/',            icon: LayoutDashboard, label: 'Dashboard'    },
  { to: '/analysis',    icon: FlaskConical,    label: 'Soil Analysis' },
  { to: '/crops',       icon: Sprout,          label: 'Crops'        },
  { to: '/fertilizer',  icon: Leaf,            label: 'Fertilizer'   },
  { to: '/irrigation',  icon: Droplets,        label: 'Irrigation'   },
  { to: '/history',     icon: History,         label: 'History'      },
]

export default function Sidebar() {
  return (
    <aside className="hidden lg:flex flex-col w-60 bg-white border-r border-gray-100 min-h-screen">
      {/* Logo */}
      <div className="flex items-center gap-2.5 px-5 py-5 border-b border-gray-100">
        <div className="w-8 h-8 bg-agro-green rounded-lg flex items-center justify-center">
          <Cpu size={16} className="text-white" />
        </div>
        <div>
          <p className="font-bold text-agro-green text-sm leading-tight">AgroSmart</p>
          <p className="text-xs text-gray-400 leading-tight">AI Soil Analysis</p>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-0.5">
        {NAV_ITEMS.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-agro-green-pale text-agro-green'
                  : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
              }`
            }
          >
            <Icon size={17} />
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="px-5 py-4 border-t border-gray-100">
        <p className="text-xs text-gray-400">B.Tech AI/ML Minor Project</p>
      </div>
    </aside>
  )
}
