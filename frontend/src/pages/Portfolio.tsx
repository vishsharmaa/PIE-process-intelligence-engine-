import { useQuery } from '@tanstack/react-query'
import { api } from '../lib/api'
import type { PortfolioSummary } from '../lib/api'
import { navigate } from '../App'

export default function Portfolio() {
  const { data, isLoading, error } = useQuery<PortfolioSummary>({
    queryKey: ['portfolio'],
    queryFn: api.portfolioSummary,
  })

  if (isLoading) return <div className="loading-state"><div className="spinner" />Loading portfolio…</div>
  if (error) return <div className="error-state">Failed to load portfolio</div>
  if (!data) return <div className="empty-state">No portfolio data available</div>

  return (
    <div>
      <div className="page-header">
        <h1>Portfolio Intelligence & Rankings</h1>
        <p>Complete transformation priority ranking of all analyzed processes</p>
      </div>

      <div className="stats-grid" style={{ marginBottom: 24 }}>
        <div className="stat-card">
          <div className="stat-label">Total Portfolio</div>
          <div className="stat-value">{data.total}</div>
          <div className="stat-sub">processes scored</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Average Score</div>
          <div className="stat-value">{data.avg_score?.toFixed(1) ?? '—'}</div>
          <div className="stat-sub">out of 100</div>
        </div>
        {data.band_counts.map(b => (
          <div className="stat-card" key={b.band}>
            <div className="stat-label">{b.band} Band</div>
            <div className="stat-value">{b.count}</div>
            <div className="stat-sub">{data.total > 0 ? ((b.count / data.total) * 100).toFixed(0) : 0}%</div>
          </div>
        ))}
      </div>

      <div className="card">
        <div className="card-header">
          <div className="card-title">Top Ranked Processes</div>
        </div>
        <table className="data-table">
          <thead>
            <tr>
              <th>Rank</th>
              <th>Process Name</th>
              <th>Department</th>
              <th>Score</th>
              <th>Band</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {data.top_processes.map(p => (
              <tr key={p.id} onClick={() => navigate(`/process/${p.id}`)}>
                <td style={{ fontWeight: 700 }}>#{p.rank ?? '—'}</td>
                <td style={{ fontWeight: 500, color: '#e8eaf0' }}>{p.name}</td>
                <td>{p.department || '—'}</td>
                <td style={{ fontWeight: 600, color: 'var(--accent-light)' }}>{p.total_score?.toFixed(1)}</td>
                <td><span className={`band-badge ${(p.band || '').toLowerCase().replace('-', '-')}`}>{p.band}</span></td>
                <td><button className="btn btn-secondary" style={{ padding: '4px 10px', fontSize: 12 }}>Inspect →</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
