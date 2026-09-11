import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import GradientWaves from '../components/GradientWaves/GradientWaves';
import Navbar from '../components/Navbar';
import './AuthPage.css';

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ email: '', password: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async e => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(form.email, form.password);
      navigate('/dashboard');
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <Navbar />
      <div className="auth-bg">
        <GradientWaves
          horizonColor="#020512"
          waveColor="#112d8a"
          crestColor="#E8F9FF"
          speed={0.25}
          amplitude={2.0}
          tilt={1.2}
          fogDepth={12}
          brightness={1.1}
          grain={true}
          grainIntensity={0.04}
          mouseInteraction={true}
        />
      </div>
      <div className="auth-center">
        <form className="auth-card animate-text delay-1" onSubmit={handleSubmit}>
          <h2 className="auth-title animate-text delay-2">Welcome back</h2>
          <p className="auth-sub animate-text delay-3">Sign in to view your reviews</p>

          {error && <div className="auth-error animate-text delay-3">{error}</div>}

          <label className="field-label animate-text delay-4">Email</label>
          <input
            className="field-input animate-text delay-4"
            type="email"
            placeholder="you@example.com"
            value={form.email}
            onChange={e => setForm(f => ({ ...f, email: e.target.value }))}
            required
          />

          <label className="field-label animate-text delay-5">Password</label>
          <input
            className="field-input animate-text delay-5"
            type="password"
            placeholder="••••••••"
            value={form.password}
            onChange={e => setForm(f => ({ ...f, password: e.target.value }))}
            required
          />

          <button className="btn btn-primary btn-full animate-text delay-6" type="submit" disabled={loading}>
            {loading ? 'Signing in…' : 'Sign in'}
          </button>

          <p className="auth-switch animate-text delay-7">
            No account? <Link to="/register">Create one →</Link>
          </p>
        </form>
      </div>
    </div>
  );
}
