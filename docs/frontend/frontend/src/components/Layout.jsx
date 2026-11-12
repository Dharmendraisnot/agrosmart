import { useState } from 'react';
import { NavLink, Outlet, useLocation } from 'react-router-dom';
import { LayoutDashboard, Activity, Sprout, Camera, History, Server, Menu, X, Leaf, WifiOff } from 'lucide-react';
import { useDemoMode } from '../services/status';
import { useHealth } from '../hooks/useData';

const NAV = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard, end: true },
  { to: '/sensors', label: 'Live Sensors', icon: Activity },
  { to: '/analysis', label: 'AI Analysis', icon: Sprout },
  { to: '/scanner', label: 'Soil Scanner', icon: Camera },
  { to: '/history', label: 'History', icon: History },
  { to: '/system', label: 'System', icon: Server },
];

function SidebarContent({ onNavigate }) {
  const { data: health } = useHealth();
  const online = health?.status === 'ok';
  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center gap-3 px-5 py-6">
        <div className="grid h-10 w-10 place-items-center rounded-xl bg-leaf-600 text-white shadow">
          <Leaf size={22} />
        </div>
        <div>
          <p className="text-lg font-extrabold leading-none text-leaf-900">AgroSmart</p>
          <p className="mt-1 text-[11px] font-medium text-soil-600">AI Soil Intelligence</p>
        </div>
      </div>

      <nav className="flex-1 space-y-1 px-3">
        {NAV.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            onClick={onNavigate}
            className={({ isActive }) =>
              `flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-semibold transition ${
                isActive ? 'bg-leaf-600 text-white shadow-sm' : 'text-slate-600 hover:bg-leaf-50 hover:text-leaf-800'
              }`
            }
          >
            <Icon size={18} />
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="m-3 rounded-xl border border-leaf-100 bg-leaf-50/60 p-3 text-xs">
        <div className="flex items-center gap-2 font-semibold text-leaf-900">
          <span className={`h-2 w-2 rounded-full ${online ? 'bg-leaf-500 animate-pulse' : 'bg-amber-500'}`} />
          {online ? 'Backend online' : 'Checking backend…'}
        </div>
        <p className="mt-1 text-slate-500">Sensor mode: {health?.sensorMode ?? '—'}</p>
      </div>
    </div>
  );
}

export default function Layout() {
  const [open, setOpen] = useState(false);
  const demo = useDemoMode();
  const { pathname } = useLocation();

  return (
    <div className="min-h-screen lg:pl-64">
      {/* Desktop sidebar */}
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-64 border-r border-leaf-100 bg-white/90 backdrop-blur lg:block">
        <SidebarContent />
      </aside>

      {/* Mobile drawer */}
      {open && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <div className="absolute inset-0 bg-slate-900/40" onClick={() => setOpen(false)} />
          <aside className="absolute inset-y-0 left-0 w-64 bg-white shadow-xl">
            <button className="absolute right-3 top-4 text-slate-500" onClick={() => setOpen(false)} aria-label="Close menu">
              <X size={20} />
            </button>
            <SidebarContent onNavigate={() => setOpen(false)} />
          </aside>
        </div>
      )}

      {/* Mobile top bar */}
      <header className="sticky top-0 z-20 flex items-center gap-3 border-b border-leaf-100 bg-white/90 px-4 py-3 backdrop-blur lg:hidden">
        <button onClick={() => setOpen(true)} aria-label="Open menu" className="text-leaf-800">
          <Menu size={22} />
        </button>
        <span className="font-extrabold text-leaf-900">AgroSmart</span>
      </header>

      {demo && (
        <div className="flex items-center justify-center gap-2 bg-amber-100 px-4 py-2 text-xs font-semibold text-amber-900">
          <WifiOff size={14} />
          Demo mode — Flask backend (localhost:5000) is not reachable, showing sample data.
        </div>
      )}

      <main key={pathname} className="fade-up mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8 lg:py-8">
        <Outlet />
      </main>
    </div>
  );
}
