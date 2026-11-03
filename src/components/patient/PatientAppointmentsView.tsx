import React, { useState, useEffect } from 'react';
import type { OPDRegistration } from '../../types';
import { db } from '../../db/database';
import { opdService } from '../../services/apiServices';
import {
  Calendar,
  Clock,
  Stethoscope,
  QrCode,
  ExternalLink,
  RotateCcw,
  XCircle,
  Loader2,
  AlertCircle
} from 'lucide-react';
import { Button, Card, Badge, EmptyState, ConfirmationDialog } from '../common/UIComponents';
import { HospitalPassQR } from './HospitalPassQR';

interface Props {
  onBookNew: () => void;
  onNavigateHospitals: () => void;
}

export const PatientAppointmentsView: React.FC<Props> = ({ onBookNew, onNavigateHospitals }) => {
  const [appointments, setAppointments] = useState<OPDRegistration[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'UPCOMING' | 'COMPLETED' | 'CANCELLED'>('UPCOMING');
  const [selectedQRPass, setSelectedQRPass] = useState<OPDRegistration | null>(null);

  // Cancellation State
  const [cancellingApp, setCancellingApp] = useState<OPDRegistration | null>(null);
  const [isCancelling, setIsCancelling] = useState<boolean>(false);
  const [cancelError, setCancelError] = useState<string | null>(null);

  // Reschedule State
  const [reschedulingApp, setReschedulingApp] = useState<OPDRegistration | null>(null);
  const [rescheduleDate, setRescheduleDate] = useState<string>('');
  const [rescheduleTime, setRescheduleTime] = useState<string>('11:00 AM');
  const [isRescheduling, setIsRescheduling] = useState<boolean>(false);
  const [rescheduleError, setRescheduleError] = useState<string | null>(null);

  const fetchAppointments = async () => {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const user = db.getCurrentUser();
      const data = await opdService.getAppointments(user?.id);
      setAppointments(data);
    } catch (err: any) {
      console.error('Failed to load appointments:', err);
      setErrorMessage(err?.message || 'Failed to retrieve appointments from backend database.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchAppointments();
  }, []);

  const filtered = appointments.filter(app => {
    if (activeTab === 'UPCOMING') return app.status === 'CONFIRMED' || app.status === 'VERIFIED';
    if (activeTab === 'COMPLETED') return app.status === 'COMPLETED';
    if (activeTab === 'CANCELLED') return app.status === 'CANCELLED';
    return true;
  });

  const handleConfirmCancel = async () => {
    if (!cancellingApp) return;
    setIsCancelling(true);
    setCancelError(null);
    try {
      await opdService.cancelAppointment(cancellingApp.id);
      db.logAudit('PATIENT', cancellingApp.patientId, 'CANCEL_APPOINTMENT', `Cancelled booking ${cancellingApp.referenceId}`);
      setCancellingApp(null);
      await fetchAppointments();
    } catch (err: any) {
      console.error('Cancel appointment failed:', err);
      setCancelError(err?.message || 'Failed to cancel appointment on server.');
    } finally {
      setIsCancelling(false);
    }
  };

  const handleConfirmReschedule = async () => {
    if (!reschedulingApp || !rescheduleDate) return;
    setIsRescheduling(true);
    setRescheduleError(null);
    try {
      await opdService.rescheduleAppointment(reschedulingApp.id, rescheduleDate, rescheduleTime);
      db.logAudit(
        'PATIENT',
        reschedulingApp.patientId,
        'RESCHEDULE_APPOINTMENT',
        `Rescheduled ${reschedulingApp.referenceId} to ${rescheduleDate} at ${rescheduleTime}`
      );
      setReschedulingApp(null);
      await fetchAppointments();
    } catch (err: any) {
      console.error('Reschedule appointment failed:', err);
      setRescheduleError(err?.message || 'Rescheduling failed. The selected slot may already be reserved.');
    } finally {
      setIsRescheduling(false);
    }
  };

  return (
    <div style={{ maxWidth: '1000px', margin: '0 auto', padding: '10px 0 40px' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px', marginBottom: '24px' }}>
        <div>
          <Badge variant="teal">MY CARE SCHEDULE</Badge>
          <h1 style={{ fontSize: '1.75rem', color: 'var(--text-heading)', margin: '4px 0 0' }}>
            My Appointments &amp; OPD Passes
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', margin: '4px 0 0' }}>
            Manage upcoming consultations, retrieve digital QR visit passes, reschedule, or review history.
          </p>
        </div>

        <Button variant="teal" onClick={onBookNew} leftIcon={<Calendar size={16} />}>
          Book New Consultation
        </Button>
      </div>

      {/* Error Banner */}
      {errorMessage && (
        <div style={{
          padding: '14px 18px',
          background: 'rgba(239, 68, 68, 0.1)',
          border: '1px solid var(--accent-red)',
          borderRadius: '10px',
          color: 'var(--accent-red)',
          marginBottom: '20px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '12px'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <AlertCircle size={20} />
            <span style={{ fontSize: '0.9rem' }}>{errorMessage}</span>
          </div>
          <Button variant="danger" size="sm" onClick={fetchAppointments}>Retry</Button>
        </div>
      )}

      {/* Tabs */}
      <div
        style={{
          display: 'flex',
          gap: '8px',
          borderBottom: '1px solid var(--border-light)',
          marginBottom: '24px',
          paddingBottom: '8px'
        }}
      >
        <button
          onClick={() => setActiveTab('UPCOMING')}
          className={`btn btn-sm ${activeTab === 'UPCOMING' ? 'btn-primary' : 'btn-ghost'}`}
        >
          Upcoming ({appointments.filter(a => a.status === 'CONFIRMED' || a.status === 'VERIFIED').length})
        </button>
        <button
          onClick={() => setActiveTab('COMPLETED')}
          className={`btn btn-sm ${activeTab === 'COMPLETED' ? 'btn-primary' : 'btn-ghost'}`}
        >
          Completed ({appointments.filter(a => a.status === 'COMPLETED').length})
        </button>
        <button
          onClick={() => setActiveTab('CANCELLED')}
          className={`btn btn-sm ${activeTab === 'CANCELLED' ? 'btn-primary' : 'btn-ghost'}`}
        >
          Cancelled ({appointments.filter(a => a.status === 'CANCELLED').length})
        </button>
      </div>

      {/* Loading or List */}
      {isLoading ? (
        <div style={{ textAlign: 'center', padding: '60px 20px', color: 'var(--text-muted)' }}>
          <Loader2 size={36} className="animate-spin" style={{ margin: '0 auto 12px', display: 'block', color: 'var(--primary-teal)' }} />
          <p style={{ margin: 0, fontSize: '0.95rem' }}>Synchronizing your appointment schedule with the server...</p>
        </div>
      ) : filtered.length === 0 ? (
        <EmptyState
          icon={<Calendar size={32} />}
          title={`No ${activeTab.toLowerCase()} appointments`}
          description={
            activeTab === 'UPCOMING'
              ? 'You do not have any active appointments scheduled. Search accredited hospitals or consult an OPD doctor.'
              : `There are no ${activeTab.toLowerCase()} appointments in your record.`
          }
          actionLabel={activeTab === 'UPCOMING' ? 'Book an Appointment' : 'Find Hospitals & Clinics'}
          onAction={activeTab === 'UPCOMING' ? onBookNew : onNavigateHospitals}
        />
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {filtered.map(app => (
            <Card key={app.id} padding="24px">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '12px', marginBottom: '14px' }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                    <span style={{ fontSize: '0.84rem', fontWeight: 700, color: 'var(--primary-teal)' }}>
                      REF: {app.referenceId}
                    </span>
                    <Badge
                      variant={
                        app.status === 'VERIFIED'
                          ? 'green'
                          : app.status === 'CONFIRMED'
                          ? 'teal'
                          : app.status === 'COMPLETED'
                          ? 'purple'
                          : 'red'
                      }
                      size="sm"
                    >
                      {app.status}
                    </Badge>
                  </div>
                  <h3 style={{ fontSize: '1.25rem', color: 'var(--text-heading)', margin: 0 }}>
                    {app.hospitalName}
                  </h3>
                  <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', margin: '2px 0 0' }}>
                    <Stethoscope size={14} style={{ display: 'inline', marginRight: '4px', verticalAlign: 'middle' }} />
                    {app.doctorName} • <strong>{app.department}</strong>
                  </p>
                </div>

                <div style={{ textAlign: 'right' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--text-heading)', fontWeight: 700, fontSize: '1.05rem' }}>
                    <Calendar size={16} color="var(--primary-teal)" />
                    {app.appointmentDate}
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--text-muted)', fontSize: '0.85rem', justifyContent: 'flex-end', marginTop: '2px' }}>
                    <Clock size={14} />
                    {app.appointmentTime}
                  </div>
                </div>
              </div>

              {/* Patient info row */}
              <div
                style={{
                  background: 'var(--bg-subtle)',
                  borderRadius: '10px',
                  padding: '10px 14px',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  fontSize: '0.84rem',
                  color: 'var(--text-secondary)',
                  marginBottom: '16px'
                }}
              >
                <div>Patient: <strong>{app.patientName}</strong> ({app.patientPhone})</div>
                <div>Consultation Fee: <strong style={{ color: '#16A34A' }}>₹{app.consultationFee}</strong> (Pay at Counter)</div>
              </div>

              {/* Action Buttons */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '10px' }}>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <a
                    href={`https://maps.google.com/?q=${encodeURIComponent(app.hospitalName)}`}
                    target="_blank"
                    rel="noreferrer"
                    style={{ textDecoration: 'none' }}
                  >
                    <Button variant="ghost" size="sm" rightIcon={<ExternalLink size={13} />}>
                      Get Directions
                    </Button>
                  </a>
                </div>

                <div style={{ display: 'flex', gap: '8px' }}>
                  {app.status !== 'CANCELLED' && (
                    <Button
                      variant="teal"
                      size="sm"
                      onClick={() => setSelectedQRPass(app)}
                      leftIcon={<QrCode size={15} />}
                    >
                      View QR Pass
                    </Button>
                  )}

                  {activeTab === 'UPCOMING' && (
                    <>
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={() => {
                          setReschedulingApp(app);
                          setRescheduleDate(app.appointmentDate);
                          setRescheduleTime(app.appointmentTime);
                        }}
                        leftIcon={<RotateCcw size={14} />}
                      >
                        Reschedule
                      </Button>

                      <Button
                        variant="danger"
                        size="sm"
                        onClick={() => setCancellingApp(app)}
                        leftIcon={<XCircle size={14} />}
                      >
                        Cancel
                      </Button>
                    </>
                  )}
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* QR PASS MODAL */}
      {selectedQRPass && (
        <div className="modal-overlay" onClick={() => setSelectedQRPass(null)}>
          <div className="modal-content" style={{ maxWidth: '640px' }} onClick={e => e.stopPropagation()}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <h3 style={{ margin: 0, color: 'var(--text-heading)' }}>Digital OPD Verification Pass</h3>
              <button
                onClick={() => setSelectedQRPass(null)}
                style={{ background: 'none', border: 'none', fontSize: '1.4rem', cursor: 'pointer', color: 'var(--text-muted)' }}
              >
                ×
              </button>
            </div>

            <HospitalPassQR
              opd={selectedQRPass}
            />
          </div>
        </div>
      )}

      {/* CANCEL CONFIRMATION DIALOG */}
      <ConfirmationDialog
        isOpen={Boolean(cancellingApp)}
        title="Cancel Appointment?"
        message={
          cancelError
            ? `Cancellation failed: ${cancelError}`
            : `Are you sure you want to cancel your OPD appointment at ${cancellingApp?.hospitalName} on ${cancellingApp?.appointmentDate}? This slot will be released back to the hospital queue.`
        }
        confirmLabel={isCancelling ? 'Cancelling...' : 'Yes, Cancel Booking'}
        confirmVariant="danger"
        onConfirm={handleConfirmCancel}
        onCancel={() => {
          setCancellingApp(null);
          setCancelError(null);
        }}
      />

      {/* RESCHEDULE MODAL */}
      {reschedulingApp && (
        <div className="modal-overlay" onClick={() => {
          setReschedulingApp(null);
          setRescheduleError(null);
        }}>
          <div className="modal-content" style={{ maxWidth: '480px', padding: '24px' }} onClick={e => e.stopPropagation()}>
            <h3 style={{ margin: '0 0 16px', color: 'var(--text-heading)' }}>
              Reschedule Appointment
            </h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.88rem', marginBottom: '16px' }}>
              Select a new date and time for {reschedulingApp.doctorName} at {reschedulingApp.hospitalName}.
            </p>

            {rescheduleError && (
              <div style={{
                padding: '10px 14px',
                background: 'rgba(239, 68, 68, 0.12)',
                border: '1px solid var(--accent-red)',
                borderRadius: '8px',
                color: 'var(--accent-red)',
                marginBottom: '14px',
                fontSize: '0.85rem'
              }}>
                {rescheduleError}
              </div>
            )}

            <div style={{ marginBottom: '14px' }}>
              <label className="form-label">New Appointment Date</label>
              <input
                type="date"
                required
                value={rescheduleDate}
                onChange={e => setRescheduleDate(e.target.value)}
                className="form-control"
                min={new Date().toISOString().split('T')[0]}
              />
            </div>

            <div style={{ marginBottom: '20px' }}>
              <label className="form-label">New Time Slot</label>
              <select
                value={rescheduleTime}
                onChange={e => setRescheduleTime(e.target.value)}
                className="form-control"
              >
                {['09:30 AM', '10:00 AM', '10:30 AM', '11:00 AM', '11:30 AM', '02:00 PM', '03:00 PM', '04:00 PM'].map(s => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
              <Button variant="secondary" onClick={() => {
                setReschedulingApp(null);
                setRescheduleError(null);
              }}>
                Cancel
              </Button>
              <Button variant="teal" onClick={handleConfirmReschedule} isLoading={isRescheduling}>
                Save Rescheduled Slot
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
