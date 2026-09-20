import React, { useState, useEffect } from 'react';
import { fetchHealth, submitResearchQuestion, HealthResponse, ResearchQuestionResponse } from './api';

export const App: React.FC = () => {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [healthStatus, setHealthStatus] = useState<'checking' | 'online' | 'offline'>('checking');
  const [query, setQuery] = useState('');
  const [discipline, setDiscipline] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submittedQuestion, setSubmittedQuestion] = useState<ResearchQuestionResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    async function checkBackend() {
      try {
        const data = await fetchHealth();
        if (isMounted) {
          setHealth(data);
          setHealthStatus('online');
        }
      } catch {
        if (isMounted) {
          setHealthStatus('offline');
        }
      }
    }

    checkBackend();
    const interval = setInterval(checkBackend, 15000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || isSubmitting) return;

    setIsSubmitting(true);
    setErrorMessage(null);

    try {
      const result = await submitResearchQuestion(query.trim(), discipline.trim() || undefined);
      setSubmittedQuestion(result);
      setQuery('');
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : 'Failed to submit research question');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="app-container">
      <header className="header">
        <div className="title-row">
          <div>
            <h1>ResearchOS</h1>
            <p className="subtitle">Autonomous AI Research Engineer &bull; ₹0 Cost Foundation</p>
          </div>
          <div>
            {healthStatus === 'checking' && (
              <span className="badge checking">
                <span className="dot" /> Checking Backend
              </span>
            )}
            {healthStatus === 'online' && health && (
              <span className="badge online" title={`LLM Provider: ${health.llm_provider}`}>
                <span className="dot" /> Backend Online (v{health.version})
              </span>
            )}
            {healthStatus === 'offline' && (
              <span className="badge offline">
                <span className="dot" /> Backend Offline
              </span>
            )}
          </div>
        </div>
      </header>

      <main>
        <section className="card">
          <h2>Submit Research Question</h2>
          <p className="subtitle" style={{ marginBottom: '1.25rem' }}>
            Formulate a research query, hypothesis, or literature investigation.
          </p>

          {errorMessage && <div className="error-banner">{errorMessage}</div>}

          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="discipline-input">Discipline / Academic Field (Optional)</label>
              <input
                id="discipline-input"
                type="text"
                placeholder="e.g. Machine Learning, Computational Biology, Physics"
                value={discipline}
                onChange={(e) => setDiscipline(e.target.value)}
                disabled={isSubmitting}
              />
            </div>

            <div className="form-group">
              <label htmlFor="question-input">Research Question *</label>
              <textarea
                id="question-input"
                rows={4}
                placeholder="e.g. How does direct preference optimization compare to PPO on sample efficiency for small reasoning models?"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                required
                disabled={isSubmitting}
              />
            </div>

            <button type="submit" disabled={isSubmitting || !query.trim()}>
              {isSubmitting ? 'Submitting to Queue...' : 'Submit to Research Queue'}
            </button>
          </form>

          {submittedQuestion && (
            <div className="result-box">
              <h3 style={{ margin: '0 0 0.5rem 0', fontSize: '1rem', color: '#166534' }}>
                &check; Research Question Registered
              </h3>
              <p style={{ margin: '0.25rem 0', fontSize: '0.95rem' }}>
                <strong>Query:</strong> {submittedQuestion.query}
              </p>
              <div className="meta-grid">
                <div className="meta-item">
                  <strong>ID:</strong> {submittedQuestion.id.slice(0, 8)}...
                </div>
                <div className="meta-item">
                  <strong>Status:</strong> {submittedQuestion.status}
                </div>
                <div className="meta-item">
                  <strong>Discipline:</strong> {submittedQuestion.discipline || 'General'}
                </div>
                <div className="meta-item">
                  <strong>Timestamp:</strong> {new Date(submittedQuestion.created_at).toLocaleTimeString()}
                </div>
              </div>
            </div>
          )}
        </section>

        {health && (
          <section className="card" style={{ backgroundColor: '#fafafa' }}>
            <h3 style={{ margin: '0 0 0.75rem 0', fontSize: '0.95rem', color: '#475569' }}>
              System Runtime Status
            </h3>
            <div className="meta-grid">
              <div className="meta-item">
                <strong>Environment:</strong> {health.environment}
              </div>
              <div className="meta-item">
                <strong>LLM Provider:</strong> {health.llm_provider}
              </div>
              <div className="meta-item">
                <strong>LLM Status:</strong> {health.llm_available ? 'Available' : 'Unavailable'}
              </div>
              <div className="meta-item">
                <strong>Cost Constraint:</strong> &#8377;0 (Free/Local)
              </div>
            </div>
          </section>
        )}
      </main>
    </div>
  );
};

export default App;
