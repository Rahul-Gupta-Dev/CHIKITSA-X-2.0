import React, { useState } from 'react';
import type { UserRole } from '../../types';
import { db } from '../../db/database';
import { authService } from '../../services/apiServices';
import { UserPlus, AlertCircle } from 'lucide-react';
import { Button } from '../common/UIComponents';

interface RegisterModalProps {
  isOpen: boolean;
  onClose: () => void;
  onRegisterSuccess: (role: UserRole) => void;
  onOpenLogin: () => void;
}

export const RegisterModal: React.FC<RegisterModalProps> = ({
  isOpen,
  onClose,
  onRegisterSuccess,
  onOpenLogin
}) => {
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [role, setRole] = useState<UserRole>('PATIENT');
  const [age, setAge] = useState<number>(35);
  const [gender, setGender] = useState('Male');
  const [phone, setPhone] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  if (!isOpen) return null;

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!fullName || !email || !password) {
      setError('Please fill in all required fields.');
      return;
    }
    if (password.length < 6) {
      setError('Password must be at least 6 characters long.');
      return;
    }
    if (password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const regResult = await authService.register({
        email: email.trim().toLowerCase(),
        password,
        name: fullName.trim(),
        fullName: fullName.trim(),
        role,
        phone: phone ? phone.trim() : undefined,
        age: age ? Number(age) : 30,
        gender
      });

      if (regResult && regResult.user && regResult.token) {
        db.setCurrentUser(regResult.user);
        setIsLoading(false);
        onRegisterSuccess(regResult.user.role as UserRole);
        onClose();
      } else {
        throw new Error('Registration failed: Invalid response from server.');
      }
    } catch (err: any) {
      setIsLoading(false);
      setError(err?.message || 'Registration failed. Please check your details.');
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        className="modal-content"
        style={{ maxWidth: '520px', padding: '28px' }}
        onClick={e => e.stopPropagation()}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '18px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div
              style={{
                padding: '10px',
                background: 'rgba(2, 132, 199, 0.12)',
                borderRadius: '12px',
                color: 'var(--primary-teal)'
              }}
            >
              <UserPlus size={24} />
            </div>
            <div>
              <h2 style={{ fontSize: '1.35rem', margin: 0, color: 'var(--text-heading)' }}>
                Create CHIKITSA-X Account
              </h2>
              <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', margin: 0 }}>
                Register for Unified Care Navigation &amp; Financial Protection
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
              marginBottom: '14px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}
          >
            <AlertCircle size={16} />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleRegister}>
          <div style={{ marginBottom: '14px' }}>
            <label className="form-label">I am registering as</label>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '8px' }}>
              <button
                type="button"
                onClick={() => setRole('PATIENT')}
                style={{
                  padding: '8px',
                  borderRadius: '10px',
                  border: role === 'PATIENT' ? '2px solid var(--primary-teal)' : '1px solid var(--border-light)',
                  background: role === 'PATIENT' ? 'rgba(2, 132, 199, 0.12)' : 'var(--bg-subtle)',
                  color: 'var(--text-main)',
                  fontSize: '0.82rem',
                  fontWeight: 600,
                  cursor: 'pointer'
                }}
              >
                Patient / Family
              </button>
              <button
                type="button"
                onClick={() => setRole('DOCTOR')}
                style={{
                  padding: '8px',
                  borderRadius: '10px',
                  border: role === 'DOCTOR' ? '2px solid #7C3AED' : '1px solid var(--border-light)',
                  background: role === 'DOCTOR' ? 'rgba(124, 58, 237, 0.12)' : 'var(--bg-subtle)',
                  color: 'var(--text-main)',
                  fontSize: '0.82rem',
                  fontWeight: 600,
                  cursor: 'pointer'
                }}
              >
                Doctor (NMC)
              </button>
              <button
                type="button"
                onClick={() => setRole('HOSPITAL_ADMIN')}
                style={{
                  padding: '8px',
                  borderRadius: '10px',
                  border: role === 'HOSPITAL_ADMIN' ? '2px solid #16A34A' : '1px solid var(--border-light)',
                  background: role === 'HOSPITAL_ADMIN' ? 'rgba(22, 163, 74, 0.12)' : 'var(--bg-subtle)',
                  color: 'var(--text-main)',
                  fontSize: '0.82rem',
                  fontWeight: 600,
                  cursor: 'pointer'
                }}
              >
                Hospital / Clinic
              </button>
            </div>
            {role !== 'PATIENT' && (
              <p style={{ fontSize: '0.78rem', color: '#DC2626', margin: '6px 0 0', fontWeight: 600 }}>
                Notice: Privileged accounts (Doctor, Hospital Admin) cannot be self-registered publicly. They must be provisioned by authorized hospital administration.
              </p>
            )}
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '12px' }}>
            <div>
              <label className="form-label">Full Name</label>
              <input
                type="text"
                required
                value={fullName}
                onChange={e => setFullName(e.target.value)}
                placeholder="Ramesh Sharma"
                className="form-control"
              />
            </div>
            <div>
              <label className="form-label">Phone Number</label>
              <input
                type="tel"
                value={phone}
                onChange={e => setPhone(e.target.value)}
                placeholder="+91 98765 43210"
                className="form-control"
              />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '12px' }}>
            <div>
              <label className="form-label">Age</label>
              <input
                type="number"
                min={1}
                max={120}
                value={age}
                onChange={e => setAge(Number(e.target.value))}
                className="form-control"
              />
            </div>
            <div>
              <label className="form-label">Gender</label>
              <select
                value={gender}
                onChange={e => setGender(e.target.value)}
                className="form-control"
              >
                <option value="Male">Male</option>
                <option value="Female">Female</option>
                <option value="Other">Other</option>
              </select>
            </div>
          </div>

          <div style={{ marginBottom: '12px' }}>
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

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '16px' }}>
            <div>
              <label className="form-label">Password</label>
              <input
                type="password"
                required
                value={password}
                onChange={e => setPassword(e.target.value)}
                placeholder="••••••••"
                className="form-control"
              />
            </div>
            <div>
              <label className="form-label">Confirm Password</label>
              <input
                type="password"
                required
                value={confirmPassword}
                onChange={e => setConfirmPassword(e.target.value)}
                placeholder="••••••••"
                className="form-control"
              />
            </div>
          </div>

          <Button
            type="submit"
            variant="teal"
            size="md"
            isLoading={isLoading}
            style={{ width: '100%' }}
          >
            Create My Account
          </Button>

          <div style={{ textAlign: 'center', marginTop: '16px', fontSize: '0.84rem', color: 'var(--text-muted)' }}>
            Already have an account?{' '}
            <button
              type="button"
              onClick={() => {
                onClose();
                onOpenLogin();
              }}
              style={{ background: 'none', border: 'none', color: 'var(--primary-teal)', fontWeight: 600, cursor: 'pointer' }}
            >
              Sign In Instead
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
