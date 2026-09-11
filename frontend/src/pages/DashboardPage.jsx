import { useState, useCallback, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import api from '../api/client';
import Navbar from '../components/Navbar';
import SplitText from '../components/SplitText/SplitText';
import { 
  Plus, 
  Home, 
  FolderCode, 
  Clock, 
  Star, 
  Settings, 
  UploadCloud, 
  FileText, 
  Sparkles, 
  X, 
  MoreHorizontal, 
  Timer, 
  HardDrive, 
  Wand2, 
  Lightbulb, 
  PartyPopper,
  CheckCircle2,
  Rocket,
  ArrowRight,
  Hexagon,
  Shield,
  Zap,
  AlertTriangle,
  Code2,
  Trash2,
  CornerDownLeft
} from 'lucide-react';
import './DashboardPage.css';

function GithubIcon({ size = 16 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4" />
      <path d="M9 18c-4.51 2-5-2-7-2" />
    </svg>
  );
}

const SEVERITY_COLOR = {
  CRITICAL: '#ef4444',
  HIGH: '#f97316',
  MEDIUM: '#f59e0b',
  LOW: '#3b82f6',
};

const SOURCE_LABEL = {
  AI: 'AI',
  STATIC_ANALYSIS: 'Static',
};

export default function DashboardPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  
  // Navigation & View state
  const [navTab, setNavTab] = useState('home'); // 'home', 'my-reviews', 'history', 'favorites'
  const [uploadMode, setUploadMode] = useState('file'); // 'file', 'paste', 'github'
  const [activeReview, setActiveReview] = useState(null);
  const [reviewsList, setReviewsList] = useState([]);
  const [favorites, setFavorites] = useState(new Set());
  const [showSettingsModal, setShowSettingsModal] = useState(false);
  const [showLearnModal, setShowLearnModal] = useState(false);
  
  // Upload & Paste state
  const [dragging, setDragging] = useState(false);
  const [loading, setLoading] = useState(false);
  const [uploadError, setUploadError] = useState('');
  const [pasteCode, setPasteCode] = useState('');
  const [pasteFilename, setPasteFilename] = useState('auth.py');
  const [githubUrl, setGithubUrl] = useState('');

  // Fetch reviews history
  const fetchReviews = useCallback(() => {
    api.get('/api/v1/reviews/?limit=20').then(res => {
      setReviewsList(res.data.items || []);
      // Auto select latest review if none selected
      if (!activeReview && res.data.items?.length > 0) {
        handleSelectReview(res.data.items[0].id);
      }
    }).catch(() => {});
  }, [activeReview]);

  useEffect(() => {
    fetchReviews();
  }, [fetchReviews]);

  const handleSelectReview = async (id) => {
    try {
      const { data } = await api.get(`/api/v1/reviews/${id}`);
      setActiveReview(data);
    } catch (err) {
      console.error(err);
    }
  };

  const handleDeleteReview = async (id, e) => {
    if (e) e.stopPropagation();
    try {
      await api.delete(`/api/v1/reviews/${id}`);
      setReviewsList(prev => prev.filter(r => r.id !== id));
      if (activeReview?.id === id) setActiveReview(null);
    } catch (err) {
      console.error(err);
    }
  };

  const toggleFavorite = (id, e) => {
    if (e) e.stopPropagation();
    setFavorites(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  // Upload handlers
  const handleFileUpload = async (file) => {
    const ext = '.' + file.name.split('.').pop().toLowerCase();
    const allowed = ['.py', '.js', '.java'];
    if (!allowed.includes(ext)) {
      setUploadError(`Unsupported file type: ${ext}. Allowed: .py, .js, .java`);
      return;
    }
    setUploadError('');
    setLoading(true);
    try {
      const form = new FormData();
      form.append('file', file);
      const { data } = await api.post('/api/v1/reviews/upload', form);
      const formatted = {
        id: data.review?.id || data.id || Date.now(),
        filename: data.filename,
        language: data.language,
        summary: data.review?.summary,
        time_complexity: data.review?.time_complexity,
        space_complexity: data.review?.space_complexity,
        refactored_code: data.review?.refactored_code,
        issues: data.review?.issues || []
      };
      setActiveReview(formatted);
      fetchReviews();
    } catch (err) {
      setUploadError(err.response?.data?.detail || 'Upload failed.');
    } finally {
      setLoading(false);
    }
  };

  const handlePasteSubmit = async () => {
    if (!pasteCode.trim()) {
      setUploadError('Please paste your code snippet before submitting.');
      return;
    }
    setUploadError('');
    setLoading(true);
    try {
      const { data } = await api.post('/api/v1/reviews/paste', {
        filename: pasteFilename.trim() || 'auth.py',
        code: pasteCode
      });
      const formatted = {
        id: data.review?.id || data.id || Date.now(),
        filename: data.filename,
        language: data.language,
        summary: data.review?.summary,
        time_complexity: data.review?.time_complexity,
        space_complexity: data.review?.space_complexity,
        refactored_code: data.review?.refactored_code,
        issues: data.review?.issues || []
      };
      setActiveReview(formatted);
      fetchReviews();
    } catch (err) {
      setUploadError(err.response?.data?.detail || 'Review failed.');
    } finally {
      setLoading(false);
    }
  };

  const handleGithubSubmit = async () => {
    if (!githubUrl.trim()) {
      setUploadError('Please enter a valid GitHub file URL.');
      return;
    }
    setUploadError('');
    setLoading(true);
    try {
      const { data } = await api.post('/api/v1/reviews/github', {
        url: githubUrl.trim()
      });
      const formatted = {
        id: data.review?.id || Date.now(),
        filename: data.filename,
        language: data.language,
        summary: data.review.summary,
        time_complexity: data.review.time_complexity,
        space_complexity: data.review.space_complexity,
        refactored_code: data.review.refactored_code,
        issues: data.review.issues || []
      };
      setActiveReview(formatted);
      fetchReviews();
    } catch (err) {
      setUploadError(err.response?.data?.detail || 'GitHub import failed. Ensure the URL points to a public file (.py, .js, .java).');
    } finally {
      setLoading(false);
    }
  };

  // Severity counts for active review
  const issues = activeReview?.issues || [];
  const criticalCount = issues.filter(i => i.severity === 'CRITICAL').length;
  const highCount = issues.filter(i => i.severity === 'HIGH').length;
  const mediumCount = issues.filter(i => i.severity === 'MEDIUM').length;
  const lowCount = issues.filter(i => i.severity === 'LOW').length;
  const totalIssues = issues.length;

  return (
    <div className="dash-container">
      <Navbar />

      <div className="dash-layout">
        
        {/* ── Left Sidebar ─────────────────────────────────────────────────── */}
        <aside className="dash-sidebar">
          {/* Vertical Nav List */}
          <nav className="nav-menu">
            <button 
              className={`nav-menu-item ${navTab === 'home' ? 'active' : ''}`}
              onClick={() => setNavTab('home')}
            >
              <Home size={18} /> <span>Home</span>
            </button>
            <button 
              className={`nav-menu-item ${navTab === 'my-reviews' ? 'active' : ''}`}
              onClick={() => setNavTab('my-reviews')}
            >
              <FolderCode size={18} /> <span>My Reviews</span>
            </button>
            <button 
              className={`nav-menu-item ${navTab === 'settings' ? 'active' : ''}`}
              onClick={() => setShowSettingsModal(true)}
            >
              <Settings size={18} /> <span>Settings</span>
            </button>
          </nav>

          {/* AI Banner Card */}
          <div className="sidebar-promo-card">
            <div className="promo-header">
              <h3>Better code with AI</h3>
              <div className="promo-sparkle"><Sparkles size={16} color="#c084fc" /></div>
            </div>
            <p>Find bugs, improve quality, and ship faster.</p>
            <button className="btn-learn-more" onClick={() => setShowLearnModal(true)}>
              Learn more <ArrowRight size={14} />
            </button>
          </div>

          {/* Footer Branding */}
          <div className="sidebar-footer">
            <div className="sf-brand">
              <Hexagon size={16} color="#3b82f6" />
              <span>BugLens</span>
            </div>
            <div className="sf-version">v1.0.0 • Open Source</div>
          </div>
        </aside>

        {/* ── Main Center Panel ─────────────────────────────────────────────── */}
        <main className="dash-main">
          
          {/* Welcome Banner */}
          <div className="welcome-banner">
            <div>
              <SplitText 
                tag="h1" 
                className="welcome-title" 
                text={`Welcome back, ${user?.name || 'Allen'}`} 
                delay={25} 
                duration={0.65} 
                ease="power3.out" 
                splitType="chars" 
                from={{ opacity: 0, y: 30 }} 
                to={{ opacity: 1, y: 0 }} 
              />
              <div>
                <SplitText 
                  tag="p" 
                  className="welcome-sub" 
                  text="Upload your code and get instant AI-powered reviews." 
                  delay={15} 
                  duration={0.55} 
                  ease="power3.out" 
                  splitType="words" 
                  from={{ opacity: 0, y: 20 }} 
                  to={{ opacity: 1, y: 0 }} 
                />
              </div>
            </div>
            <div className="quote-box">
              <SplitText 
                tag="p" 
                text="“Good code is a conversation. Make it a better one.”" 
                delay={20} 
                duration={0.6} 
                ease="power3.out" 
                splitType="words" 
                from={{ opacity: 0, y: 15 }} 
                to={{ opacity: 1, y: 0 }} 
              />
            </div>
          </div>

          {/* Upload & Input Container */}
          <div className="upload-container">
            
            {/* Left Upload / Input Area */}
            <div className="upload-left">
              {uploadMode === 'file' && (
                <div 
                  className={`dropzone-box ${dragging ? 'dragging' : ''}`}
                  onDragOver={e => { e.preventDefault(); setDragging(true); }}
                  onDragLeave={() => setDragging(false)}
                  onDrop={e => {
                    e.preventDefault();
                    setDragging(false);
                    if (e.dataTransfer.files[0]) handleFileUpload(e.dataTransfer.files[0]);
                  }}
                >
                  <input 
                    type="file" 
                    accept=".py,.js,.java" 
                    onChange={e => e.target.files[0] && handleFileUpload(e.target.files[0])} 
                    id="file-input-hidden" 
                    hidden 
                  />
                  <label htmlFor="file-input-hidden" className="dropzone-label">
                    <div className="cloud-icon-bg">
                      <UploadCloud size={28} color="#3b82f6" />
                    </div>
                    <div className="dropzone-text">
                      Drop a file or <span className="browse-link">browse</span>
                    </div>
                    <div className="dropzone-hint">.py · .js · .java — Max 25 MB</div>
                  </label>
                </div>
              )}

              {uploadMode === 'paste' && (
                <div className="paste-box">
                  <div className="paste-header">
                    <input 
                      type="text" 
                      className="paste-filename-input" 
                      value={pasteFilename} 
                      onChange={e => setPasteFilename(e.target.value)} 
                      placeholder="Filename (e.g. auth.py)"
                    />
                    <button className="btn-paste-submit" onClick={handlePasteSubmit} disabled={loading}>
                      {loading ? 'Analyzing…' : 'Analyze Code'} <CornerDownLeft size={14} />
                    </button>
                  </div>
                  <textarea 
                    className="paste-textarea"
                    placeholder="Paste your code snippet here..."
                    value={pasteCode}
                    onChange={e => setPasteCode(e.target.value)}
                  />
                </div>
              )}

              {uploadError && <div className="upload-error-msg">{uploadError}</div>}
              {loading && <div className="loading-bar-indicator"><div className="loading-progress" /> Reviewing code with Groq AI...</div>}
            </div>

            {/* Right Mode Selector Tabs */}
            <div className="upload-right-tabs">
              <button 
                className={`tab-btn ${uploadMode === 'file' ? 'active' : ''}`}
                onClick={() => setUploadMode('file')}
              >
                <UploadCloud size={16} /> <span>Upload File</span>
              </button>
              <button 
                className={`tab-btn ${uploadMode === 'paste' ? 'active' : ''}`}
                onClick={() => setUploadMode('paste')}
              >
                <FileText size={16} /> <span>Paste Code</span>
              </button>
            </div>

          </div>

          {/* Dynamic Views: My Reviews / History / Favorites OR Active Review Detail */}
          {navTab === 'my-reviews' || navTab === 'history' || navTab === 'favorites' ? (
            <div className="reviews-list-section">
              <h2 className="section-title-text">
                {navTab === 'my-reviews' && 'My Reviews'}
                {navTab === 'history' && 'Review History'}
                {navTab === 'favorites' && 'Favorite Reviews'}
              </h2>
              <div className="reviews-grid-list">
                {reviewsList
                  .filter(r => navTab !== 'favorites' || favorites.has(r.id))
                  .map(r => (
                    <div 
                      key={r.id} 
                      className={`review-grid-card ${activeReview?.id === r.id ? 'active' : ''}`}
                      onClick={() => {
                        handleSelectReview(r.id);
                        setNavTab('home');
                      }}
                    >
                      <div className="rgc-head">
                        <div className="rgc-title">
                          <Code2 size={16} color="#3b82f6" />
                          <span>{r.filename}</span>
                        </div>
                        <div className="rgc-actions">
                          <button onClick={(e) => toggleFavorite(r.id, e)} className="star-btn">
                            <Star size={14} fill={favorites.has(r.id) ? "#f59e0b" : "none"} color={favorites.has(r.id) ? "#f59e0b" : "rgba(255,255,255,0.4)"} />
                          </button>
                          <button onClick={(e) => handleDeleteReview(r.id, e)} className="del-btn">
                            <Trash2 size={14} />
                          </button>
                        </div>
                      </div>
                      <div className="rgc-meta">
                        <span className="rgc-lang">{r.language}</span>
                        <span className="rgc-count">{r.issue_count} issues</span>
                      </div>
                      <p className="rgc-summary">{r.summary}</p>
                    </div>
                  ))}
              </div>
            </div>
          ) : activeReview ? (
            <ReviewDetail 
              key={activeReview.id} 
              review={activeReview} 
              isFavorite={favorites.has(activeReview.id)}
              onToggleFav={() => toggleFavorite(activeReview.id)}
            />
          ) : (
            <div className="empty-detail-state">
              <Sparkles size={40} color="#3b82f6" />
              <p>Select a review or upload a file above to inspect findings.</p>
            </div>
          )}

        </main>

        {/* ── Right Info Sidebar ───────────────────────────────────────────── */}
        <aside className="dash-right-sidebar">
          
          {/* Review Summary Donut Card */}
          <div className="right-card summary-card">
            <SplitText tag="h3" className="card-title" text="Review Summary" delay={30} duration={0.6} splitType="words" />
            <div className="summary-card-body">
              {/* SVG Donut Chart */}
              <div className="donut-container">
                <svg width="100" height="100" viewBox="0 0 36 36" className="donut-chart">
                  <path
                    className="donut-bg"
                    d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                    fill="none"
                    stroke="rgba(255, 255, 255, 0.08)"
                    strokeWidth="3.8"
                  />
                  <path
                    className="donut-segment"
                    d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                    fill="none"
                    stroke="#3b82f6"
                    strokeWidth="3.8"
                    strokeDasharray={`${totalIssues > 0 ? 100 : 0}, 100`}
                  />
                </svg>
                <div className="donut-text">
                  <span className="donut-num">{totalIssues}</span>
                  <span className="donut-label">{totalIssues === 1 ? 'Issue' : 'Issues'}</span>
                </div>
              </div>

              {/* Severity Legend List */}
              <div className="legend-list">
                <div className="legend-item">
                  <span className="dot critical" />
                  <span className="label">Critical</span>
                  <span className="val">{criticalCount}</span>
                </div>
                <div className="legend-item">
                  <span className="dot high" />
                  <span className="label">High</span>
                  <span className="val">{highCount}</span>
                </div>
                <div className="legend-item">
                  <span className="dot medium" />
                  <span className="label">Medium</span>
                  <span className="val">{mediumCount}</span>
                </div>
                <div className="legend-item">
                  <span className="dot low" />
                  <span className="label">Low</span>
                  <span className="val">{lowCount}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Quick Tips Card */}
          <div className="right-card tips-card">
            <h3 className="card-title">
              <Lightbulb size={16} color="#f59e0b" style={{ marginRight: 6 }} /> Quick Tips
            </h3>
            <ul className="tips-list">
              <li><CheckCircle2 size={15} color="#3b82f6" /> Keep functions small and focused</li>
              <li><CheckCircle2 size={15} color="#3b82f6" /> Use meaningful variable names</li>
              <li><CheckCircle2 size={15} color="#3b82f6" /> Handle errors gracefully</li>
              <li><CheckCircle2 size={15} color="#3b82f6" /> Follow language best practices</li>
            </ul>
          </div>

          {/* Bottom Rocket Card */}
          <div className="right-card promo-rocket-card">
            <div className="rocket-icon-box">
              <Rocket size={20} color="#a855f7" />
            </div>
            <SplitText tag="h4" text="Ship better code." delay={25} duration={0.6} splitType="words" />
            <p>Let AI catch the issues so you can focus on what matters.</p>
          </div>

        </aside>

      </div>

      {/* ── Settings Modal ──────────────────────────────────────────────── */}
      {showSettingsModal && (
        <div className="modal-overlay" onClick={() => setShowSettingsModal(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Settings & AI Config</h2>
              <button className="modal-close-btn" onClick={() => setShowSettingsModal(false)}><X size={18} /></button>
            </div>
            <div className="modal-body">
              <div className="setting-group">
                <label>AI Engine Model</label>
                <select className="setting-input" defaultValue="llama3-70b">
                  <option value="llama3-70b">Groq Llama 3.3 70B Versatile (Fast & Intelligent)</option>
                  <option value="mixtral-8x7b">Groq Mixtral 8x7B</option>
                </select>
              </div>
              <div className="setting-group">
                <label>API Status</label>
                <div className="status-badge-row">
                  <span className="status-dot green" /> FastAPI Backend Online (Port 8000)
                </div>
              </div>
              <div className="setting-group">
                <label>Supported Languages</label>
                <div className="setting-desc">Python (.py), JavaScript (.js), Java (.java)</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ── Learn More Modal ────────────────────────────────────────────── */}
      {showLearnModal && (
        <div className="modal-overlay" onClick={() => setShowLearnModal(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Better Code with AI</h2>
              <button className="modal-close-btn" onClick={() => setShowLearnModal(false)}><X size={18} /></button>
            </div>
            <div className="modal-body">
              <p>Our platform runs static analysis and Groq LLM inference to analyze code complexity, flag security vulnerabilities, and provide automatic refactored solutions.</p>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}

/* ── Review Detail Component ──────────────────────────────────────────────── */
function ReviewDetail({ review, isFavorite, onToggleFav }) {
  const [filter, setFilter] = useState('ALL');
  const [dismissSummary, setDismissSummary] = useState(false);
  const severities = ['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'];

  const issues = filter === 'ALL'
    ? review.issues || []
    : (review.issues || []).filter(i => i.severity === filter);

  const getSeverityCount = (sev) => {
    if (sev === 'ALL') return review.issues?.length || 0;
    return (review.issues || []).filter(i => i.severity === sev).length;
  };

  return (
    <div className="review-detail-card">
      
      {/* Detail Header */}
      <div className="rd-header">
        <div className="rd-title-group">
          <FileText size={20} color="#3b82f6" />
          <SplitText tag="h2" className="rd-filename" text={review.filename} delay={20} duration={0.5} splitType="chars" />
          <span className="rd-lang-badge">{review.language}</span>
          <span className="rd-issue-count-badge">{review.issues?.length ?? review.issue_count} issues</span>
        </div>
        <div className="rd-time-meta">
          <Clock size={14} /> <span>Reviewed just now</span>
          <button onClick={onToggleFav} className="rd-fav-btn" title="Bookmark">
            <Star size={16} fill={isFavorite ? "#f59e0b" : "none"} color={isFavorite ? "#f59e0b" : "rgba(255,255,255,0.4)"} />
          </button>
        </div>
      </div>

      {/* Summary Box */}
      {!dismissSummary && (
        <div className="rd-summary-box">
          <p>{review.summary}</p>
          <button className="summary-close-btn" onClick={() => setDismissSummary(true)}>
            <X size={14} />
          </button>
        </div>
      )}

      {/* Complexity Metrics */}
      {(review.time_complexity || review.space_complexity) && (
        <div className="rd-metrics-row">
          {review.time_complexity && (
            <span className="rd-metric-badge">
              <Timer size={14} /> Time: <strong>{review.time_complexity}</strong>
            </span>
          )}
          {review.space_complexity && (
            <span className="rd-metric-badge">
              <HardDrive size={14} /> Space: <strong>{review.space_complexity}</strong>
            </span>
          )}
        </div>
      )}

      {/* Suggested Refactoring */}
      {review.refactored_code && (
        <div className="rd-refactored-box">
          <h3>
            <Wand2 size={16} color="#38bdf8" /> Suggested Refactoring
          </h3>
          <pre><code>{review.refactored_code}</code></pre>
        </div>
      )}

      {/* Filter Pills */}
      <div className="rd-filter-bar">
        {severities.map(s => {
          const count = getSeverityCount(s);
          const label = s === 'ALL' ? `All (${count})` : `${s.charAt(0) + s.slice(1).toLowerCase()} (${count})`;
          return (
            <button
              key={s}
              className={`rd-filter-pill ${filter === s ? 'active' : ''}`}
              onClick={() => setFilter(s)}
            >
              {label}
            </button>
          );
        })}
      </div>

      {/* Issues List */}
      <div className="rd-issues-list">
        {issues.length === 0 ? (
          <div className="rd-no-issues">
            <PartyPopper size={24} color="#3b82f6" />
            <p>No issues for this filter 🎉</p>
          </div>
        ) : (
          issues.map((issue, i) => (
            <div 
              key={i} 
              className="rd-issue-card" 
              style={{ borderLeftColor: SEVERITY_COLOR[issue.severity] }}
            >
              <div className="rd-issue-header">
                <span className="rd-sev-badge" style={{ color: SEVERITY_COLOR[issue.severity], borderColor: SEVERITY_COLOR[issue.severity] }}>
                  {issue.severity}
                </span>
                <span className="rd-cat-badge">{issue.category}</span>
                <span className="rd-src-badge">{SOURCE_LABEL[issue.source] || issue.source}</span>
                {issue.line && <span className="rd-line-badge">L{issue.line}</span>}
                <button className="rd-more-btn"><MoreHorizontal size={16} /></button>
              </div>

              <h4 className="rd-issue-message">{issue.message}</h4>
              
              {issue.explanation && (
                <p className="rd-issue-explanation">{issue.explanation}</p>
              )}

              {issue.suggestion && (
                <div className="rd-issue-fix">
                  <span className="fix-label">💡 Fix:</span> {issue.suggestion}
                </div>
              )}
            </div>
          ))
        )}
      </div>

    </div>
  );
}
