import React from 'react';
import { mockHospitalService } from '../../services/apiServices';
import type { Hospital } from '../../types';
import { X } from 'lucide-react';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onSelectHospital: (hospital: Hospital) => void;
}

export const HospitalCompare: React.FC<Props> = ({ isOpen, onClose, onSelectHospital }) => {
  const hospitals = mockHospitalService.getRankedHospitals().slice(0, 4);

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" style={{ maxWidth: '900px' }} onClick={e => e.stopPropagation()}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <div>
            <span className="badge badge-purple">COMPARISON MATRIX</span>
            <h3 style={{ color: 'var(--text-heading)', fontSize: '1.4rem', margin: '4px 0 0' }}>Side-by-Side Hospital Comparison</h3>
          </div>
          <button onClick={onClose} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', fontSize: '1.4rem', cursor: 'pointer' }}>
            <X size={20} />
          </button>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.88rem', color: 'var(--text-main)' }}>
            <thead>
              <tr style={{ borderBottom: '2px solid var(--border-dark)' }}>
                <th style={{ padding: '12px', textAlign: 'left', color: 'var(--text-muted)', width: '160px' }}>Metric</th>
                {hospitals.map(h => (
                  <th key={h.id} style={{ padding: '12px', textAlign: 'center', color: 'var(--text-heading)' }}>
                    <div style={{ fontSize: '0.95rem', fontWeight: 700 }}>{h.name}</div>
                    <span className="badge badge-teal" style={{ marginTop: '4px' }}>
                      Care Score: {h.chikitsaxCareScore}/100
                    </span>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              <tr style={{ borderBottom: '1px solid var(--border-light)' }}>
                <td style={{ padding: '12px', fontWeight: 600, color: 'var(--text-muted)' }}>Distance</td>
                {hospitals.map(h => (
                  <td key={h.id} style={{ padding: '12px', textAlign: 'center' }}>
                    {h.distanceKm} km
                  </td>
                ))}
              </tr>

              <tr style={{ borderBottom: '1px solid var(--border-light)' }}>
                <td style={{ padding: '12px', fontWeight: 600, color: 'var(--text-muted)' }}>Est. Cost Range</td>
                {hospitals.map(h => (
                  <td key={h.id} style={{ padding: '12px', textAlign: 'center', color: 'var(--accent-green)', fontWeight: 700 }}>
                    ₹{(h.estimatedCostRange.min/1000).toFixed(0)}k – ₹{(h.estimatedCostRange.max/1000).toFixed(0)}k
                  </td>
                ))}
              </tr>

              <tr style={{ borderBottom: '1px solid var(--border-light)' }}>
                <td style={{ padding: '12px', fontWeight: 600, color: 'var(--text-muted)' }}>Emergency Availability</td>
                {hospitals.map(h => (
                  <td key={h.id} style={{ padding: '12px', textAlign: 'center' }}>
                    {h.emergencyAvailable ? (
                      <span style={{ color: 'var(--accent-green)', fontWeight: 600 }}>24/7 Active ({h.emergencyBedsFree} Beds)</span>
                    ) : (
                      <span style={{ color: 'var(--text-muted)' }}>No Emergency Desk</span>
                    )}
                  </td>
                ))}
              </tr>

              <tr style={{ borderBottom: '1px solid var(--border-light)' }}>
                <td style={{ padding: '12px', fontWeight: 600, color: 'var(--text-muted)' }}>Ayushman Bharat / PM-JAY</td>
                {hospitals.map(h => (
                  <td key={h.id} style={{ padding: '12px', textAlign: 'center' }}>
                    {h.acceptedGovSchemes.length > 0 ? (
                      <span className="badge badge-green">Empaneled</span>
                    ) : (
                      <span className="badge badge-amber">Private Cashless Only</span>
                    )}
                  </td>
                ))}
              </tr>

              <tr style={{ borderBottom: '1px solid var(--border-light)' }}>
                <td style={{ padding: '12px', fontWeight: 600, color: 'var(--text-muted)' }}>NGO Desk</td>
                {hospitals.map(h => (
                  <td key={h.id} style={{ padding: '12px', textAlign: 'center', color: 'var(--accent-purple)', fontWeight: 600 }}>
                    {h.ngoPartnerships.length > 0 ? h.ngoPartnerships[0] : 'None'}
                  </td>
                ))}
              </tr>

              <tr>
                <td style={{ padding: '16px 12px', fontWeight: 600, color: 'var(--text-muted)' }}>Action</td>
                {hospitals.map(h => (
                  <td key={h.id} style={{ padding: '16px 12px', textAlign: 'center' }}>
                    <button
                      onClick={() => {
                        onSelectHospital(h);
                        onClose();
                      }}
                      className="btn btn-primary btn-sm"
                    >
                      Select Hospital
                    </button>
                  </td>
                ))}
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
