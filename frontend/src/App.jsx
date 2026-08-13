/**
 * App.jsx — React Router layout + route definitions.
 *
 * Layout:
 *   ┌──────────┬───────────────────────────────┐
 *   │ Sidebar  │  Navbar                       │
 *   │ (lg+)    ├───────────────────────────────┤
 *   │          │  <Outlet /> via PageWrapper   │
 *   └──────────┴───────────────────────────────┘
 */
import { useState } from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'

import Sidebar     from './components/layout/Sidebar'
import Navbar      from './components/layout/Navbar'
import PageWrapper from './components/layout/PageWrapper'

import Dashboard         from './pages/Dashboard'
import SoilAnalysis      from './pages/SoilAnalysis'
import CropRecommendation from './pages/CropRecommendation'
import FertilizerAdvice  from './pages/FertilizerAdvice'
import IrrigationAdvice  from './pages/IrrigationAdvice'
import History           from './pages/History'

const PAGE_TITLES = {
  '/':           'Dashboard',
  '/analysis':   'Soil Analysis',
  '/crops':      'Crop Recommendation',
  '/fertilizer': 'Fertilizer Advice',
  '/irrigation': 'Irrigation Advice',
  '/history':    'History',
}

function AppLayout() {
  const [menuOpen, setMenuOpen] = useState(false)

  // Determine current title from URL
  const path   = window.location.pathname
  const title  = PAGE_TITLES[path] || 'AgroSmart'

  return (
    <div className="flex min-h-screen bg-gray-50">
      {/* Sidebar — desktop */}
      <Sidebar />

      {/* Mobile drawer overlay */}
      {menuOpen && (
        <div
          className="fixed inset-0 bg-black/30 z-40 lg:hidden"
          onClick={() => setMenuOpen(false)}
        />
      )}

      {/* Main content area */}
      <div className="flex-1 flex flex-col min-h-screen">
        <Navbar
          title={title}
          onMenuClick={() => setMenuOpen((v) => !v)}
        />
        <PageWrapper>
          <Routes>
            <Route path="/"           element={<Dashboard />}          />
            <Route path="/analysis"   element={<SoilAnalysis />}       />
            <Route path="/crops"      element={<CropRecommendation />} />
            <Route path="/fertilizer" element={<FertilizerAdvice />}   />
            <Route path="/irrigation" element={<IrrigationAdvice />}   />
            <Route path="/history"    element={<History />}            />
          </Routes>
        </PageWrapper>
      </div>
    </div>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AppLayout />
    </BrowserRouter>
  )
}
