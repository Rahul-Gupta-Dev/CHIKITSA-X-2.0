import React, { useState } from 'react';
import type { UserRole } from '../../types';
import { db } from '../../db/database';
import { authService } from '../../services/apiServices';
import { LogIn, UserCheck, Stethoscope, Building2, AlertCircle, CheckCircle2 } from 'lucide-react';
import { Button } from '../common/UIComponents';

interface LoginModalProps {
  isOpen: boolean;
  onClose: () => void;
  onLoginSuccess: (role: UserRole) => void;
  onOpenRegister: () => void;
}

export const LoginModal: React.FC<LoginModalProps> = ({
  isOpen,
  onClose,
  onLoginSuccess,
  onOpenRegister
}) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState<UserRole>('PATIENT');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [showForgotPassword, setShowForgotPassword] = useState(false);
  const [resetEmailSent, setResetEmailSent] = useState(false);

  if (!isOpen) return null;

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) {
      setError('Please fill in both email and password.');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const backendAuth = await authService.login(email.trim(), password, role);
      if (backendAuth && backendAuth.user && backendAuth.token) {
        const u = {
          id: backendAuth.user.id,
          email: backendAuth.user.email,
          name: backendAuth.user.name,
          role: backendAuth.user.role as UserRole,
          phone: backendAuth.user.phone,
          avatar: backendAuth.user.avatar,
          hospitalId: backendAuth.user.hospitalId,
          doctorProfile: backendAuth.user.doctorProfile,
          patientProfile: backendAuth.user.patientProfile
        };
        db.setCurrentUser(u);
        setIsLoading(false);
        onLoginSuccess(u.role);
        onClose();
        return;
      } else {
        throw new Error('Authentication failed: No user profile received.');
      }
    } catch (err: any) {
      setIsLoading(false);
      const msg = err?.message || 'Login failed. Please check your email, password, and selected role.';
      setError(msg);
      return;
    }
  };

  const handleUseDemoAccount = async (demoRole: UserRole, demoEmail: string) => {
    setEmail(demoEmail);
    setPassword('demo123');
    setRole(demoRole);
    setError(null);
    setIsLoading(true);

    try {
      const backendAuth = await authService.login(demoEmail, 'demo123', demoRole);
      if (backendAuth && backendAuth.user && backendAuth.token) {
        const u = {
          id: backendAuth.user.id,
          email: backendAuth.user.email,
          name: backendAuth.user.name,
          role: backendAuth.user.role as UserRole,
          phone: backendAuth.user.phone,
          avatar: backendAuth.user.avatar,
          hospitalId: backendAuth.user.hospitalId,
          doctorProfile: backendAuth.user.doctorProfile,
          patientProfile: backendAuth.user.patientProfile
        };
        db.setCurrentUser(u);
        setIsLoading(false);
        onLoginSuccess(u.role);
        onClose();
      } else {
        throw new Error(`Failed to log in as ${demoRole}.`);
      }
    } catch (err: any) {
      setIsLoading(false);
      setError(err?.message || `Failed to authenticate ${demoRole} demo account on backend.`);
    }
  };

  const handleForgotPasswordSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) {
      setError('Please enter your account email to receive a password recovery link.');
      return;
    }
    setResetEmailSent(true);
    setError(null);
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        className="modal-content"
        style={{ maxWidth: '480px', padding: '28px' }}
        onClick={e => e.stopPropagation()}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div
              style={{
                padding: '10px',
                background: 'rgba(2, 132, 199, 0.12)',
                borderRadius: '12px',
                color: 'var(--primary-teal)'
              }}
            >
              <LogIn size={24} />
            </div>
            <div>
              <h2 style={{ fontSize: '1.35rem', margin: 0, color: 'var(--text-heading)' }}>
                {showForgotPassword ? 'Reset Password' : 'Sign In to CHIKITSA-X'}
              </h2>
              <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', margin: 0 }}>
                {showForgotPassword ? 'Enter your email to receive recovery instructions' : 'Access Patient, Doctor, Hospital, or Admin Portal'}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            style={{ background: 'none', border: 'none', color: 'var(--text-muted)', fontSize: '1.4rem', cursor: 'pointer' }}
          >
            ×
          </button>
        </div>

        {error && (
          <div
            style={{
              padding: '10px 14px',
              background: 'rgba(220, 38, 38, 0.1)',
              border: '1px solid rgba(220, 38, 38, 0.3)',
              borderRadius: '10px',
              color: '#DC2626',
              fontSize: '0.85rem',
              marginBottom: '16px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}
          >
            <AlertCircle size={16} />
            <span>{error}</span>
          </div>
        )}

        {showForgotPassword ? (
          <div>
            {resetEmailSent ? (
              <div style={{ textAlign: 'center', padding: '20px 0' }}>
                <CheckCircle2 size={42} color="#16A34A" style={{ margin: '0 auto 12px' }} />
                <h4 style={{ margin: '0 0 6px', color: 'var(--text-heading)' }}>Reset Link Dispatched</h4>
                <p style={{ color: 'var(--text-muted)', fontSize: '0.88rem', marginBottom: '20px' }}>
                  If an account exists for <strong>{email}</strong>, a secure password reset link has been dispatched.
                </p>
                <Button
                  variant="secondary"
                  onClick={() => {
                    setShowForgotPassword(false);
                    setResetEmailSent(false);
                  }}
                >
                  Back to Sign In
                </Button>
              </div>
            ) : (
              <form onSubmit={handleForgotPasswordSubmit}>
                <div style={{ marginBottom: '16px' }}>
                  <label className="form-label">Account Email Address</label>
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={e => setEmail(e.target.value)}
                    placeholder="Enter your registered email address"
                    className="form-control"
                  />
                </div>
                <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
                  <Button variant="secondary" onClick={() => setShowForgotPassword(false)}>
                    Cancel
                  </Button>
                  <Button type="submit" variant="teal">
                    Send Recovery Link
                  </Button>
                </div>
              </form>
            )}
          </div>
        ) : (
          <form onSubmit={handleLogin}>
            {/* Role Selection */}
            <div style={{ marginBottom: '16px' }}>
              <label className="form-label">Select Portal / Role</label>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '6px' }}>
                <button
                  type="button"
                  onClick={() => setRole('PATIENT')}
                  style={{
                    padding: '8px 4px',
                    borderRadius: '10px',
                    border: role === 'PATIENT' ? '2px solid var(--primary-teal)' : '1px solid var(--border-light)',
                    background: role === 'PATIENT' ? 'rgba(2, 132, 199, 0.12)' : 'var(--bg-subtle)',
                    color: 'var(--text-main)',
                    fontSize: '0.76rem',
                    fontWeight: 600,
                    cursor: 'pointer',
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    gap: '4px'
                  }}
                >
                  <UserCheck size={16} color="var(--primary-teal)" />
                  Patient
                </button>

                <button
                  type="button"
                  onClick={() => setRole('DOCTOR')}
                  style={{
                    padding: '8px 4px',
                    borderRadius: '10px',
                    border: role === 'DOCTOR' ? '2px solid #7C3AED' : '1px solid var(--border-light)',
                    background: role === 'DOCTOR' ? 'rgba(124, 58, 237, 0.12)' : 'var(--bg-subtle)',
                    color: 'var(--text-main)',
                    fontSize: '0.76rem',
                    fontWeight: 600,
                    cursor: 'pointer',
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    gap: '4px'
                  }}
                >
                  <Stethoscope size={16} color="#7C3AED" />
                  Doctor
                </button>

                <button
                  type="button"
                  onClick={() => setRole('HOSPITAL_ADMIN')}
                  style={{
                    padding: '8px 4px',
                    borderRadius: '10px',
                    border: role === 'HOSPITAL_ADMIN' ? '2px solid #16A34A' : '1px solid var(--border-light)',
                    background: role === 'HOSPITAL_ADMIN' ? 'rgba(22, 163, 74, 0.12)' : 'var(--bg-subtle)',
                    color: 'var(--text-main)',
                    fontSize: '0.76rem',
                    fontWeight: 600,
                    cursor: 'pointer',
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    gap: '4px'
                  }}
                >
                  <Building2 size={16} color="#16A34A" />
                  Hospital
                </button>
              </div>
            </div>

            {/* Email Field */}
            <div style={{ marginBottom: '14px' }}>
              <label className="form-label">Email Address</label>
              <input
                type="email"
                required
                value={email}
                onChange={e => setEmail(e.target.value)}
                placeholder="name@example.com"
                className="form-control"
              />
            </div>

            {/* Password Field */}
            <div style={{ marginBottom: '8px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <label className="form-label" style={{ marginBottom: 0 }}>Password</label>
                <button
                  type="button"
                  onClick={() => setShowForgotPassword(true)}
                  style={{ background: 'none', border: 'none', color: 'var(--primary-teal)', fontSize: '0.78rem', cursor: 'pointer', padding: 0 }}
                >
                  Forgot Password?
                </button>
              </div>
              <input
                type="password"
                required
                value={password}
                onChange={e => setPassword(e.target.value)}
                placeholder="••••••••"
                className="form-control"
                style={{ marginTop: '6px' }}
              />
            </div>

            <Button
              type="submit"
              variant="teal"
              size="md"
              isLoading={isLoading}
              style={{ width: '100%', marginTop: '16px' }}
            >
              Sign In to {role.replace('_', ' ')}
            </Button>
          </form>
        )}

        {/* Demo Accounts Quick Fill (Essential for Hackathon Judges) */}
        {!showForgotPassword && (
          <div style={{ marginTop: '20px', borderTop: '1px solid var(--border-light)', paddingTop: '16px' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', display: 'block', marginBottom: '8px', textTransform: 'uppercase' }}>
              Demo Quick-Fill for Evaluators:
            </span>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '6px' }}>
              <button
                type="button"
                onClick={() => handleUseDemoAccount('PATIENT', 'patient@chikitsax.demo')}
                style={{
                  padding: '6px 10px',
                  borderRadius: '8px',
                  background: 'var(--bg-subtle)',
                  border: '1px solid var(--border-light)',
                  color: 'var(--text-main)',
                  fontSize: '0.75rem',
                  textAlign: 'left',
                  cursor: 'pointer'
                }}
              >
                👤 <strong>Patient:</strong> Ramesh
              </button>

              <button
                type="button"
                onClick={() => handleUseDemoAccount('DOCTOR', 'doctor@chikitsax.demo')}
                style={{
                  padding: '6px 10px',
                  borderRadius: '8px',
                  background: 'var(--bg-subtle)',
                  border: '1px solid var(--border-light)',
                  color: 'var(--text-main)',
                  fontSize: '0.75rem',
                  textAlign: 'left',
                  cursor: 'pointer'
                }}
              >
                🩺 <strong>Doctor:</strong> Dr. Rajesh
              </button>

              <button
                type="button"
                onClick={() => handleUseDemoAccount('HOSPITAL_ADMIN', 'hospital@chikitsax.demo')}
                style={{
                  padding: '6px 10px',
                  borderRadius: '8px',
                  background: 'var(--bg-subtle)',
                  border: '1px solid var(--border-light)',
                  color: 'var(--text-main)',
                  fontSize: '0.75rem',
                  textAlign: 'left',
                  cursor: 'pointer'
                }}
              >
                🏥 <strong>Hospital:</strong> CarePlus Desk
              </button>
            </div>

            <div style={{ textAlign: 'center', marginTop: '16px', fontSize: '0.84rem', color: 'var(--text-muted)' }}>
              Don't have an account?{' '}
              <button
                onClick={() => {
                  onClose();
                  onOpenRegister();
                }}
                style={{ background: 'none', border: 'none', color: 'var(--primary-teal)', fontWeight: 600, cursor: 'pointer' }}
              >
                Create Patient Account
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
