import React from 'react';
import { Info } from 'lucide-react';

interface Props {
  text?: string;
  type?: 'CLINICAL' | 'FINANCIAL';
}

export const DisclaimerBanner: React.FC<Props> = ({
  text,
  type = 'CLINICAL'
}) => {
  const defaultText = type === 'CLINICAL'
    ? 'AI-Assisted Intake & Triage only. This does NOT provide a medical diagnosis. Professional medical evaluation by a licensed physician is required.'
    : 'Financial figures, scheme matches, and insurance projections are estimates based on prototype rules and subject to hospital billing verification.';

  return (
    <div style={{
      background: 'rgba(109, 40, 217, 0.08)',
      border: '1px solid var(--accent-purple)',
      borderRadius: '10px',
      padding: '10px 14px',
      display: 'flex',
      alignItems: 'center',
      gap: '10px',
      fontSize: '0.82rem',
      color: 'var(--text-main)',
      margin: '12px 0'
    }}>
      <Info size={16} style={{ flexShrink: 0, color: 'var(--accent-purple)' }} />
      <div>
        <strong style={{ color: 'var(--accent-purple)' }}>AI Transparency Notice:</strong> {text || defaultText}
      </div>
    </div>
  );
};
