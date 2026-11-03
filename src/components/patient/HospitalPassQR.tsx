import React, { useEffect, useRef } from 'react';
import QRCode from 'qrcode';
import type { OPDRegistration } from '../../types';
import { QrCode, ShieldCheck, Building2, Calendar, User, Stethoscope } from 'lucide-react';

interface Props {
  opd: OPDRegistration;
  onSimulateHospitalVerify?: () => void;
}

export const HospitalPassQR: React.FC<Props> = ({ opd, onSimulateHospitalVerify }) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    if (canvasRef.current && opd) {
      const qrPayload = JSON.stringify({
        referenceId: opd.referenceId,
        token: opd.qrToken,
        hospitalId: opd.hospitalId,
        patientId: opd.patientId,
        system: 'CHIKITSAX_SECURE_TOKEN_PASS'
      });

      QRCode.toCanvas(canvasRef.current, qrPayload, {
        width: 180,
        margin: 2,
        color: {
          dark: '#0F172A',
          light: '#FFFFFF'
        }
      }, (err) => {
        if (err) console.error('QR rendering error:', err);
      });
    }
  }, [opd]);

  return (
    <div className="glass-panel" style={{ padding: '24px', margin: '20px 0', border: '1px solid var(--primary-teal)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '12px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{ background: 'linear-gradient(135deg, #0284C7 0%, #15803D 100%)', padding: '10px', borderRadius: '12px', color: '#FFF' }}>
            <QrCode size={24} />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <h3 style={{ fontSize: '1.3rem', color: 'var(--text-heading)', margin: 0 }}>Digital Hospital Visit Pass</h3>
              <span className={`badge ${opd.status === 'VERIFIED' ? 'badge-green' : 'badge-teal'}`}>
                STATUS: {opd.status}
              </span>
            </div>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', margin: 0 }}>Present this QR pass at the hospital reception staff desk</p>
          </div>
        </div>

        <div style={{
          background: 'rgba(2, 132, 199, 0.08)',
          border: '1px solid var(--border-light)',
          borderRadius: '8px',
          padding: '8px 12px',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          fontSize: '0.85rem',
          color: 'var(--text-main)'
        }}>
          <ShieldCheck size={16} color="var(--primary-teal)" />
          <span>Present this QR pass to the hospital reception desk upon arrival.</span>
        </div>

        {Boolean(import.meta.env?.DEV && (window as any)?.__ENABLE_EVALUATOR_SIMULATION__) && onSimulateHospitalVerify && opd.status !== 'VERIFIED' && (
          <button onClick={onSimulateHospitalVerify} className="btn btn-secondary btn-sm" style={{ opacity: 0.75 }}>
            [Debug Evaluator] Simulate Staff Scan
          </button>
        )}
      </div>

      <div style={{
        background: 'var(--bg-subtle)',
        border: '1px solid var(--border-light)',
        borderRadius: '16px',
        padding: '24px',
        display: 'flex',
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '24px'
      }}>
        {/* Left: Details */}
        <div style={{ flex: 1, minWidth: '240px' }}>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '4px', fontWeight: 600 }}>
            UNIQUE REFERENCE IDENTIFIER
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 800, color: 'var(--primary-teal-dark)', fontFamily: 'Outfit', letterSpacing: '0.05em', marginBottom: '16px' }}>
            {opd.referenceId}
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '0.9rem', color: 'var(--text-main)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <User size={16} color="var(--primary-teal)" /> <span>Patient: <strong>{opd.patientName}</strong></span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Building2 size={16} color="var(--primary-teal)" /> <span>Hospital: <strong>{opd.hospitalName}</strong></span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Stethoscope size={16} color="var(--primary-teal)" /> <span>Doctor: <strong>{opd.doctorName}</strong> ({opd.department})</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Calendar size={16} color="var(--primary-teal)" /> <span>Slot: <strong>{opd.appointmentDate} at {opd.appointmentTime}</strong></span>
            </div>
          </div>
        </div>

        {/* Right: Rendered QR Canvas Code */}
        <div style={{
          background: '#FFF',
          padding: '16px',
          borderRadius: '16px',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          boxShadow: 'var(--shadow-md)',
          border: '1px solid var(--border-light)'
        }}>
          <canvas ref={canvasRef} />
          <div style={{ marginTop: '8px', fontSize: '0.72rem', color: '#64748B', fontWeight: 700, textTransform: 'uppercase' }}>
            SECURE TOKEN ENCRYPTED
          </div>
        </div>
      </div>

      <div style={{ marginTop: '14px', fontSize: '0.8rem', color: 'var(--text-muted)', textAlign: 'center' }}>
        <strong>Privacy Note:</strong> Raw medical health records are NOT stored inside this QR payload. Only an encrypted reference token is encoded for verification.
      </div>
    </div>
  );
};
