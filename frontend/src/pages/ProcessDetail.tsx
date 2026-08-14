import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '../lib/api'
import type { ProcessDetail, Factor } from '../lib/api'
import { navigate } from '../App'

const FACTOR_LABELS: Record<string, string> = {
  data_availability: 'Data Availability',
  process_repeatability: 'Process Repeatability',
  rule_clarity: 'Rule Clarity',
  volume_frequency: 'Volume / Frequency',
  digital_maturity: 'Digital Maturity',
  error_cost_tolerance: 'Error Tolerance',
  human_judgment_dependency: 'Human Judgment',
  regulatory_safety_constraint: 'Regulatory Constraint',
  override_cap: 'Override Cap',
}

function ScoreWaterfall({ factors, totalScore }: { factors: Factor[]; totalScore: number }) {
  const real = factors.filter(f => f.factor_key !== 'override_cap')
  const maxContrib = Math.max(...real.map(f => Math.abs(f.contribution)), 1)

  return (
    <div className="waterfall-container">
      {real.map(f => (
        <div className="waterfall-row" key={f.factor_key}>
          <div className="waterfall-label">{FACTOR_LABELS[f.factor_key] || f.factor_key}</div>
          <div className="waterfall-bar-bg">
            <div
              className={`waterfall-bar ${f.contribution >= 0 ? 'positive' : 'negative'}`}
              style={{ width: `${(Math.abs(f.contribution) / maxContrib) * 100}%` }}
            />
          </div>
          <div className="waterfall-value" style={{ color: f.contribution >= 0 ? '#22c55e' : '#ef4444' }}>
            {f.contribution >= 0 ? '+' : ''}{f.contribution.toFixed(1)}
          </div>
        </div>
      ))}
      <div className="waterfall-row" style={{ borderTop: '1px solid var(--border)', paddingTop: 8, marginTop: 4 }}>
        <div className="waterfall-label" style={{ fontWeight: 700, color: 'var(--text-primary)' }}>Total</div>
        <div />
        <div className="waterfall-value" style={{ fontWeight: 700, color: 'var(--accent-light)', fontSize: 14 }}>
          {totalScore.toFixed(1)}
        </div>
      </div>
    </div>
  )
}

export default function ProcessDetailPage({ id }: { id: number }) {
  const [tab, setTab] = useState<'overview' | 'features' | 'evidence'>('overview')

  const { data, isLoading, error } = useQuery<ProcessDetail>({
    queryKey: ['process', id],
    queryFn: () => api.getProcess(id),
  })

  if (isLoading) return <div className="loading-state"><div className="spinner" />Loading process…</div>
  if (error) return <div className="error-state">Failed to load process detail.</div>
  if (!data) return <div className="empty-state">Process not found.</div>

  const scoreClass = data.score ? (data.score.total_score >= 70 ? 'high' : data.score.total_score >= 45 ? 'mid' : 'low') : ''

  return (
    <div>
      <div className="back-link" onClick={() => navigate('/processes')}>← Back to Processes</div>

      <div className="detail-header">
        <div className="detail-header-left">
          <h1 style={{ fontSize: 22, fontWeight: 700, marginBottom: 6 }}>{data.name}</h1>
          <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
            {data.department && <span className="tag">{data.department}</span>}
            {data.industry && <span className="tag">{data.industry}</span>}
            <span className="tag" style={{ textTransform: 'capitalize' }}>{data.status}</span>
            {data.rank && (
              <span className="tag">Rank #{data.rank.rank} · Top {data.rank.percentile.toFixed(0)}%</span>
            )}
          </div>
        </div>
        <div className="detail-header-right">
          {data.score && (
            <>
              <div className={`score-circle ${scoreClass}`}>
                {data.score.total_score.toFixed(0)}
              </div>
              <div>
                <span className={`band-badge ${data.score.band.toLowerCase().replace('-', '-')}`} style={{ fontSize: 14, padding: '5px 14px' }}>
                  {data.score.band}
                </span>
              </div>
            </>
          )}
        </div>
      </div>

      <div className="tabs">
        <div className={`tab ${tab === 'overview' ? 'active' : ''}`} onClick={() => setTab('overview')}>Overview & Score</div>
        <div className={`tab ${tab === 'features' ? 'active' : ''}`} onClick={() => setTab('features')}>Features</div>
        <div className={`tab ${tab === 'evidence' ? 'active' : ''}`} onClick={() => setTab('evidence')}>Evidence</div>
      </div>

      {tab === 'overview' && (
        <div>
          {data.score && (
            <div className="card" style={{ marginBottom: 20 }}>
              <div className="card-title" style={{ marginBottom: 12 }}>Recommendation</div>
              <p style={{ fontSize: 14, lineHeight: 1.7, color: 'var(--text-secondary)' }}>
                {data.score.recommendation_text}
              </p>
            </div>
          )}

          {data.score && data.score.factors.length > 0 && (
            <div className="card" style={{ marginBottom: 20 }}>
              <div className="card-header">
                <div>
                  <div className="card-title">Score Waterfall</div>
                  <div className="card-subtitle">
                    Factor contributions sum to {data.score.total_score.toFixed(1)} — SUM(contributions) ≈ total score
                  </div>
                </div>
              </div>
              <ScoreWaterfall factors={data.score.factors} totalScore={data.score.total_score} />
            </div>
          )}

          <div className="card">
            <div className="card-title" style={{ marginBottom: 12 }}>Raw Description</div>
            <div className="description-block">{data.raw_description}</div>
          </div>
        </div>
      )}

      {tab === 'features' && (
        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">Extracted Features</div>
              <div className="card-subtitle">LLM-extracted ordinal values (1–5), normalized (0–1), with rationale</div>
            </div>
          </div>
          {data.features.length === 0 ? (
            <div className="empty-state">No features extracted yet</div>
          ) : (
            <table className="data-table feature-table">
              <thead>
                <tr>
                  <th>Factor</th>
                  <th>Ordinal (1–5)</th>
                  <th>Normalized</th>
                  <th>Confidence</th>
                  <th>Rationale</th>
                </tr>
              </thead>
              <tbody>
                {data.features.map(f => (
                  <tr key={f.feature_key} style={{ cursor: 'default' }}>
                    <td>{FACTOR_LABELS[f.feature_key] || f.feature_key}</td>
                    <td style={{ fontWeight: 600, fontSize: 15 }}>{f.ordinal_value}</td>
                    <td>{f.normalized_value.toFixed(2)}</td>
                    <td>{f.confidence != null ? `${(f.confidence * 100).toFixed(0)}%` : '—'}</td>
                    <td style={{ maxWidth: 400, fontSize: 12.5, lineHeight: 1.5 }}>
                      {f.rationale || '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {tab === 'evidence' && (
        <div>
          <div className="card-title" style={{ marginBottom: 16 }}>Claims & Evidence Chain</div>
          <div className="card-subtitle" style={{ marginBottom: 16 }}>
            Recommendation → Claim → Retrieved source chunk → Verified quote → Source document
          </div>
          {data.claims.length === 0 ? (
            <div className="empty-state">No claims generated for this process</div>
          ) : (
            <div className="evidence-chain">
              {data.claims.map(claim => (
                <div className="claim-card" key={claim.id}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                    <span className={`tag ${claim.supported ? 'green' : 'red'}`}>
                      {claim.supported ? '✓ Supported' : '✗ Unsupported'}
                    </span>
                    {claim.claim_type && <span className="tag">{claim.claim_type}</span>}
                  </div>
                  <div className="claim-text">{claim.claim_text}</div>

                  {claim.evidence_items.map(ev => (
                    <div className={`evidence-item ${ev.verified ? 'verified' : 'unverified'}`} key={ev.id}>
                      <div style={{ display: 'flex', gap: 6, alignItems: 'center', marginBottom: 4 }}>
                        <span className={`tag ${ev.verified ? 'green' : 'red'}`}>
                          {ev.verified ? '✓ Verified' : '✗ Unverified'}
                        </span>
                        <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                          {ev.verification_method}
                        </span>
                      </div>
                      {ev.quote && <div className="quote-text">"{ev.quote}"</div>}
                      {ev.source_title && (
                        <div className="source-ref">
                          📄 {ev.source_title}
                          {ev.source_publisher && ` · ${ev.source_publisher}`}
                          {ev.source_year && ` (${ev.source_year})`}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
