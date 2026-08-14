import { useState } from 'react'
import { api } from '../lib/api'
import type { IngestResponse, JobOut } from '../lib/api'
import { navigate } from '../App'

export default function Ingest() {
  const [name, setName] = useState('')
  const [department, setDepartment] = useState('')
  const [industry, setIndustry] = useState('Manufacturing')
  const [description, setDescription] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [jobId, setJobId] = useState<number | null>(null)
  const [processId, setProcessId] = useState<number | null>(null)
  const [jobStatus, setJobStatus] = useState<JobOut | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!name.trim() || description.trim().length < 20) {
      setError('Please provide a process name and a description of at least 20 characters.')
      return
    }
    setError(null)
    setLoading(true)

    try {
      const res: IngestResponse = await api.ingestProcess({
        name,
        raw_description: description,
        department: department || undefined,
        industry: industry || undefined,
      })
      setJobId(res.job_id)
      setProcessId(res.process_id)
      startPolling(res.job_id)
    } catch (err: any) {
      setError(err.message || 'Ingestion failed')
      setLoading(false)
    }
  }

  const startPolling = (jId: number) => {
    const interval = setInterval(async () => {
      try {
        const job = await api.getJob(jId)
        setJobStatus(job)
        if (job.status === 'completed' || job.status === 'failed') {
          clearInterval(interval)
          setLoading(false)
        }
      } catch (err) {
        console.error(err)
      }
    }, 1000)
  }

  return (
    <div>
      <div className="page-header">
        <h1>Process 101 Ingestion</h1>
        <p>Dynamically ingest a completely new process into the real AI/Data pipeline</p>
      </div>

      <div className="grid-2">
        <div className="card">
          <div className="card-title" style={{ marginBottom: 16 }}>Ingest New Process</div>

          {error && <div className="error-state" style={{ padding: 12, marginBottom: 16 }}>{error}</div>}

          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label className="form-label">Process Name *</label>
              <input
                className="form-input"
                placeholder="e.g., Automated Optical Inspection for SMT Assemblies"
                value={name}
                onChange={e => setName(e.target.value)}
                disabled={loading}
              />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              <div className="form-group">
                <label className="form-label">Department</label>
                <input
                  className="form-input"
                  placeholder="e.g., Quality Control"
                  value={department}
                  onChange={e => setDepartment(e.target.value)}
                  disabled={loading}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Industry</label>
                <input
                  className="form-input"
                  placeholder="e.g., Electronics"
                  value={industry}
                  onChange={e => setIndustry(e.target.value)}
                  disabled={loading}
                />
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">Raw Process Description * (min 20 chars)</label>
              <textarea
                className="form-textarea"
                placeholder="Describe current workflow, data streams, manual steps, cycle time, quality requirements, and regulations..."
                value={description}
                onChange={e => setDescription(e.target.value)}
                disabled={loading}
                rows={6}
              />
            </div>

            <button className="btn btn-primary" type="submit" disabled={loading} style={{ width: '100%', justifyContent: 'center' }}>
              {loading ? 'Running Ingest Pipeline…' : 'Submit Process to Pipeline'}
            </button>
          </form>
        </div>

        <div className="card">
          <div className="card-title" style={{ marginBottom: 16 }}>Real-Time Pipeline Execution</div>
          {!jobId ? (
            <div className="empty-state">
              Submit a process on the left to watch the 9-stage pipeline execute in real time.
            </div>
          ) : (
            <div>
              <div style={{ marginBottom: 16 }}>
                <span className="tag" style={{ fontSize: 13, padding: '4px 10px' }}>Job #{jobId}</span>
                <span className="tag" style={{ marginLeft: 8, fontSize: 13, textTransform: 'uppercase' }}>
                  {jobStatus?.status || 'QUEUED'}
                </span>
              </div>

              {jobStatus && (
                <div>
                  <div className="progress-bar-bg" style={{ marginBottom: 12 }}>
                    <div className="progress-bar-fill" style={{ width: `${jobStatus.progress}%` }} />
                  </div>

                  <div className="job-stage">
                    <span className="dot" />
                    Current Stage: <strong>{jobStatus.stage || 'starting'}</strong> ({jobStatus.progress.toFixed(0)}%)
                  </div>

                  {jobStatus.status === 'completed' && (
                    <div style={{ marginTop: 24, textAlign: 'center' }}>
                      <div style={{ color: 'var(--green)', fontWeight: 600, fontSize: 16, marginBottom: 12 }}>
                        ✓ Ingestion & Scoring Complete!
                      </div>
                      <button className="btn btn-primary" onClick={() => navigate(`/process/${processId}`)}>
                        Inspect Generated Intelligence →
                      </button>
                    </div>
                  )}

                  {jobStatus.status === 'failed' && (
                    <div style={{ marginTop: 20, color: 'var(--red)' }}>
                      <strong>Pipeline Error:</strong> {jobStatus.error}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
