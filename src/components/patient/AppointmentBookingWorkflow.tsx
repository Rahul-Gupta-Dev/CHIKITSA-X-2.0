import React, { useState, useEffect } from 'react';
import type { Hospital, Doctor, OPDRegistration, DoctorAvailability } from '../../types';
import { db } from '../../db/database';
import { opdService, doctorService } from '../../services/apiServices';
import {
  Building2,
  Calendar,
  User,
  FileText,
  CheckCircle2,
  ArrowRight,
  ArrowLeft,
  ShieldCheck,
  AlertCircle,
  Loader2
} from 'lucide-react';
import { Button, Card, Badge, StepIndicator } from '../common/UIComponents';
import { HospitalPassQR } from './HospitalPassQR';

interface Props {
  initialHospital?: Hospital | null;
  initialDoctor?: Doctor | null;
  onBookingComplete: (opd: OPDRegistration) => void;
  onCancel: () => void;
}

export const AppointmentBookingWorkflow: React.FC<Props> = ({
  initialHospital,
  initialDoctor,
  onBookingComplete,
  onCancel
}) => {
  const hospitals = db.getHospitals();
  const profile = db.getPatientProfile();

  // Wizard Step (1 to 4)
  const [step, setStep] = useState<number>(1);

  // Form State (Preserved across steps)
  const [selectedHospitalId, setSelectedHospitalId] = useState<string>(
    initialHospital?.id || hospitals[0]?.id || ''
  );

  const selectedHospital = hospitals.find(h => h.id === selectedHospitalId) || hospitals[0];
  const hospitalDoctors = db.getDoctors(selectedHospital?.id);

  const [selectedDoctorId, setSelectedDoctorId] = useState<string>(
    initialDoctor?.id || hospitalDoctors[0]?.id || ''
  );
  const [department, setDepartment] = useState<string>(
    initialDoctor?.specialty || selectedHospital?.specialties[0] || 'Cardiology'
  );

  const [appointmentDate, setAppointmentDate] = useState<string>(() =>
    new Date(Date.now() + 86400000).toISOString().split('T')[0]
  );
  const [appointmentTime, setAppointmentTime] = useState<string>('11:00 AM');

  const [patientName, setPatientName] = useState<string>(profile.fullName);
  const [patientPhone, setPatientPhone] = useState<string>(profile.phone);
  const [patientAge, setPatientAge] = useState<number>(profile.age);
  const [patientGender, setPatientGender] = useState<string>(profile.gender);
  const [visitReason, setVisitReason] = useState<string>('Consultation for chest tightness & cardiac routine evaluation');

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [confirmedBooking, setConfirmedBooking] = useState<OPDRegistration | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [availability, setAvailability] = useState<DoctorAvailability | null>(null);
  const [isLoadingAvailability, setIsLoadingAvailability] = useState<boolean>(false);

  const selectedDoctor = hospitalDoctors.find(d => d.id === selectedDoctorId) || hospitalDoctors[0];

  const fetchDoctorAvailability = async () => {
    if (!selectedDoctor?.id || !appointmentDate) return;
    setIsLoadingAvailability(true);
    try {
      const avail = await doctorService.getDoctorAvailability(selectedDoctor.id, appointmentDate);
      setAvailability(avail);
      if (avail && avail.slots) {
        const cur = avail.slots.find(s => s.time === appointmentTime);
        if (!cur || !cur.isAvailable) {
          const firstOpen = avail.slots.find(s => s.isAvailable);
          if (firstOpen) {
            setAppointmentTime(firstOpen.time);
          }
        }
      }
    } catch (err) {
      console.warn('Could not load doctor availability:', err);
    } finally {
      setIsLoadingAvailability(false);
    }
  };

  useEffect(() => {
    fetchDoctorAvailability();
  }, [selectedDoctor?.id, appointmentDate]);

  const timeSlots = [
    '09:30 AM', '10:00 AM', '10:30 AM', '11:00 AM', '11:30 AM',
    '02:00 PM', '02:30 PM', '03:00 PM', '04:00 PM', '05:00 PM'
  ];

  // Step Validation
  const isSelectedSlotAvailable = availability?.slots
    ? (availability.slots.find(s => s.time === appointmentTime)?.isAvailable ?? true)
    : true;
  const canProceedStep1 = Boolean(selectedHospitalId && selectedDoctorId);
  const canProceedStep2 = Boolean(appointmentDate && appointmentTime && (!availability?.isDayBlocked) && isSelectedSlotAvailable);
  const canProceedStep3 = Boolean(patientName.trim() && patientPhone.trim() && visitReason.trim());

  const handleNext = () => {
    setError(null);
    if (step === 1 && !canProceedStep1) {
      setError('Please select both a hospital and a doctor.');
      return;
    }
    if (step === 2 && !canProceedStep2) {
      setError('Please pick an appointment date and an available slot.');
      return;
    }
    if (step === 3 && !canProceedStep3) {
      setError('Please confirm patient contact information and reason for visit.');
      return;
    }
    setStep(prev => Math.min(4, prev + 1));
  };

  const handleBack = () => {
    setError(null);
    setStep(prev => Math.max(1, prev - 1));
  };

  const handleConfirmBooking = async () => {
    setIsSubmitting(true);
    setError(null);
    try {
      const opd = await opdService.bookAppointment(
        selectedHospital.id,
        selectedHospital.name,
        department,
        selectedDoctor?.id || 'doc-1',
        selectedDoctor?.name || 'Dr. Rajesh Kulkarni',
        appointmentDate,
        appointmentTime
      );

      setConfirmedBooking(opd);
      onBookingComplete(opd);
    } catch (err: any) {
      setError(err?.message || 'Booking submission failed. Please try again.');
      fetchDoctorAvailability();
    } finally {
      setIsSubmitting(false);
    }
  };

  // SUCCESS CONFIRMATION SCREEN
  if (confirmedBooking) {
    return (
      <div style={{ maxWidth: '820px', margin: '0 auto', padding: '20px 0' }}>
        <Card padding="32px" style={{ textAlign: 'center', marginBottom: '24px' }}>
          <div
            style={{
              width: '64px',
              height: '64px',
              borderRadius: '50%',
              background: 'rgba(22, 163, 74, 0.12)',
              color: '#16A34A',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 16px'
            }}
          >
            <CheckCircle2 size={36} />
          </div>

          <Badge variant="green" style={{ marginBottom: '8px' }}>
            APPOINTMENT CONFIRMED
          </Badge>

          <h2 style={{ fontSize: '1.8rem', color: 'var(--text-heading)', margin: '0 0 6px' }}>
            OPD Registration Successful!
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem', margin: '0 auto 20px', maxWidth: '520px' }}>
            Your booking reference has been encrypted and issued. Present the digital QR token pass below at the hospital reception desk for instant check-in.
          </p>

          <div
            style={{
              display: 'inline-block',
              background: 'var(--bg-subtle)',
              border: '2px dashed var(--primary-teal)',
              borderRadius: '16px',
              padding: '12px 28px',
              marginBottom: '24px'
            }}
          >
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600, display: 'block' }}>
              UNIQUE APPOINTMENT REFERENCE ID
            </span>
            <span style={{ fontSize: '1.6rem', fontWeight: 800, color: 'var(--primary-teal)', letterSpacing: '0.04em' }}>
              {confirmedBooking.referenceId}
            </span>
          </div>
        </Card>

        {/* Live Digital QR Visit Pass Component */}
        <HospitalPassQR
          opd={confirmedBooking}
        />

        <div style={{ textAlign: 'center', marginTop: '24px' }}>
          <Button variant="secondary" onClick={onCancel}>
            Return to Dashboard
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: '820px', margin: '0 auto', padding: '10px 0 40px' }}>
      {/* Title & Wizard Step Indicator */}
      <div style={{ marginBottom: '16px' }}>
        <h1 style={{ fontSize: '1.75rem', color: 'var(--text-heading)', margin: '0 0 4px' }}>
          Book OPD Appointment
        </h1>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', margin: 0 }}>
          Follow the 4 simple steps to book verified hospital consultation
        </p>

        <StepIndicator
          steps={['Hospital & Doctor', 'Date & Slot', 'Patient Details', 'Review & Confirm']}
          currentStep={step}
          onStepClick={targetStep => {
            if (targetStep < step) setStep(targetStep);
          }}
        />
      </div>

      {error && (
        <div
          style={{
            padding: '12px 16px',
            background: 'rgba(220, 38, 38, 0.1)',
            border: '1px solid rgba(220, 38, 38, 0.3)',
            borderRadius: '12px',
            color: '#DC2626',
            fontSize: '0.88rem',
            marginBottom: '20px',
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}
        >
          <AlertCircle size={18} />
          <span>{error}</span>
        </div>
      )}

      {/* STEP 1: SELECT HOSPITAL & DOCTOR */}
      {step === 1 && (
        <Card padding="28px">
          <h3 style={{ fontSize: '1.25rem', color: 'var(--text-heading)', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Building2 size={20} color="var(--primary-teal)" />
            Step 1: Select Hospital &amp; Doctor
          </h3>

          {/* Hospital Selector */}
          <div style={{ marginBottom: '20px' }}>
            <label className="form-label">Healthcare Facility</label>
            <select
              value={selectedHospitalId}
              onChange={e => {
                const newId = e.target.value;
                setSelectedHospitalId(newId);
                const docs = db.getDoctors().filter(d => d.hospitalId === newId);
                if (docs.length > 0) {
                  setSelectedDoctorId(docs[0].id);
                  setDepartment(docs[0].specialty);
                }
              }}
              className="form-control"
            >
              {hospitals.map(h => (
                <option key={h.id} value={h.id}>
                  {h.name} — {h.city} ({h.distanceKm} km away) • Care Score: {h.chikitsaxCareScore}/100
                </option>
              ))}
            </select>
          </div>

          {/* Department Selector */}
          <div style={{ marginBottom: '20px' }}>
            <label className="form-label">Specialty Department</label>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
              {selectedHospital.specialties.map(spec => (
                <button
                  key={spec}
                  type="button"
                  onClick={() => setDepartment(spec)}
                  style={{
                    padding: '8px 14px',
                    borderRadius: '10px',
                    border: department === spec ? '2px solid var(--primary-teal)' : '1px solid var(--border-light)',
                    background: department === spec ? 'rgba(2, 132, 199, 0.12)' : 'var(--bg-subtle)',
                    color: department === spec ? 'var(--primary-teal)' : 'var(--text-secondary)',
                    fontWeight: 600,
                    fontSize: '0.85rem',
                    cursor: 'pointer'
                  }}
                >
                  {spec}
                </button>
              ))}
            </div>
          </div>

          {/* Doctor List */}
          <div>
            <label className="form-label">Select Specialist Consultant</label>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {hospitalDoctors.map(doc => {
                const isSelected = doc.id === selectedDoctorId;
                return (
                  <div
                    key={doc.id}
                    onClick={() => {
                      setSelectedDoctorId(doc.id);
                      setDepartment(doc.specialty);
                    }}
                    style={{
                      padding: '14px 18px',
                      borderRadius: '14px',
                      border: isSelected ? '2px solid var(--primary-teal)' : '1px solid var(--border-light)',
                      background: isSelected ? 'rgba(2, 132, 199, 0.08)' : 'var(--bg-subtle)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      cursor: 'pointer',
                      transition: 'all 0.15s ease'
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                      <img
                        src={doc.avatar}
                        alt={doc.name}
                        style={{ width: '44px', height: '44px', borderRadius: '50%', objectFit: 'cover' }}
                      />
                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <span style={{ fontWeight: 700, fontSize: '0.96rem', color: 'var(--text-heading)' }}>
                            {doc.name}
                          </span>
                          <span className="badge badge-teal" style={{ fontSize: '0.68rem' }}>{doc.specialty}</span>
                        </div>
                        <p style={{ margin: '2px 0 0', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                          {doc.qualification} • {doc.experienceYears}+ years exp • ★ {doc.rating}/5.0
                        </p>
                      </div>
                    </div>

                    <div style={{ textAlign: 'right' }}>
                      <div style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--primary-teal)' }}>
                        ₹{doc.consultationFee}
                      </div>
                      <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Consultation Fee</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </Card>
      )}

      {/* STEP 2: CHOOSE DATE & TIME SLOT */}
      {step === 2 && (
        <Card padding="28px">
          <h3 style={{ fontSize: '1.25rem', color: 'var(--text-heading)', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Calendar size={20} color="var(--primary-teal)" />
            Step 2: Choose Date &amp; Available Time Slot
          </h3>

          <div style={{ marginBottom: '20px' }}>
            <label className="form-label">Consultation Date</label>
            <input
              type="date"
              required
              value={appointmentDate}
              onChange={e => setAppointmentDate(e.target.value)}
              className="form-control"
              min={new Date().toISOString().split('T')[0]}
            />
          </div>

          {availability?.isDayBlocked && (
            <div style={{ padding: '12px 16px', borderRadius: '10px', background: '#FEF2F2', border: '1px solid #FCA5A5', color: '#991B1B', marginBottom: '16px', fontSize: '0.88rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <AlertCircle size={18} color="#DC2626" />
              <span>Doctor {selectedDoctor?.name} has marked this day ({availability.day || 'Selected day'}) as blocked/unavailable. Please choose another date.</span>
            </div>
          )}

          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <label className="form-label" style={{ margin: 0 }}>
                Available OPD Slots for {selectedDoctor?.name}
              </label>
              {isLoadingAvailability && (
                <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <Loader2 size={12} className="animate-spin" /> Checking slot status...
                </span>
              )}
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(130px, 1fr))', gap: '10px' }}>
              {(availability?.slots || timeSlots.map(s => ({ time: s, isAvailable: true, isBlocked: false, isBooked: false }))).map(slotObj => {
                const isSelected = slotObj.time === appointmentTime;
                const isAvail = slotObj.isAvailable && !availability?.isDayBlocked;
                return (
                  <button
                    key={slotObj.time}
                    type="button"
                    disabled={!isAvail}
                    onClick={() => {
                      if (isAvail) setAppointmentTime(slotObj.time);
                    }}
                    style={{
                      padding: '10px 8px',
                      borderRadius: '10px',
                      border: isSelected ? '2px solid var(--primary-teal)' : '1px solid var(--border-light)',
                      background: !isAvail
                        ? '#F3F4F6'
                        : isSelected
                        ? 'var(--primary-teal)'
                        : 'var(--bg-subtle)',
                      color: !isAvail
                        ? '#9CA3AF'
                        : isSelected
                        ? '#FFFFFF'
                        : 'var(--text-main)',
                      fontWeight: 600,
                      fontSize: '0.84rem',
                      cursor: isAvail ? 'pointer' : 'not-allowed',
                      textAlign: 'center',
                      opacity: isAvail ? 1 : 0.65,
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'center',
                      gap: '2px'
                    }}
                  >
                    <span>{slotObj.time}</span>
                    {!isAvail && (
                      <span style={{ fontSize: '0.68rem', fontWeight: 700, color: slotObj.isBlocked || availability?.isDayBlocked ? '#DC2626' : '#D97706' }}>
                        {slotObj.isBlocked || availability?.isDayBlocked ? 'BLOCKED' : 'BOOKED'}
                      </span>
                    )}
                  </button>
                );
              })}
            </div>
          </div>
        </Card>
      )}

      {/* STEP 3: PATIENT INFORMATION & VISIT REASON */}
      {step === 3 && (
        <Card padding="28px">
          <h3 style={{ fontSize: '1.25rem', color: 'var(--text-heading)', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <User size={20} color="var(--primary-teal)" />
            Step 3: Confirm Patient Details &amp; Reason for Visit
          </h3>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px', marginBottom: '14px' }}>
            <div>
              <label className="form-label">Patient Full Name</label>
              <input
                type="text"
                required
                value={patientName}
                onChange={e => setPatientName(e.target.value)}
                className="form-control"
              />
            </div>
            <div>
              <label className="form-label">Mobile Number</label>
              <input
                type="tel"
                required
                value={patientPhone}
                onChange={e => setPatientPhone(e.target.value)}
                className="form-control"
              />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px', marginBottom: '14px' }}>
            <div>
              <label className="form-label">Age</label>
              <input
                type="number"
                min={1}
                max={120}
                value={patientAge}
                onChange={e => setPatientAge(Number(e.target.value))}
                className="form-control"
              />
            </div>
            <div>
              <label className="form-label">Gender</label>
              <select
                value={patientGender}
                onChange={e => setPatientGender(e.target.value)}
                className="form-control"
              >
                <option value="Male">Male</option>
                <option value="Female">Female</option>
                <option value="Other">Other</option>
              </select>
            </div>
          </div>

          <div>
            <label className="form-label">Chief Complaint / Reason for Visit</label>
            <textarea
              required
              rows={3}
              value={visitReason}
              onChange={e => setVisitReason(e.target.value)}
              placeholder="Describe your current symptoms or reason for consulting the doctor..."
              className="form-control"
              style={{ resize: 'vertical' }}
            />
          </div>
        </Card>
      )}

      {/* STEP 4: REVIEW DETAILS & CONFIRM BOOKING */}
      {step === 4 && (
        <Card padding="28px">
          <h3 style={{ fontSize: '1.25rem', color: 'var(--text-heading)', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <FileText size={20} color="var(--primary-teal)" />
            Step 4: Review Appointment Summary &amp; Confirm
          </h3>

          <div
            style={{
              background: 'var(--bg-subtle)',
              border: '1px solid var(--border-light)',
              borderRadius: '14px',
              padding: '20px',
              display: 'flex',
              flexDirection: 'column',
              gap: '12px',
              marginBottom: '20px'
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border-light)', paddingBottom: '8px' }}>
              <span style={{ color: 'var(--text-muted)' }}>Hospital Facility:</span>
              <strong style={{ color: 'var(--text-heading)' }}>{selectedHospital.name} ({selectedHospital.city})</strong>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border-light)', paddingBottom: '8px' }}>
              <span style={{ color: 'var(--text-muted)' }}>Consultant:</span>
              <strong style={{ color: 'var(--text-heading)' }}>{selectedDoctor?.name} ({department})</strong>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border-light)', paddingBottom: '8px' }}>
              <span style={{ color: 'var(--text-muted)' }}>Scheduled Date &amp; Slot:</span>
              <strong style={{ color: 'var(--primary-teal)' }}>{appointmentDate} at {appointmentTime}</strong>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border-light)', paddingBottom: '8px' }}>
              <span style={{ color: 'var(--text-muted)' }}>Patient Name:</span>
              <strong style={{ color: 'var(--text-heading)' }}>{patientName} ({patientAge} yrs, {patientGender})</strong>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border-light)', paddingBottom: '8px' }}>
              <span style={{ color: 'var(--text-muted)' }}>Contact:</span>
              <strong style={{ color: 'var(--text-heading)' }}>{patientPhone}</strong>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border-light)', paddingBottom: '8px' }}>
              <span style={{ color: 'var(--text-muted)' }}>Reason:</span>
              <span style={{ color: 'var(--text-main)', maxWidth: '60%' }}>{visitReason}</span>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', paddingTop: '4px' }}>
              <span style={{ color: 'var(--text-muted)' }}>Consultation Fee:</span>
              <strong style={{ fontSize: '1.2rem', color: '#16A34A' }}>₹{selectedDoctor?.consultationFee || 800}</strong>
            </div>
          </div>

          <div
            style={{
              padding: '12px 16px',
              borderRadius: '10px',
              background: 'rgba(2, 132, 199, 0.08)',
              border: '1px solid rgba(2, 132, 199, 0.2)',
              fontSize: '0.84rem',
              color: 'var(--text-secondary)',
              marginBottom: '20px'
            }}
          >
            <ShieldCheck size={16} color="var(--primary-teal)" style={{ display: 'inline', marginRight: '6px' }} />
            Zero advance payment required online. Pay consultation fee directly at hospital reception desk or via cashless PM-JAY.
          </div>
        </Card>
      )}

      {/* Navigation Buttons Row */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '24px' }}>
        <div>
          {step > 1 ? (
            <Button variant="secondary" onClick={handleBack} leftIcon={<ArrowLeft size={16} />}>
              Back
            </Button>
          ) : (
            <Button variant="ghost" onClick={onCancel}>
              Cancel
            </Button>
          )}
        </div>

        <div>
          {step < 4 ? (
            <Button variant="teal" onClick={handleNext} rightIcon={<ArrowRight size={16} />}>
              Continue to Step {step + 1}
            </Button>
          ) : (
            <Button
              variant="teal"
              isLoading={isSubmitting}
              onClick={handleConfirmBooking}
              leftIcon={<CheckCircle2 size={18} />}
            >
              Confirm Appointment Booking
            </Button>
          )}
        </div>
      </div>
    </div>
  );
};
