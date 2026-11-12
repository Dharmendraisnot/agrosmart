import { Route, Routes, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Sensors from './pages/Sensors';
import Analysis from './pages/Analysis';
import SoilScanner from './pages/SoilScanner';
import History from './pages/History';
import System from './pages/System';

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="sensors" element={<Sensors />} />
        <Route path="analysis" element={<Analysis />} />
        <Route path="analysis/:id" element={<Analysis />} />
        <Route path="scanner" element={<SoilScanner />} />
        <Route path="history" element={<History />} />
        <Route path="system" element={<System />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
