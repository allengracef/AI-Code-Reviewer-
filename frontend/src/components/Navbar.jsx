import { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { 
  Box, 
  LayoutGrid, 
  ChevronDown,
  LogOut
} from 'lucide-react';
import './Navbar.css';

function GithubIcon({ size = 15 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4" />
      <path d="M9 18c-4.51 2-5-2-7-2" />
    </svg>
  );
}

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [showDropdown, setShowDropdown] = useState(false);

  const handleLogout = () => {
    logout();
    setShowDropdown(false);
    navigate('/');
  };

  const isHome = location.pathname === '/';
  const isDashboard = location.pathname === '/dashboard';

  return (
    <nav className="glass-navbar">
      {/* Brand Logo */}
      <Link to="/" className="glass-brand">
        <div className="glass-logo-box">
          <Box size={18} color="#fff" />
        </div>
        <span className="glass-brand-title">BugLens</span>
      </Link>

      {/* Center Nav Links */}
      <div className="glass-nav-center">
        <Link to="/" className={`glass-nav-item ${isHome ? 'active' : ''}`}>
          {isHome && <span className="active-dot" />}
          <span>Home</span>
        </Link>
        
        <Link to="/dashboard" className={`glass-nav-item ${isDashboard ? 'active' : ''}`}>
          <LayoutGrid size={15} />
          <span>Dashboard</span>
        </Link>

        <a href="https://github.com" target="_blank" rel="noreferrer" className="glass-nav-item">
          <GithubIcon size={15} />
          <span>GitHub</span>
        </a>
      </div>

      {/* Right Controls */}
      <div className="glass-nav-right">
        {user ? (
          <div className="glass-user-container">
            <div 
              className="glass-user-pill" 
              onClick={() => setShowDropdown(!showDropdown)}
            >
              <div className="glass-avatar">
                {user.name ? user.name.charAt(0).toUpperCase() : 'A'}
              </div>
              <span className="glass-username">{user.name || 'Allen'}</span>
              <ChevronDown size={14} className={`chevron ${showDropdown ? 'open' : ''}`} />
            </div>

            {showDropdown && (
              <div className="glass-user-dropdown">
                <button onClick={handleLogout} className="dropdown-logout">
                  <LogOut size={14} />
                  <span>Logout</span>
                </button>
              </div>
            )}
          </div>
        ) : (
          <div className="glass-auth-btns">
            <Link to="/login" className="glass-login-btn">Login</Link>
            <Link to="/register" className="glass-register-btn">Get Started</Link>
          </div>
        )}
      </div>
    </nav>
  );
}
