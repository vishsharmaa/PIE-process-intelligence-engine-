import { useQuery } from '@tanstack/react-query'
import { api } from '../lib/api'
import type { PortfolioSummary } from '../lib/api'
import { navigate } from '../App'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell
} from 'recharts'

const BAND_COLORS: Record<string, string> = {
  'Automate': '#22c55e',
  'Augment': '#eab308',
  'Human-Led': '#ef4444',
}

export default function Dashboard() {
  const { data, isLoading, error } = useQuery<PortfolioSummary>({
    queryKey: ['portfolio'],
    queryFn: api.portfolioSummary,
  })

  if (isLoading) return <div className="loading-state"><div className="spinner" />Loading dashboard…</div>
  if (error) return <div className="error-state">Failed to load dashboard. Is the backend running?</div>
  if (!data) return <div className="empty-state">No data available. Run the seed script first.</div>

  const pieData = data.band_counts.map(b => ({ name: b.band, value: b.count }))
  const distData = data.score_distribution.filter(d => d.count > 0)

  return (
    <div>
      <div className="page-header">
        <h1>Process Intelligence Dashboard</h1>
        <p>AI-powered process analysis — deterministic scoring, evidence-backed recommendations</p>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-label">Total Processes</div>
          <div className="stat-value">{data.total}</div>
          <div className="stat-sub">analyzed through the pipeline</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Average Score</div>
          <div className="stat-value">{data.avg_score?.toFixed(1) ?? '—'}</div>
          <div className="stat-sub">out of 100 points</div>
        </div>
        {data.band_counts.map(b => (
          <div className="stat-card" key={b.band}>
            <div className="stat-label">{b.band}</div>
            <div className="stat-value" style={{ color: BAND_COLORS[b.band] }}>{b.count}</div>
            <div className="stat-sub">{data.total > 0 ? ((b.count / data.total) * 100).toFixed(0) : 0}% of portfolio</div>
          </div>
        ))}
      </div>

      <div className="grid-2">
        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">Band Distribution</div>
              <div className="card-subtitle">Process classification breakdown</div>
            </div>
          </div>
          {pieData.length > 0 ? (
            <ResponsiveContainer width="100%" height={240}>
              <PieChart>
                <Pie data={pieData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={90} label={({ name, value }) => `${name}: ${value}`}>
                  {pieData.map(entry => (
                    <Cell key={entry.name} fill={BAND_COLORS[entry.name] || '#6366f1'} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ background: '#21242f', border: '1px solid #2e3140', borderRadius: 8, color: '#e8eaf0' }} />
              </PieChart>
            </ResponsiveContainer>
          ) : <div className="empty-state">No data</div>}
        </div>

        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">Score Distribution</div>
              <div className="card-subtitle">Histogram of transformation priority scores</div>
            </div>
          </div>
          {distData.length > 0 ? (
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={distData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#2e3140" />
                <XAxis dataKey="range" tick={{ fill: '#9ba1b0', fontSize: 11 }} />
                <YAxis tick={{ fill: '#9ba1b0', fontSize: 11 }} />
                <Tooltip contentStyle={{ background: '#21242f', border: '1px solid #2e3140', borderRadius: 8, color: '#e8eaf0' }} />
                <Bar dataKey="count" fill="#6366f1" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : <div className="empty-state">No data</div>}
        </div>
      </div>

      <div className="grid-2" style={{ marginTop: 20 }}>
        <div className="card">
          <div className="card-header">
            <div className="card-title">Top Automation Candidates</div>
            <button className="btn btn-secondary" onClick={() => navigate('/portfolio')}>View All →</button>
          </div>
          {data.top_processes.length > 0 ? (
            <table className="data-table">
              <thead><tr><th>Process</th><th>Score</th><th>Band</th></tr></thead>
              <tbody>
                {data.top_processes.map(p => (
                  <tr key={p.id} onClick={() => navigate(`/process/${p.id}`)}>
                    <td style={{ color: '#e8eaf0', fontWeight: 500 }}>{p.name}</td>
                    <td>{p.total_score?.toFixed(1)}</td>
                    <td><span className={`band-badge ${(p.band || '').toLowerCase().replace('-', '-')}`}>{p.band}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : <div className="empty-state">No processes scored yet</div>}
        </div>

        <div className="card">
          <div className="card-header">
            <div className="card-title">Lowest Priority (Human-Led)</div>
          </div>
          {data.bottom_processes.length > 0 ? (
            <table className="data-table">
              <thead><tr><th>Process</th><th>Score</th><th>Band</th></tr></thead>
              <tbody>
                {data.bottom_processes.map(p => (
                  <tr key={p.id} onClick={() => navigate(`/process/${p.id}`)}>
                    <td style={{ color: '#e8eaf0', fontWeight: 500 }}>{p.name}</td>
                    <td>{p.total_score?.toFixed(1)}</td>
                    <td><span className={`band-badge ${(p.band || '').toLowerCase().replace('-', '-')}`}>{p.band}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : <div className="empty-state">No processes scored yet</div>}
        </div>
      </div>
    </div>
  )
}
