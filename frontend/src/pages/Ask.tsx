import { useState } from 'react'
import { api } from '../lib/api'
import type { AskResponse } from '../lib/api'
import { navigate } from '../App'

const SAMPLE_QUESTIONS = [
  "What are the top 5 automation candidates in manufacturing?",
  "Which processes are in the Human-Led band?",
  "Explain the score for Vibration-Based Bearing Failure Prediction",
  "Give me overall portfolio statistics",
]

export default function Ask() {
  const [question, setQuestion] = useState('')
  const [loading, setLoading] = useState(false)
  const [response, setResponse] = useState<AskResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleAsk = async (q: string) => {
    if (!q.trim()) return
    setQuestion(q)
    setLoading(true)
    setError(null)

    try {
      const res = await api.ask(q)
      setResponse(res)
    } catch (err: any) {
      setError(err.message || 'Failed to query')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <div className="page-header">
        <h1>Ask Process Intelligence Engine</h1>
        <p>Natural Language Querying — Intent Classification → Validated QueryPlan → Parameterized SQL</p>
      </div>

      <div className="card" style={{ marginBottom: 24 }}>
        <form onSubmit={e => { e.preventDefault(); handleAsk(question) }}>
          <div className="ask-input-group">
            <input
              className="form-input"
              placeholder="Ask a question about the process portfolio..."
              value={question}
              onChange={e => setQuestion(e.target.value)}
              disabled={loading}
            />
            <button className="btn btn-primary" type="submit" disabled={loading}>
              {loading ? 'Executing Query…' : 'Ask'}
            </button>
          </div>
        </form>

        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
          <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>Try:</span>
          {SAMPLE_QUESTIONS.map(sq => (
            <button
              key={sq}
              className="btn btn-secondary"
              style={{ fontSize: 12, padding: '4px 10px' }}
              onClick={() => handleAsk(sq)}
            >
              {sq}
            </button>
          ))}
        </div>
      </div>

      {error && <div className="error-state">{error}</div>}

      {response && (
        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">Query Results</div>
              <div style={{ marginTop: 4 }}>
                <span className="tag green">Intent: {response.intent}</span>
                {response.unmappable && <span className="tag red">Unmappable</span>}
              </div>
            </div>
          </div>

          {response.unmappable ? (
            <div className="empty-state">
              {response.unmappable_message || 'Question could not be mapped to a whitelisted executor.'}
            </div>
          ) : (
            <div>
              {response.prose_explanation && (
                <div className="description-block" style={{ marginBottom: 16 }}>
                  <strong>Explanation:</strong> {response.prose_explanation}
                </div>
              )}

              {Array.isArray(response.results) && response.results.length > 0 && (
                <table className="data-table">
                  <thead>
                    <tr>
                      {Object.keys(response.results[0]).map(k => (
                        <th key={k}>{k.replace('_', ' ')}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {response.results.map((row: any, i: number) => (
                      <tr key={i} onClick={() => row.id && navigate(`/process/${row.id}`)}>
                        {Object.entries(row).map(([k, v]) => (
                          <td key={k}>
                            {k === 'band' ? (
                              <span className={`band-badge ${(String(v)).toLowerCase().replace('-', '-')}`}>{String(v)}</span>
                            ) : k === 'total_score' && typeof v === 'number' ? (
                              v.toFixed(1)
                            ) : (
                              String(v ?? '—')
                            )}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}

              {typeof response.results === 'object' && !Array.isArray(response.results) && (
                <pre className="query-plan-debug">{JSON.stringify(response.results, null, 2)}</pre>
              )}

              <div style={{ marginTop: 20 }}>
                <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-muted)', marginBottom: 6 }}>
                  DEBUG: VALIDATED QUERY PLAN (No text-to-SQL executed)
                </div>
                <pre className="query-plan-debug">{JSON.stringify(response.query_plan, null, 2)}</pre>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
