import React, { useState } from 'react';
import { opdService } from '../../services/apiServices';
import type { Hospital, OPDRegistration } from '../../types';
import { db } from '../../db/database';
import { X } from 'lucide-react';

interface Props {
  isOpen: boolean;
  selectedHospital: Hospital | null;
  onClose: () => void;
  onBookingConfirmed: (opd: OPDRegistration) => void;
}

export const OPDRegistrationModal: React.FC<Props> = ({
  isOpen,
  selectedHospital,
  onClose,
  onBookingConfirmed
}) => {
  const doctors = db.getDoctors(selectedHospital?.id);
  const [selectedDocId, setSelectedDocId] = useState<string>(doctors[0]?.id || 'doc-1');
  const [department, setDepartment] = useState<string>('Cardiology');
  const [appDate, setAppDate] = useState<string>('Today (09 Sep 2026)');
  const [timeSlot, setTimeSlot] = useState<string>('11:30 AM');
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!isOpen || !selectedHospital) return null;

  const currentDoctor = doctors.find(d => d.id === selectedDocId) || doctors[0];

  const handleConfirmBooking = async () => {
    setIsSubmitting(true);
    try {
      const opd = await opdService.bookAppointment(
        selectedHospital.id,
        selectedHospital.name,
        department,
        currentDoctor.id,
        currentDoctor.name,
        appDate,
        timeSlot
      );
      onBookingConfirmed(opd);
      onClose();
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content" style={{ maxWidth: '600px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <div>
            <span className="badge badge-teal">OPD REGISTRATION</span>
            <h3 style={{ color: 'var(--text-heading)', fontSize: '1.3rem', margin: '4px 0 0' }}>
              Book OPD Consultation: {selectedHospital.name}
            </h3>
          </div>
          <button onClick={onClose} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}>
            <X size={20} />
          </button>
        </div>

        {/* Selected Hospital Info Card */}
        <div style={{ background: 'var(--bg-subtle)', border: '1px solid var(--border-light)', borderRadius: '12px', padding: '12px', marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '12px' }}>
          <img src={selectedHospital.image} alt={selectedHospital.name} style={{ width: '50px', height: '50px', borderRadius: '10px', objectFit: 'cover' }} />
          <div>
            <div style={{ color: 'var(--text-heading)', fontWeight: 600 }}>{selectedHospital.name}</div>
            <div style={{ color: 'var(--text-secondary)', fontSize: '0.82rem' }}>
              Care Score: {selectedHospital.chikitsaxCareScore}/100 • Distance: {selectedHospital.distanceKm} km
            </div>
          </div>
        </div>

        {/* Form Fields */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', marginBottom: '24px' }}>
          {/* Department Selection */}
          <div>
            <label className="form-label">Specialty Department:</label>
            <select
              value={department}
              onChange={(e) => setDepartment(e.target.value)}
              className="form-control"
            >
              {selectedHospital.specialties.map((spec, i) => (
                <option key={i} value={spec}>{spec}</option>
              ))}
            </select>
          </div>

          {/* Doctor Selection */}
          <div>
            <label className="form-label">Available Specialist Doctor:</label>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {doctors.map((doc) => (
                <div
                  key={doc.id}
                  onClick={() => setSelectedDocId(doc.id)}
                  style={{
                    background: selectedDocId === doc.id ? 'rgba(2, 132, 199, 0.1)' : 'var(--bg-subtle)',
                    border: `1px solid ${selectedDocId === doc.id ? 'var(--primary-teal)' : 'var(--border-light)'}`,
                    borderRadius: '10px',
                    padding: '10px 14px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    cursor: 'pointer'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <img src={doc.avatar} alt={doc.name} style={{ width: '36px', height: '36px', borderRadius: '50%', objectFit: 'cover' }} />
                    <div>
                      <div style={{ color: 'var(--text-heading)', fontWeight: 600, fontSize: '0.9rem' }}>{doc.name}</div>
                      <div style={{ color: 'var(--text-secondary)', fontSize: '0.78rem' }}>{doc.specialty} • {doc.qualification}</div>
                    </div>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ color: 'var(--accent-green)', fontWeight: 600, fontSize: '0.88rem' }}>₹{doc.consultationFee}</div>
                    <div style={{ color: 'var(--warning-amber)', fontSize: '0.75rem' }}>★ {doc.rating}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Date & Time Slot */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
            <div>
              <label className="form-label">Appointment Date:</label>
              <select value={appDate} onChange={(e) => setAppDate(e.target.value)} className="form-control">
                <option value="Today (09 Sep 2026)">Today (09 Sep 2026)</option>
                <option value="Tomorrow (10 Sep 2026)">Tomorrow (10 Sep 2026)</option>
                <option value="Thursday (11 Sep 2026)">Thursday (11 Sep 2026)</option>
              </select>
            </div>

            <div>
              <label className="form-label">Time Slot:</label>
              <select value={timeSlot} onChange={(e) => setTimeSlot(e.target.value)} className="form-control">
                {currentDoctor?.availableSlots.map((slot, idx) => (
                  <option key={idx} value={slot}>{slot}</option>
                ))}
              </select>
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
          <button onClick={onClose} className="btn btn-secondary">
            Cancel
          </button>
          <button onClick={handleConfirmBooking} disabled={isSubmitting} className="btn btn-green">
            {isSubmitting ? 'Generating Reference ID...' : 'Confirm OPD & Generate QR Pass ✓'}
          </button>
        </div>
      </div>
    </div>
  );
};
