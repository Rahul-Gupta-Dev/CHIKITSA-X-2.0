import React from 'react';
import { CheckCircle2 } from 'lucide-react';

interface Props {
  currentStage: number; // 1 to 12
  onStageClick?: (stage: number) => void;
}

const STAGES = [
  { id: 1, name: 'Symptoms', desc: 'AI Voice Intake' },
  { id: 2, name: 'Records', desc: 'OCR Extraction' },
  { id: 3, name: 'Profile', desc: 'Unified Health' },
  { id: 4, name: 'Triage', desc: 'AI Risk Guidance' },
  { id: 5, name: 'Hospitals', desc: 'Care Score Engine' },
  { id: 6, name: 'OPD Booked', desc: 'Ref ID Generated' },
  { id: 7, name: 'QR Pass', desc: 'Hospital Pass' },
  { id: 8, name: 'Verified', desc: 'Hospital Check-in' },
  { id: 9, name: 'Consent', desc: 'Access Granted' },
  { id: 10, name: 'Consultation', desc: 'Doctor & Cost Plan' },
  { id: 11, name: 'Aid Match', desc: 'Insurance/Schemes' },
  { id: 12, name: 'Finance Plan', desc: 'Zero-Gap Plan' }
];

export const CareJourneyTimeline: React.FC<Props> = ({ currentStage, onStageClick }) => {
  return (
    <div style={{
      background: 'var(--bg-subtle)',
      border: '1px solid var(--border-light)',
      borderRadius: '16px',
      padding: '16px 20px',
      margin: '16px 0'
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
        <h4 style={{ fontSize: '0.9rem', color: 'var(--primary-teal-dark)', textTransform: 'uppercase', letterSpacing: '0.05em', margin: 0, fontWeight: 700 }}>
          Connected Patient Care Journey Tracking
        </h4>
        <span className="badge badge-teal">
          Stage {currentStage} of 12: {STAGES[currentStage - 1]?.name}
        </span>
      </div>

      {/* Horizontal Step Indicator */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        overflowX: 'auto',
        paddingBottom: '8px',
        gap: '8px'
      }}>
        {STAGES.map((s) => {
          const isDone = s.id < currentStage;
          const isCurrent = s.id === currentStage;

          return (
            <div
              key={s.id}
              onClick={() => onStageClick && onStageClick(s.id)}
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                minWidth: '80px',
                cursor: onStageClick ? 'pointer' : 'default',
                opacity: isDone || isCurrent ? 1 : 0.6,
                transition: 'opacity 0.2s'
              }}
            >
              <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                width: '32px',
                height: '32px',
                borderRadius: '50%',
                background: isDone
                  ? 'var(--accent-green)'
                  : isCurrent
                  ? 'linear-gradient(135deg, #0284C7 0%, #6D28D9 100%)'
                  : 'var(--border-light)',
                color: isDone || isCurrent ? '#FFF' : 'var(--text-muted)',
                fontWeight: 700,
                fontSize: '0.82rem',
                marginBottom: '4px',
                boxShadow: isCurrent ? '0 0 10px rgba(2, 132, 199, 0.4)' : 'none'
              }}>
                {isDone ? <CheckCircle2 size={18} /> : s.id}
              </div>

              <span style={{
                fontSize: '0.75rem',
                fontWeight: isCurrent ? 700 : 500,
                color: isCurrent ? 'var(--primary-teal)' : isDone ? 'var(--accent-green)' : 'var(--text-muted)',
                textAlign: 'center',
                whiteSpace: 'nowrap'
              }}>
                {s.name}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
};
