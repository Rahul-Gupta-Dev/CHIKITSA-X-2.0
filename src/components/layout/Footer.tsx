import React from 'react';
import { HeartPulse, ShieldAlert, PhoneCall, Building2, Stethoscope, CheckCircle2 } from 'lucide-react';

interface Props {
  onNavigate?: (tab: string) => void;
  onSelectRole?: (role: any) => void;
  onOpenEmergency?: () => void;
}

export const Footer: React.FC<Props> = ({ onNavigate, onSelectRole, onOpenEmergency }) => {
  return (
    <footer style={{
      background: 'var(--bg-header)',
      borderTop: '1px solid var(--border-light)',
      padding: '48px 20px 28px',
      color: 'var(--text-secondary)',
      fontSize: '0.88rem',
      marginTop: 'auto',
      transition: 'background 0.2s ease, border-color 0.2s ease'
    }}>
      <div style={{
        maxWidth: '1360px',
        margin: '0 auto',
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
        gap: '36px',
        marginBottom: '36px'
      }}>
        {/* Col 1: Brand & SIH Context */}
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '14px' }}>
            <div style={{
              background: 'linear-gradient(135deg, #0284C7 0%, #0F172A 100%)',
              padding: '8px',
              borderRadius: '10px',
              color: '#FFF'
            }}>
              <HeartPulse size={22} />
            </div>
            <span style={{ fontSize: '1.35rem', fontWeight: 800, fontFamily: 'Outfit, sans-serif', color: 'var(--text-heading)' }}>
              CHIKITSA<span style={{ color: 'var(--primary-teal)' }}>-X</span>
            </span>
          </div>
          <p style={{ fontSize: '0.84rem', lineHeight: 1.6, color: 'var(--text-secondary)', marginBottom: '16px' }}>
            Next-generation AI-powered connected healthcare ecosystem. Connecting symptoms, clinical triage, hospital discovery, verified OPD check-ins, consent-backed health records, and government financial assistance.
          </p>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
            <span className="badge badge-purple" style={{ fontSize: '0.72rem', padding: '3px 8px' }}>
              SIH INNOVATION MVP
            </span>
            <span className="badge badge-teal" style={{ fontSize: '0.72rem', padding: '3px 8px' }}>
              ABDM READY ARCHITECTURE
            </span>
          </div>
        </div>

        {/* Col 2: Connected Care Journey */}
        <div>
          <h4 style={{ color: 'var(--text-heading)', fontSize: '0.95rem', fontWeight: 700, marginBottom: '14px' }}>
            Connected Care Pathway
          </h4>
          <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '0.83rem' }}>
            <li 
              style={{ cursor: onNavigate ? 'pointer' : 'default', display: 'flex', alignItems: 'center', gap: '6px' }}
              onClick={() => onNavigate && onNavigate('DASHBOARD')}
            >
              <CheckCircle2 size={13} color="var(--primary-teal)" /> AI Voice & Text Symptom Intake
            </li>
            <li 
              style={{ cursor: onNavigate ? 'pointer' : 'default', display: 'flex', alignItems: 'center', gap: '6px' }}
              onClick={() => onNavigate && onNavigate('FIND_HOSPITAL')}
            >
              <CheckCircle2 size={13} color="var(--primary-teal)" /> 5-Factor Care Score Hospital Finder
            </li>
            <li 
              style={{ cursor: onNavigate ? 'pointer' : 'default', display: 'flex', alignItems: 'center', gap: '6px' }}
              onClick={() => onNavigate && onNavigate('BOOK_APPOINTMENT')}
            >
              <CheckCircle2 size={13} color="var(--primary-teal)" /> Direct OPD Slot Booking & Digital Pass
            </li>
            <li 
              style={{ cursor: onNavigate ? 'pointer' : 'default', display: 'flex', alignItems: 'center', gap: '6px' }}
              onClick={() => onNavigate && onNavigate('HEALTH_PROFILE')}
            >
              <CheckCircle2 size={13} color="var(--primary-teal)" /> Medical Records & OCR Extraction
            </li>
            <li 
              style={{ cursor: onNavigate ? 'pointer' : 'default', display: 'flex', alignItems: 'center', gap: '6px' }}
              onClick={() => onNavigate && onNavigate('FINANCIAL_SUPPORT')}
            >
              <CheckCircle2 size={13} color="var(--primary-teal)" /> PM-JAY & State Scheme Gap Calculator
            </li>
          </ul>
        </div>

        {/* Col 3: Role Portals */}
        <div>
          <h4 style={{ color: 'var(--text-heading)', fontSize: '0.95rem', fontWeight: 700, marginBottom: '14px' }}>
            Stakeholder Portals
          </h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '0.83rem' }}>
            <button
              onClick={() => {
                if (onSelectRole) onSelectRole('PATIENT');
                if (onNavigate) onNavigate('DASHBOARD');
              }}
              style={{ background: 'none', border: 'none', padding: 0, textAlign: 'left', color: 'var(--text-secondary)', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px' }}
            >
              <HeartPulse size={14} color="var(--primary-teal)" /> Patient & Caregiver Portal
            </button>
            <button
              onClick={() => {
                if (onSelectRole) onSelectRole('DOCTOR');
                if (onNavigate) onNavigate('DOCTOR_DASHBOARD');
              }}
              style={{ background: 'none', border: 'none', padding: 0, textAlign: 'left', color: 'var(--text-secondary)', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px' }}
            >
              <Stethoscope size={14} color="#8B5CF6" /> Doctor Clinical Workspace
            </button>
            <button
              onClick={() => {
                if (onSelectRole) onSelectRole('HOSPITAL_ADMIN');
                if (onNavigate) onNavigate('HOSPITAL_DASHBOARD');
              }}
              style={{ background: 'none', border: 'none', padding: 0, textAlign: 'left', color: 'var(--text-secondary)', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px' }}
            >
              <Building2 size={14} color="#10B981" /> Hospital Admin & QR Check-In
            </button>
          </div>
        </div>

        {/* Col 4: Emergency Contacts & Disclaimer */}
        <div>
          <h4 style={{ color: 'var(--text-heading)', fontSize: '0.95rem', fontWeight: 700, marginBottom: '14px' }}>
            Emergency & Support
          </h4>
          <div 
            onClick={onOpenEmergency}
            style={{
              background: 'rgba(239, 68, 68, 0.08)',
              border: '1px solid rgba(239, 68, 68, 0.3)',
              borderRadius: '10px',
              padding: '12px 14px',
              marginBottom: '12px',
              cursor: onOpenEmergency ? 'pointer' : 'default'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--danger-red)', fontWeight: 700, fontSize: '0.82rem' }}>
              <PhoneCall size={14} /> National Medical Emergency
            </div>
            <div style={{ color: 'var(--danger-red)', fontWeight: 800, fontSize: '1.25rem', marginTop: '2px' }}>
              108 / 112
            </div>
            <div style={{ fontSize: '0.73rem', color: 'var(--text-muted)', marginTop: '4px' }}>
              Free 24/7 Ambulance Dispatch
            </div>
          </div>

          <div style={{ fontSize: '0.76rem', color: 'var(--text-muted)', lineHeight: 1.5 }}>
            <p style={{ margin: '0 0 6px' }}><strong>PM-JAY Scheme Helpline:</strong> 14555</p>
            <p style={{ margin: 0 }}><strong>National Health Portal:</strong> 1800-180-1104</p>
          </div>
        </div>
      </div>

      {/* Safety Notice & Copyright Strip */}
      <div style={{
        borderTop: '1px solid var(--border-light)',
        paddingTop: '20px',
        maxWidth: '1360px',
        margin: '0 auto',
        display: 'flex',
        flexWrap: 'wrap',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: '14px',
        fontSize: '0.78rem',
        color: 'var(--text-muted)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', maxWidth: '780px' }}>
          <ShieldAlert size={16} color="var(--accent-amber)" style={{ flexShrink: 0 }} />
          <span>
            <strong>AI Medical Disclaimer:</strong> CHIKITSA-X AI symptom triage and cost estimates are decision-support aids for informational guidance only. They do not substitute for licensed clinical judgment, diagnostic evaluations, or in-person emergency hospital care.
          </span>
        </div>

        <div>
          © 2026 CHIKITSA-X Healthcare Platform • Built for SIH Healthcare Innovation
        </div>
      </div>
    </footer>
  );
};
