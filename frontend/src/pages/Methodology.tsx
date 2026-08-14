import { useQuery } from '@tanstack/react-query'
import { api } from '../lib/api'
import type { RubricData } from '../lib/api'

export default function Methodology() {
  const { data: rubric } = useQuery<RubricData>({
    queryKey: ['rubric'],
    queryFn: () => api.getRubric('v1'),
  })

  return (
    <div>
      <div className="page-header">
        <h1>Methodology & System Architecture</h1>
        <p>Core Design Principle: AI interprets. Deterministic software decides.</p>
      </div>

      <div className="card methodology-section">
        <h2>Architecture Principle</h2>
        <p>
          The Process Intelligence Engine maintains a strict separation of concerns between AI and deterministic software.
          The Groq LLM is used exclusively for bounded structured information extraction and interpretation.
          Final transformation priority scores, rankings, deduplication, and evidence verification are executed entirely by deterministic Python code.
        </p>

        <div className="flow-diagram">
          <div className="flow-step">Raw Process Input</div>
          <div className="flow-arrow">→</div>
          <div className="flow-step">Validate & Normalize</div>
          <div className="flow-arrow">→</div>
          <div className="flow-step">SHA-256 Dedup</div>
          <div className="flow-arrow">→</div>
          <div className="flow-step">LLM Extraction (Bounded)</div>
          <div className="flow-arrow">→</div>
          <div className="flow-step">Evidence Retrieval</div>
          <div className="flow-arrow">→</div>
          <div className="flow-step">Deterministic Scoring</div>
          <div className="flow-arrow">→</div>
          <div className="flow-step">Portfolio Ranking</div>
        </div>
      </div>

      <div className="grid-2">
        <div className="card methodology-section">
          <h2>LLM Responsibilities</h2>
          <ul>
            <li>Extract bounded 1–5 ordinal feature ratings from unstructured process text</li>
            <li>Provide textual rationale and confidence score for each feature</li>
            <li>Extract 3–5 verifiable factual claims about the process</li>
            <li>Classify natural-language user queries into closed intent types</li>
            <li>Generate 2–3 sentence prose explanations of pre-computed query results</li>
          </ul>
        </div>

        <div className="card methodology-section">
          <h2>Deterministic Software Responsibilities</h2>
          <ul>
            <li>Validate inputs and compute SHA-256 content hashes for deduplication</li>
            <li>Normalize ordinal values <code>(1–5)</code> to <code>0..1</code> scale</li>
            <li>Calculate signed contributions and total score: <code>sum(contribution) ≈ total_score</code></li>
            <li>Enforce safety & regulatory override caps (e.g. high safety constraint caps band at Augment)</li>
            <li>Execute whitelisted parameterized SQL queries for natural language questions</li>
            <li>Verify verbatim quote substrings against manufacturing corpus chunks</li>
          </ul>
        </div>
      </div>

      {rubric && (
        <div className="card methodology-section" style={{ marginTop: 20 }}>
          <h2>Scoring Rubric (Version: {rubric.version})</h2>
          <p style={{ marginBottom: 16 }}>
            The scoring system uses 8 weighted factors. Positive direction factors increase the AI priority score;
            negative direction factors decrease it.
          </p>

          <table className="data-table">
            <thead>
              <tr>
                <th>Factor Key</th>
                <th>Direction</th>
                <th>Weight</th>
                <th>Description</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(rubric.factors).map(([key, val]) => (
                <tr key={key}>
                  <td style={{ fontWeight: 600, color: '#e8eaf0' }}>{key}</td>
                  <td>
                    <span className={`tag ${val.direction === '+' ? 'green' : 'red'}`}>
                      {val.direction} ({val.direction === '+' ? 'Driver' : 'Constraint'})
                    </span>
                  </td>
                  <td style={{ fontWeight: 600 }}>{(val.weight * 100).toFixed(0)}%</td>
                  <td style={{ color: 'var(--text-secondary)' }}>{val.description}</td>
                </tr>
              ))}
            </tbody>
          </table>

          <div style={{ marginTop: 20, display: 'flex', gap: 20, flexWrap: 'wrap' }}>
            <div className="card" style={{ flex: 1, background: 'var(--bg-elevated)' }}>
              <h3>Decision Bands</h3>
              <ul style={{ marginTop: 8 }}>
                <li><strong>Automate:</strong> Score ≥ {rubric.bands.automate_threshold} points</li>
                <li><strong>Augment:</strong> Score ≥ {rubric.bands.augment_threshold} points</li>
                <li><strong>Human-Led:</strong> Score &lt; {rubric.bands.augment_threshold} points</li>
              </ul>
            </div>
            <div className="card" style={{ flex: 1, background: 'var(--bg-elevated)' }}>
              <h3>Override Rules</h3>
              <p style={{ fontSize: 13, marginTop: 8 }}>
                If <code>regulatory_safety_constraint == 5</code> AND <code>human_judgment_dependency &gt;= 4</code>,
                the decision band is capped at <strong>Augment</strong> regardless of total score.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
