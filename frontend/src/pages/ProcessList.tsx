import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '../lib/api'
import type { ProcessListResponse } from '../lib/api'
import { navigate } from '../App'

const BANDS = ['All', 'Automate', 'Augment', 'Human-Led']

export default function ProcessList() {
  const [search, setSearch] = useState('')
  const [band, setBand] = useState('')
  const [sortBy, setSortBy] = useState('rank')
  const [sortDir, setSortDir] = useState('asc')
  const [offset, setOffset] = useState(0)
  const limit = 25

  const { data, isLoading, error } = useQuery<ProcessListResponse>({
    queryKey: ['processes', band, search, sortBy, sortDir, offset],
    queryFn: () => api.listProcesses({
      band: band || undefined,
      search: search || undefined,
      sort_by: sortBy,
      sort_dir: sortDir,
      offset,
      limit,
    }),
  })

  const toggleSort = (col: string) => {
    if (sortBy === col) {
      setSortDir(d => d === 'asc' ? 'desc' : 'asc')
    } else {
      setSortBy(col)
      setSortDir(col === 'score' ? 'desc' : 'asc')
    }
    setOffset(0)
  }

  const sortIcon = (col: string) =>
    sortBy === col ? (sortDir === 'asc' ? ' ↑' : ' ↓') : ''

  return (
    <div>
      <div className="page-header">
        <h1>Processes</h1>
        <p>All analyzed processes with scores and rankings</p>
      </div>

      <div className="search-bar">
        <input
          className="form-input"
          placeholder="Search processes…"
          value={search}
          onChange={e => { setSearch(e.target.value); setOffset(0) }}
          style={{ maxWidth: 300 }}
        />
        <div className="filter-chips">
          {BANDS.map(b => (
            <div
              key={b}
              className={`filter-chip ${(b === 'All' ? band === '' : band === b) ? 'active' : ''}`}
              onClick={() => { setBand(b === 'All' ? '' : b); setOffset(0) }}
            >
              {b}
            </div>
          ))}
        </div>
      </div>

      {isLoading ? (
        <div className="loading-state"><div className="spinner" />Loading processes…</div>
      ) : error ? (
        <div className="error-state">Failed to load processes</div>
      ) : !data || data.items.length === 0 ? (
        <div className="empty-state">No processes found. Run the seed script or add a process via Process 101.</div>
      ) : (
        <>
          <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th onClick={() => toggleSort('rank')}>Rank{sortIcon('rank')}</th>
                  <th onClick={() => toggleSort('name')}>Name{sortIcon('name')}</th>
                  <th>Department</th>
                  <th onClick={() => toggleSort('score')}>Score{sortIcon('score')}</th>
                  <th>Band</th>
                  <th>Percentile</th>
                </tr>
              </thead>
              <tbody>
                {data.items.map(p => (
                  <tr key={p.id} onClick={() => navigate(`/process/${p.id}`)}>
                    <td style={{ fontWeight: 600, color: '#e8eaf0' }}>#{p.rank ?? '—'}</td>
                    <td style={{ fontWeight: 500, color: '#e8eaf0', maxWidth: 300, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {p.name}
                    </td>
                    <td>{p.department || '—'}</td>
                    <td style={{ fontWeight: 600 }}>{p.total_score?.toFixed(1) ?? '—'}</td>
                    <td>
                      {p.band ? (
                        <span className={`band-badge ${p.band.toLowerCase().replace('-', '-')}`}>{p.band}</span>
                      ) : '—'}
                    </td>
                    <td>{p.percentile != null ? `${p.percentile.toFixed(0)}%` : '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 16 }}>
            <span style={{ fontSize: 13, color: 'var(--text-muted)' }}>
              Showing {offset + 1}–{Math.min(offset + limit, data.total)} of {data.total}
            </span>
            <div style={{ display: 'flex', gap: 8 }}>
              <button className="btn btn-secondary" disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - limit))}>
                ← Previous
              </button>
              <button className="btn btn-secondary" disabled={offset + limit >= data.total} onClick={() => setOffset(offset + limit)}>
                Next →
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
