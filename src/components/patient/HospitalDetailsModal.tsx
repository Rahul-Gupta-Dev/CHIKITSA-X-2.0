import React, { useState, useEffect } from 'react';
import type { Hospital, Doctor } from '../../types';
import { doctorService, hospitalService } from '../../services/apiServices';
import { db } from '../../db/database';
import {
  X,
  MapPin,
  Phone,
  AlertTriangle,
  Award,
  Clock,
  ShieldCheck,
  CheckCircle2,
  ExternalLink,
  ChevronRight,
  Star,
  MessageSquare
} from 'lucide-react';
import { Button } from '../common/UIComponents';

interface Props {
  hospital: Hospital | null;
  isOpen: boolean;
  onClose: () => void;
  onBookWithDoctor: (hospital: Hospital, doctor?: Doctor) => void;
  onOpenCompare?: (hospital: Hospital) => void;
}

export const HospitalDetailsModal: React.FC<Props> = ({
  hospital,
  isOpen,
  onClose,
  onBookWithDoctor,
  onOpenCompare
}) => {
  const [doctors, setDoctors] = useState<Doctor[]>([]);
  const [selectedSpecialty, setSelectedSpecialty] = useState<string>('ALL');
  const [activeTab, setActiveTab] = useState<'OVERVIEW' | 'DOCTORS' | 'FACILITIES' | 'REVIEWS'>('OVERVIEW');
  const [reviews, setReviews] = useState<any[]>([]);
  const [ratingInput, setRatingInput] = useState<number>(5);
  const [reviewTextInput, setReviewTextInput] = useState<string>('');
  const [isSubmittingReview, setIsSubmittingReview] = useState<boolean>(false);
  const [reviewError, setReviewError] = useState<string | null>(null);
  const [reviewSuccess, setReviewSuccess] = useState<string | null>(null);

  const currentUser = db.getCurrentUser();

  const fetchReviews = async (hospId: string) => {
    try {
      const revs = await hospitalService.getHospitalReviews(hospId);
      setReviews(revs);
    } catch {
      // ignore
    }
  };

  useEffect(() => {
    if (hospital) {
      doctorService.getDoctors(hospital.id).then(docs => {
        setDoctors(docs);
      });
      fetchReviews(hospital.id);
    }
  }, [hospital]);

  const handleSubmitReview = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!hospital) return;
    if (!reviewTextInput.trim()) {
      setReviewError('Please enter your review text.');
      return;
    }
    setIsSubmittingReview(true);
    setReviewError(null);
    setReviewSuccess(null);
    try {
      await hospitalService.submitHospitalReview(hospital.id, ratingInput, reviewTextInput.trim());
      setReviewSuccess('Thank you! Your verified patient review has been submitted to the server.');
      setReviewTextInput('');
      await fetchReviews(hospital.id);
    } catch (err: any) {
      setReviewError(err?.message || 'Failed to submit hospital review. Please check your login session.');
    } finally {
      setIsSubmittingReview(false);
    }
  };

  if (!isOpen || !hospital) return null;

  const filteredDoctors = selectedSpecialty === 'ALL'
    ? doctors
    : doctors.filter(d => d.specialty.toLowerCase().includes(selectedSpecialty.toLowerCase()));

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        className="modal-content"
        style={{ maxWidth: '820px', padding: '0', overflow: 'hidden' }}
        onClick={e => e.stopPropagation()}
      >
        {/* Hospital Header Banner */}
        <div style={{ position: 'relative', height: '180px', overflow: 'hidden' }}>
          <img
            src={hospital.image}
            alt={hospital.name}
            style={{ width: '100%', height: '100%', objectFit: 'cover' }}
          />
          <div
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              background: 'linear-gradient(180deg, rgba(15, 23, 42, 0.2) 0%, rgba(15, 23, 42, 0.88) 100%)'
            }}
          />

          <button
            onClick={onClose}
            style={{
              position: 'absolute',
              top: '16px',
              right: '16px',
              background: 'rgba(0, 0, 0, 0.55)',
              border: 'none',
              borderRadius: '50%',
              width: '36px',
              height: '36px',
              color: '#FFFFFF',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer',
              zIndex: 10
            }}
          >
            <X size={20} />
          </button>

          <div style={{ position: 'absolute', bottom: '16px', left: '20px', right: '20px', color: '#FFFFFF' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
              <span className="badge badge-teal" style={{ background: 'rgba(2, 132, 199, 0.85)', color: '#FFF' }}>
                <ShieldCheck size={12} /> VERIFIED FACILITY
              </span>
              <span className="care-score-pill" style={{ padding: '2px 10px', fontSize: '0.78rem' }}>
                Care Score: {hospital.chikitsaxCareScore}/100
              </span>
            </div>
            <h2 style={{ fontSize: '1.6rem', margin: 0, color: '#FFFFFF' }}>{hospital.name}</h2>
            <p style={{ margin: '2px 0 0', opacity: 0.9, fontSize: '0.85rem' }}>
              <MapPin size={13} style={{ display: 'inline', marginRight: '4px' }} />
              {hospital.address}, {hospital.city} • {hospital.distanceKm} km away
            </p>
          </div>
        </div>

        {/* Tab Navigation */}
        <div
          style={{
            display: 'flex',
            borderBottom: '1px solid var(--border-light)',
            background: 'var(--bg-subtle)',
            padding: '0 20px'
          }}
        >
          <button
            onClick={() => setActiveTab('OVERVIEW')}
            style={{
              padding: '12px 16px',
              background: 'none',
              border: 'none',
              borderBottom: activeTab === 'OVERVIEW' ? '3px solid var(--primary-teal)' : '3px solid transparent',
              color: activeTab === 'OVERVIEW' ? 'var(--primary-teal)' : 'var(--text-secondary)',
              fontWeight: 600,
              fontSize: '0.9rem',
              cursor: 'pointer'
            }}
          >
            Overview &amp; Facilities
          </button>
          <button
            onClick={() => setActiveTab('DOCTORS')}
            style={{
              padding: '12px 16px',
              background: 'none',
              border: 'none',
              borderBottom: activeTab === 'DOCTORS' ? '3px solid var(--primary-teal)' : '3px solid transparent',
              color: activeTab === 'DOCTORS' ? 'var(--primary-teal)' : 'var(--text-secondary)',
              fontWeight: 600,
              fontSize: '0.9rem',
              cursor: 'pointer'
            }}
          >
            Doctors Directory ({doctors.length})
          </button>
          <button
            onClick={() => setActiveTab('FACILITIES')}
            style={{
              padding: '12px 16px',
              background: 'none',
              border: 'none',
              borderBottom: activeTab === 'FACILITIES' ? '3px solid var(--primary-teal)' : '3px solid transparent',
              color: activeTab === 'FACILITIES' ? 'var(--primary-teal)' : 'var(--text-secondary)',
              fontWeight: 600,
              fontSize: '0.9rem',
              cursor: 'pointer'
            }}
          >
            Financial Schemes &amp; Aid
          </button>
          <button
            onClick={() => setActiveTab('REVIEWS')}
            style={{
              padding: '12px 16px',
              background: 'none',
              border: 'none',
              borderBottom: activeTab === 'REVIEWS' ? '3px solid var(--primary-teal)' : '3px solid transparent',
              color: activeTab === 'REVIEWS' ? 'var(--primary-teal)' : 'var(--text-secondary)',
              fontWeight: 600,
              fontSize: '0.9rem',
              cursor: 'pointer'
            }}
          >
            Patient Reviews ({reviews.length})
          </button>
        </div>

        {/* Content Body */}
        <div style={{ padding: '24px', maxHeight: 'calc(80vh - 240px)', overflowY: 'auto' }}>
          {/* TAB 1: OVERVIEW */}
          {activeTab === 'OVERVIEW' && (
            <div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '14px', marginBottom: '20px' }}>
                <div style={{ background: 'var(--bg-subtle)', padding: '14px', borderRadius: '12px', border: '1px solid var(--border-light)' }}>
                  <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', fontWeight: 600 }}>ESTIMATED COST RANGE</div>
                  <div style={{ fontSize: '1.15rem', fontWeight: 700, color: '#16A34A', marginTop: '2px' }}>
                    ₹{hospital.estimatedCostRange.min.toLocaleString()} – ₹{hospital.estimatedCostRange.max.toLocaleString()}
                  </div>
                </div>

                <div style={{ background: 'var(--bg-subtle)', padding: '14px', borderRadius: '12px', border: '1px solid var(--border-light)' }}>
                  <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', fontWeight: 600 }}>EMERGENCY TRAUMA ICU</div>
                  <div style={{ fontSize: '1.05rem', fontWeight: 700, color: hospital.emergencyAvailable ? '#16A34A' : 'var(--text-secondary)', marginTop: '2px' }}>
                    {hospital.emergencyAvailable ? `24/7 (${hospital.emergencyBedsFree} Beds Free)` : 'Routine OPD Only'}
                  </div>
                </div>

                <div style={{ background: 'var(--bg-subtle)', padding: '14px', borderRadius: '12px', border: '1px solid var(--border-light)' }}>
                  <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', fontWeight: 600 }}>PATIENT RATING</div>
                  <div style={{ fontSize: '1.15rem', fontWeight: 700, color: '#D97706', marginTop: '2px' }}>
                    ★ {hospital.rating} / 5.0 ({hospital.reviewCount} reviews)
                  </div>
                </div>
              </div>

              {/* Departments & Specialties */}
              <div style={{ marginBottom: '20px' }}>
                <h4 style={{ fontSize: '0.95rem', color: 'var(--text-heading)', marginBottom: '8px' }}>
                  Departments &amp; Clinical Specialties
                </h4>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                  {hospital.specialties.map(spec => (
                    <span key={spec} className="badge badge-purple" style={{ padding: '6px 12px', fontSize: '0.8rem' }}>
                      {spec}
                    </span>
                  ))}
                </div>
              </div>

              {/* Accreditations */}
              <div style={{ marginBottom: '20px' }}>
                <h4 style={{ fontSize: '0.95rem', color: 'var(--text-heading)', marginBottom: '8px' }}>
                  Accreditations &amp; Quality Standards
                </h4>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                  {hospital.accreditation.map(acc => (
                    <span key={acc} className="badge badge-teal" style={{ padding: '4px 10px' }}>
                      <Award size={12} /> {acc}
                    </span>
                  ))}
                </div>
              </div>

              {/* Contact and Directions */}
              <div style={{ background: 'var(--bg-subtle)', padding: '16px', borderRadius: '12px', border: '1px solid var(--border-light)' }}>
                <h4 style={{ fontSize: '0.95rem', color: 'var(--text-heading)', margin: '0 0 8px' }}>
                  Contact Information &amp; Hotline
                </h4>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', fontSize: '0.88rem', color: 'var(--text-secondary)' }}>
                  <div><Phone size={14} style={{ display: 'inline', marginRight: '6px' }} /> Reception Desk: <strong>{hospital.phone}</strong></div>
                  <div><AlertTriangle size={14} style={{ display: 'inline', marginRight: '6px', color: '#DC2626' }} /> 24/7 Emergency Helpline: <strong>{hospital.emergencyPhone}</strong></div>
                  <div><MapPin size={14} style={{ display: 'inline', marginRight: '6px' }} /> Full Address: <strong>{hospital.address}, {hospital.city}</strong></div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: DOCTORS DIRECTORY */}
          {activeTab === 'DOCTORS' && (
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '10px' }}>
                <h4 style={{ margin: 0, fontSize: '1rem', color: 'var(--text-heading)' }}>
                  Available Consultants &amp; Specialists
                </h4>
                <div style={{ display: 'flex', gap: '6px' }}>
                  <button
                    onClick={() => setSelectedSpecialty('ALL')}
                    style={{
                      background: selectedSpecialty === 'ALL' ? 'var(--primary-teal)' : 'var(--bg-subtle)',
                      color: selectedSpecialty === 'ALL' ? '#FFF' : 'var(--text-main)',
                      border: '1px solid var(--border-light)',
                      borderRadius: '8px',
                      padding: '4px 10px',
                      fontSize: '0.78rem',
                      cursor: 'pointer'
                    }}
                  >
                    All Specialists
                  </button>
                  {hospital.specialties.slice(0, 3).map(s => (
                    <button
                      key={s}
                      onClick={() => setSelectedSpecialty(s)}
                      style={{
                        background: selectedSpecialty === s ? 'var(--primary-teal)' : 'var(--bg-subtle)',
                        color: selectedSpecialty === s ? '#FFF' : 'var(--text-main)',
                        border: '1px solid var(--border-light)',
                        borderRadius: '8px',
                        padding: '4px 10px',
                        fontSize: '0.78rem',
                        cursor: 'pointer'
                      }}
                    >
                      {s}
                    </button>
                  ))}
                </div>
              </div>

              {filteredDoctors.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '24px', color: 'var(--text-muted)' }}>
                  No doctors listed for this specific filter.
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  {filteredDoctors.map(doc => (
                    <div
                      key={doc.id}
                      style={{
                        background: 'var(--bg-subtle)',
                        border: '1px solid var(--border-light)',
                        borderRadius: '14px',
                        padding: '16px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        flexWrap: 'wrap',
                        gap: '12px'
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                        <img
                          src={doc.avatar}
                          alt={doc.name}
                          style={{ width: '48px', height: '48px', borderRadius: '50%', objectFit: 'cover' }}
                        />
                        <div>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                            <h4 style={{ margin: 0, fontSize: '1.02rem', color: 'var(--text-heading)' }}>{doc.name}</h4>
                            <span className="badge badge-teal" style={{ fontSize: '0.7rem' }}>{doc.specialty}</span>
                          </div>
                          <p style={{ margin: '2px 0 0', fontSize: '0.82rem', color: 'var(--text-muted)' }}>
                            {doc.qualification} • {doc.experienceYears}+ years exp • ★ {doc.rating}/5.0
                          </p>
                          <p style={{ margin: '2px 0 0', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                            <Clock size={12} style={{ display: 'inline', marginRight: '4px' }} />
                            Available: {doc.availableDays.join(', ')} ({doc.availableSlots.length} slots today)
                          </p>
                        </div>
                      </div>

                      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                        <div style={{ textAlign: 'right' }}>
                          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Consultation Fee</span>
                          <div style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--primary-teal)' }}>
                            ₹{doc.consultationFee}
                          </div>
                        </div>
                        <Button
                          variant="teal"
                          size="sm"
                          onClick={() => {
                            onBookWithDoctor(hospital, doc);
                            onClose();
                          }}
                          rightIcon={<ChevronRight size={14} />}
                        >
                          Select Doctor
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* TAB 3: FINANCIAL SCHEMES */}
          {activeTab === 'FACILITIES' && (
            <div>
              <div style={{ marginBottom: '16px' }}>
                <h4 style={{ fontSize: '0.98rem', color: 'var(--text-heading)', marginBottom: '8px' }}>
                  Accepted Government Schemes
                </h4>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {hospital.acceptedGovSchemes.map(sch => (
                    <div
                      key={sch}
                      style={{
                        padding: '12px 16px',
                        background: 'var(--bg-subtle)',
                        borderRadius: '10px',
                        border: '1px solid var(--border-light)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between'
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <CheckCircle2 size={16} color="#16A34A" />
                        <span style={{ fontWeight: 600, fontSize: '0.9rem' }}>{sch}</span>
                      </div>
                      <span className="badge badge-green" style={{ fontSize: '0.72rem' }}>100% Cashless Empaneled</span>
                    </div>
                  ))}
                </div>
              </div>

              <div style={{ marginBottom: '16px' }}>
                <h4 style={{ fontSize: '0.98rem', color: 'var(--text-heading)', marginBottom: '8px' }}>
                  Accepted Insurance Providers
                </h4>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                  {hospital.acceptedInsuranceProviders.map(ins => (
                    <span key={ins} className="badge badge-teal" style={{ padding: '6px 12px' }}>
                      {ins}
                    </span>
                  ))}
                </div>
              </div>

              <div>
                <h4 style={{ fontSize: '0.98rem', color: 'var(--text-heading)', marginBottom: '8px' }}>
                  Philanthropic NGO Partnerships
                </h4>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                  {hospital.ngoPartnerships.map(ngo => (
                    <span key={ngo} className="badge badge-purple" style={{ padding: '6px 12px' }}>
                      {ngo}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* TAB 4: REVIEWS */}
          {activeTab === 'REVIEWS' && (
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', flexWrap: 'wrap', gap: '10px' }}>
                <div>
                  <h4 style={{ fontSize: '1.05rem', color: 'var(--text-heading)', margin: '0 0 4px' }}>
                    Patient Reviews &amp; Ratings
                  </h4>
                  <p style={{ color: 'var(--text-muted)', fontSize: '0.82rem', margin: 0 }}>
                    Real verified feedback from registered patients
                  </p>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', background: 'rgba(217, 119, 6, 0.1)', padding: '6px 14px', borderRadius: '10px', border: '1px solid rgba(217, 119, 6, 0.3)' }}>
                  <Star size={18} color="#D97706" fill="#D97706" />
                  <strong style={{ color: '#D97706', fontSize: '1.1rem' }}>{hospital.rating} / 5.0</strong>
                  <span style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>({reviews.length} reviews)</span>
                </div>
              </div>

              {/* Write Review Form for Authenticated Patients */}
              {currentUser?.role === 'PATIENT' ? (
                <form onSubmit={handleSubmitReview} style={{ background: 'var(--bg-subtle)', padding: '16px', borderRadius: '12px', border: '1px solid var(--border-light)', marginBottom: '20px' }}>
                  <h5 style={{ margin: '0 0 10px', fontSize: '0.92rem', color: 'var(--text-heading)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <MessageSquare size={16} /> Write a Verified Patient Review
                  </h5>

                  {reviewError && (
                    <div style={{ marginBottom: '10px', padding: '8px 12px', borderRadius: '6px', background: '#FEF2F2', border: '1px solid #FCA5A5', color: '#991B1B', fontSize: '0.82rem' }}>
                      {reviewError}
                    </div>
                  )}
                  {reviewSuccess && (
                    <div style={{ marginBottom: '10px', padding: '8px 12px', borderRadius: '6px', background: '#ECFDF5', border: '1px solid #A7F3D0', color: '#065F46', fontSize: '0.82rem' }}>
                      {reviewSuccess}
                    </div>
                  )}

                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '10px' }}>
                    <label style={{ fontSize: '0.84rem', color: 'var(--text-secondary)', fontWeight: 600 }}>Your Rating:</label>
                    <div style={{ display: 'flex', gap: '6px' }}>
                      {[1, 2, 3, 4, 5].map((star) => (
                        <button
                          key={star}
                          type="button"
                          onClick={() => setRatingInput(star)}
                          style={{
                            background: 'none',
                            border: 'none',
                            cursor: 'pointer',
                            padding: '2px'
                          }}
                        >
                          <Star
                            size={20}
                            color="#D97706"
                            fill={star <= ratingInput ? '#D97706' : 'none'}
                          />
                        </button>
                      ))}
                    </div>
                    <span style={{ fontSize: '0.85rem', fontWeight: 700, color: '#D97706' }}>{ratingInput} Stars</span>
                  </div>

                  <div style={{ marginBottom: '12px' }}>
                    <textarea
                      rows={2}
                      value={reviewTextInput}
                      onChange={e => setReviewTextInput(e.target.value)}
                      placeholder="Share your experience regarding hospital cleanliness, doctor responsiveness, waiting times..."
                      className="form-control"
                      style={{ width: '100%', fontSize: '0.85rem' }}
                    />
                  </div>

                  <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                    <Button variant="teal" size="sm" disabled={isSubmittingReview}>
                      {isSubmittingReview ? 'Submitting...' : 'Submit Verified Review'}
                    </Button>
                  </div>
                </form>
              ) : (
                <div style={{ padding: '12px 16px', background: 'var(--bg-subtle)', borderRadius: '10px', border: '1px solid var(--border-light)', marginBottom: '20px', fontSize: '0.84rem', color: 'var(--text-secondary)' }}>
                  ℹ️ Log in as a registered patient to submit a verified hospital review.
                </div>
              )}

              {/* Reviews List */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {reviews.length === 0 ? (
                  <div style={{ textAlign: 'center', padding: '30px', color: 'var(--text-muted)', fontSize: '0.88rem' }}>
                    No patient reviews recorded yet for {hospital.name}. Be the first verified patient to share your experience!
                  </div>
                ) : (
                  reviews.map((rev) => (
                    <div
                      key={rev.id}
                      style={{
                        padding: '14px',
                        background: 'var(--bg-subtle)',
                        borderRadius: '10px',
                        border: '1px solid var(--border-light)'
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <strong style={{ fontSize: '0.9rem', color: 'var(--text-heading)' }}>{rev.patientName}</strong>
                          <span className="badge badge-teal" style={{ fontSize: '0.68rem', padding: '2px 6px' }}>Verified Patient</span>
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '4px', color: '#D97706', fontSize: '0.85rem', fontWeight: 700 }}>
                          <Star size={14} color="#D97706" fill="#D97706" /> {rev.rating} / 5.0
                        </div>
                      </div>
                      <p style={{ margin: '4px 0 6px', fontSize: '0.84rem', color: 'var(--text-main)' }}>
                        {rev.reviewText}
                      </p>
                      <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                        {rev.createdAt}
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>

        {/* Modal Bottom Actions Footer */}
        <div
          style={{
            padding: '16px 24px',
            borderTop: '1px solid var(--border-light)',
            background: 'var(--bg-subtle)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: '12px'
          }}
        >
          <div style={{ display: 'flex', gap: '8px' }}>
            {onOpenCompare && (
              <Button
                variant="secondary"
                size="sm"
                onClick={() => {
                  onOpenCompare(hospital);
                  onClose();
                }}
              >
                Compare with Others
              </Button>
            )}
            <a
              href={`https://maps.google.com/?q=${encodeURIComponent(hospital.name + ' ' + hospital.city)}`}
              target="_blank"
              rel="noreferrer"
              style={{ textDecoration: 'none' }}
            >
              <Button variant="ghost" size="sm" rightIcon={<ExternalLink size={14} />}>
                Get Directions
              </Button>
            </a>
          </div>

          <Button
            variant="teal"
            onClick={() => {
              onBookWithDoctor(hospital);
              onClose();
            }}
            rightIcon={<ChevronRight size={16} />}
          >
            Book OPD Appointment
          </Button>
        </div>
      </div>
    </div>
  );
};
