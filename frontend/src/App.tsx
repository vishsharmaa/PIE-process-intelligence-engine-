import { useState, useEffect } from 'react'
import Dashboard from './pages/Dashboard'
import ProcessList from './pages/ProcessList'
import ProcessDetailPage from './pages/ProcessDetail'
import Portfolio from './pages/Portfolio'
import Ingest from './pages/Ingest'
import Ask from './pages/Ask'
import Methodology from './pages/Methodology'

type Route =
  | { page: 'dashboard' }
  | { page: 'processes' }
  | { page: 'process'; id: number }
  | { page: 'portfolio' }
  | { page: 'ingest' }
  | { page: 'ask' }
  | { page: 'methodology' }

function parseHash(): Route {
  const hash = window.location.hash.slice(1) || '/'
  if (hash === '/' || hash === '/dashboard') return { page: 'dashboard' }
  if (hash === '/processes') return { page: 'processes' }
  if (hash.startsWith('/process/')) {
    const id = parseInt(hash.split('/')[2], 10)
    return isNaN(id) ? { page: 'processes' } : { page: 'process', id }
  }
  if (hash === '/portfolio') return { page: 'portfolio' }
  if (hash === '/ingest') return { page: 'ingest' }
  if (hash === '/ask') return { page: 'ask' }
  if (hash === '/methodology') return { page: 'methodology' }
  return { page: 'dashboard' }
}

export function navigate(path: string) {
  window.location.hash = path
}

export default function App() {
  const [route, setRoute] = useState<Route>(parseHash)

  useEffect(() => {
    const onHash = () => setRoute(parseHash())
    window.addEventListener('hashchange', onHash)
    return () => window.removeEventListener('hashchange', onHash)
  }, [])

  const navItems = [
    { path: '/dashboard', label: 'Dashboard', icon: '📊' },
    { path: '/processes', label: 'Processes', icon: '⚙️' },
    { path: '/portfolio', label: 'Portfolio', icon: '📈' },
    { path: '/ingest', label: 'Process 101', icon: '➕' },
    { path: '/ask', label: 'Ask PIE', icon: '💬' },
    { path: '/methodology', label: 'Methodology', icon: '📖' },
  ]

  return (
    <div className="app-layout">
      <nav className="sidebar">
        <div className="sidebar-brand" onClick={() => navigate('/dashboard')}>
          <div className="logo">PI</div>
          <span>Process Intel</span>
        </div>
        <div className="nav-links">
          {navItems.map(n => (
            <div
              key={n.path}
              className={`nav-link ${route.page === n.path.slice(1) ? 'active' : ''}`}
              onClick={() => navigate(n.path)}
            >
              <span className="icon">{n.icon}</span>
              {n.label}
            </div>
          ))}
        </div>
      </nav>
      <main className="main-content">
        {route.page === 'dashboard' && <Dashboard />}
        {route.page === 'processes' && <ProcessList />}
        {route.page === 'process' && <ProcessDetailPage id={route.id} />}
        {route.page === 'portfolio' && <Portfolio />}
        {route.page === 'ingest' && <Ingest />}
        {route.page === 'ask' && <Ask />}
        {route.page === 'methodology' && <Methodology />}
      </main>
    </div>
  )
}
