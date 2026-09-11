import { Link } from 'react-router-dom';
import Navbar from '../components/Navbar';
import GradientWaves from '../components/GradientWaves/GradientWaves';
import { 
  Bug, 
  ShieldAlert, 
  Zap, 
  Sparkles, 
  Ruler, 
  Bot, 
  Play, 
  ArrowRight, 
  Flame, 
  AlertTriangle, 
  CheckCircle2, 
  Lock, 
  ChevronRight, 
  AlertCircle, 
  FileCode,
  Terminal,
  Braces,
  Coffee
} from 'lucide-react';
import './LandingPage.css';

const LANGUAGES = [
  { label: 'Python', icon: Terminal, color: '#3b82f6' },
  { label: 'JavaScript', icon: Braces, color: '#f59e0b' },
  { label: 'Java', icon: Coffee, color: '#ef4444' }
];

const FEATURES = [
  { icon: Bug, title: 'Find Bugs', desc: 'Detect logical errors and edge cases before they cause issues.', color: '#ef4444' },
  { icon: ShieldAlert, title: 'Security Analysis', desc: 'Identify security vulnerabilities and risky patterns.', color: '#eab308' },
  { icon: Zap, title: 'Performance', desc: 'Get suggestions to improve speed and efficiency.', color: '#3b82f6' },
  { icon: Sparkles, title: 'Code Quality', desc: 'Follow best practices and maintain clean, readable code.', color: '#a855f7' },
  { icon: Ruler, title: 'Design Insights', desc: 'Find design flaws and get architectural recommendations.', color: '#22c55e' },
  { icon: Bot, title: 'AI Powered', desc: 'Advanced LLM analysis tailored for real-world development.', color: '#ec4899' }
];

export default function LandingPage() {
  return (
    <div className="landing">
      <Navbar />

      <section className="hero">
        <div className="hero-bg">
          <GradientWaves
            horizonColor="#040a1f"
            waveColor="#2457FF"
            crestColor="#E8F9FF"
            speed={0.4}
            amplitude={2.5}
            waveScale={0.6}
            waveRatio={0.9}
            swell={35}
            turbulence={20}
            tilt={1.11}
            zoom={1.0}
            height={5.5}
            fogDepth={15}
            detail="medium"
            brightness={1.1}
            opacity={1.0}
            mouseInteraction={true}
            parallaxStrength={0.5}
            grain={true}
            grainIntensity={0.05}
          />
        </div>
        
        <div className="hero-content">
          <div className="hero-badge animate-text delay-1">
            <Sparkles size={14} className="sparkle" /> AI-POWERED • OPEN SOURCE
          </div>
          
          <h1 className="hero-title">
            <div className="hero-title-top animate-text delay-2">Code review that</div>
            <div className="hero-title-bottom animate-text delay-3">
              <span className="text-blue">actually</span> <span className="text-light">helps.</span>
            </div>
          </h1>
          
          <p className="hero-subtitle animate-text delay-4">
            Find bugs, security issues, performance problems, and design flaws
            in your code — all in one response.
          </p>
          
          <div className="hero-langs animate-text delay-5">
            {LANGUAGES.map(l => {
              const LangIcon = l.icon;
              return (
                <span key={l.label} className="lang-badge">
                  <LangIcon size={14} color={l.color} style={{ marginRight: 6 }} /> {l.label}
                </span>
              );
            })}
          </div>
          

        </div>
        
        {/* Floating Annotations */}
        <div className="annotation annotation-left animate-text delay-7">
          <div className="annotation-text">Better code.<br/>Happier developers.</div>
          <svg width="40" height="40" viewBox="0 0 100 100" className="arrow arrow-left">
            <path d="M 10 10 Q 50 80 90 90" fill="none" stroke="currentColor" strokeWidth="2" strokeDasharray="5,5" />
            <polygon points="90,90 80,85 85,75" fill="currentColor" />
          </svg>
        </div>
        
        <div className="annotation annotation-right animate-text delay-8">
          <div className="annotation-text">Open source.<br/>Built for everyone.</div>
          <svg width="40" height="40" viewBox="0 0 100 100" className="arrow arrow-right">
            <path d="M 90 10 Q 50 80 10 90" fill="none" stroke="currentColor" strokeWidth="2" strokeDasharray="5,5" />
            <polygon points="10,90 20,85 15,75" fill="currentColor" />
          </svg>
        </div>
        
        {/* Floating Issue Card */}
        <div className="floating-card floating-issues animate-text delay-6">
          <div className="fc-header">
            <Flame size={16} color="#f97316" style={{ marginRight: 6 }} /> 3 issues found
          </div>
          <div className="fc-body">
            <div className="fc-row"><span>Security</span> <span className="fc-badge">1</span></div>
            <div className="fc-row"><span>Performance</span> <span className="fc-badge">1</span></div>
            <div className="fc-row"><span>Code Quality</span> <span className="fc-badge">1</span></div>
          </div>
        </div>
      </section>

      {/* ── IDE Mockup ── */}
      <section className="mockup-section animate-text delay-5">
        <div className="ide-mockup">
          <div className="ide-header">
            <div className="mac-dots">
              <span className="dot red"></span>
              <span className="dot yellow"></span>
              <span className="dot green"></span>
            </div>
          </div>
          <div className="ide-body">
            <div className="ide-editor">
              <div className="ide-tab">
                <FileCode size={14} color="#38bdf8" style={{ marginRight: 6 }} /> review.py
              </div>
              <div className="ide-code">
                <div className="code-line"><span className="num">1</span> <span className="kw">def</span> <span className="fn">calculate_total</span>(items):</div>
                <div className="code-line"><span className="num">2</span>     total = <span className="num-val">0</span></div>
                <div className="code-line"><span className="num">3</span>     <span className="kw">for</span> item <span className="kw">in</span> items:</div>
                <div className="code-line error-line"><span className="num">4</span>         total += item.price <AlertCircle size={14} color="#f85149" className="error-icon" /></div>
                <div className="code-line"><span className="num">5</span>     <span className="kw">return</span> total</div>
                <div className="code-line"><span className="num">6</span></div>
                <div className="code-line"><span className="num">7</span> <span className="kw">def</span> <span className="fn">get_user</span>(id):</div>
                <div className="code-line"><span className="num">8</span>     user = db.query(User).filter_by(id=id).first()</div>
                <div className="code-line"><span className="num">9</span>     <span className="kw">return</span> user</div>
              </div>
            </div>
            
            <div className="ide-panel">
              <div className="panel-tabs">
                <div className="ptab active">AI Review</div>
                <div className="ptab">Issues <span className="badge">3</span></div>
                <div className="ptab">Suggestions</div>
                <div className="ptab">Summary</div>
              </div>
              
              <div className="panel-content">
                <div className="review-card error">
                  <div className="rc-head">
                    <AlertTriangle size={16} color="#f85149" className="rc-icon" />
                    <span className="rc-title">Performance</span>
                    <ChevronRight size={16} className="rc-arrow" />
                  </div>
                  <div className="rc-desc">Use sum() instead of manually iterating.</div>
                  <div className="rc-snippet">
                    <div className="snip-comment"># Instead of:</div>
                    <div>total = 0</div>
                    <div>for item in items:</div>
                    <div>    total += item.price</div>
                    <div className="snip-comment mt-2"># Use:</div>
                    <div className="snip-green">total = sum(item.price for item in items)</div>
                  </div>
                </div>
                
                <div className="review-card info">
                  <div className="rc-head">
                    <CheckCircle2 size={16} color="#58a6ff" className="rc-icon" />
                    <span className="rc-title">Code Quality</span>
                    <ChevronRight size={16} className="rc-arrow" />
                  </div>
                  <div className="rc-desc">Consider adding type hints for better maintainability.</div>
                </div>
                
                <div className="review-card warning">
                  <div className="rc-head">
                    <Lock size={16} color="#d29922" className="rc-icon" />
                    <span className="rc-title">Security</span>
                    <ChevronRight size={16} className="rc-arrow" />
                  </div>
                  <div className="rc-desc">Validate input data to prevent potential injection attacks.</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── Features Grid ── */}
      <section className="features">
        <div className="features-grid">
          {FEATURES.map((f, i) => {
            const IconComponent = f.icon;
            return (
              <div key={f.title} className={`feature-card animate-text delay-${Math.min(i + 4, 8)}`}>
                <div className="feature-icon">
                  <IconComponent size={28} color={f.color} />
                </div>
                <h3>{f.title}</h3>
                <p>{f.desc}</p>
              </div>
            );
          })}
        </div>
      </section>
      
      {/* ── Stats / Footer CTA ── */}
      <section className="stats-section animate-text delay-5">
        <h2 className="stats-title">Built for developers who care about better code.</h2>
        <div className="stats-grid">
          <div className="stat-item">
            <div className="stat-num">10K+</div>
            <div className="stat-label">Reviews performed</div>
          </div>
          <div className="stat-item">
            <div className="stat-num">98%</div>
            <div className="stat-label">Issues detected</div>
          </div>
          <div className="stat-item">
            <div className="stat-num">3+</div>
            <div className="stat-label">Languages supported</div>
          </div>
          <div className="stat-item">
            <div className="stat-num">100%</div>
            <div className="stat-label">Open source</div>
          </div>
        </div>
      </section>
    </div>
  );
}
