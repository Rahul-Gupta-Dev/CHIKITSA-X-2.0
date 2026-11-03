import React, { useState, useEffect } from 'react';
import { db } from '../../db/database';
import { patientService, recordService, consentService } from '../../services/apiServices';
import type { PatientProfile, MedicalRecord, PatientConsent } from '../../types';
import { DisclaimerBanner } from '../common/DisclaimerBanner';
import {
  Pill,
  Heart,
  CheckCircle2,
  FileText,
  Upload,
  Search,
  Eye,
  Lock,
  Unlock,
  Plus,
  Trash2,
  ShieldCheck,
  Download,
  Loader2,
  AlertCircle,
  RotateCcw
} from 'lucide-react';
import { Button, Card, Badge, EmptyState, ConfirmationDialog } from '../common/UIComponents';
import { MedicalRecordOCR } from './MedicalRecordOCR';

interface Props {
  onOpenUploadOCR?: () => void;
}

export const HealthProfileView: React.FC<Props> = ({ onOpenUploadOCR }) => {
  const [profile, setProfile] = useState<PatientProfile>(() => db.getPatientProfile());
  const [medicalRecords, setMedicalRecords] = useState<MedicalRecord[]>([]);
  const [consents, setConsents] = useState<PatientConsent[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  const [activeTab, setActiveTab] = useState<'RECORDS' | 'VITALS_MEDS' | 'CONSENTS'>('RECORDS');
  const [isOCROpen, setIsOCROpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('ALL');

  // Record detail viewer modal
  const [viewingRecord, setViewingRecord] = useState<MedicalRecord | null>(null);

  // Profile Edit State
  const [isEditingProfile, setIsEditingProfile] = useState(false);
  const [isSavingProfile, setIsSavingProfile] = useState(false);
  const [fullName, setFullName] = useState(profile.fullName);
  const [age, setAge] = useState(profile.age);
  const [bloodGroup, setBloodGroup] = useState(profile.bloodGroup);
  const [phone, setPhone] = useState(profile.phone);
  const [emergencyPhone, setEmergencyPhone] = useState(profile.emergencyContact?.phone || '');

  // New Medication input
  const [newMed, setNewMed] = useState('');
  // New Allergy input
  const [newAllergy, setNewAllergy] = useState('');

  // Revoke Consent State
  const [revokingConsentId, setRevokingConsentId] = useState<string | null>(null);
  const [isRevoking, setIsRevoking] = useState(false);

  // Authenticated Download State
  const [downloadingId, setDownloadingId] = useState<string | null>(null);

  const handleDownloadRecord = async (recordId: string, fileName?: string) => {
    setDownloadingId(recordId);
    try {
      await recordService.downloadRecordFile(recordId, fileName);
    } catch (err: any) {
      alert(`Download failed: ${err?.message || 'Access denied or file not found.'}`);
    } finally {
      setDownloadingId(null);
    }
  };

  const loadData = async () => {
    setIsLoading(true);
    setLoadError(null);
    try {
      const user = db.getCurrentUser();
      const uid = user?.id || 'me';

      const [profRes, recordsRes, consentsRes] = await Promise.allSettled([
        patientService.getProfile(uid),
        recordService.getRecords(uid),
        consentService.getConsents(uid)
      ]);

      if (profRes.status === 'fulfilled' && profRes.value) {
        setProfile(profRes.value);
        setFullName(profRes.value.fullName);
        setAge(profRes.value.age);
        setBloodGroup(profRes.value.bloodGroup);
        setPhone(profRes.value.phone);
        setEmergencyPhone(profRes.value.emergencyContact?.phone || '');
      }

      if (recordsRes.status === 'fulfilled') {
        setMedicalRecords(recordsRes.value);
      } else {
        console.warn('Failed to fetch records from server:', recordsRes.reason);
      }

      if (consentsRes.status === 'fulfilled') {
        setConsents(consentsRes.value);
      } else {
        console.warn('Failed to fetch consents from server:', consentsRes.reason);
      }
    } catch (err: any) {
      console.error('Failed to load profile data:', err);
      setLoadError(err?.message || 'Failed to retrieve profile data from server.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleSaveProfile = async () => {
    setIsSavingProfile(true);
    try {
      const user = db.getCurrentUser();
      const updated = await patientService.updateProfile({
        fullName,
        age: Number(age),
        bloodGroup,
        phone,
        emergencyContact: {
          ...profile.emergencyContact,
          phone: emergencyPhone
        }
      }, user?.id);
      setProfile(updated);
      setIsEditingProfile(false);
    } catch (err: any) {
      alert(err?.message || 'Failed to update profile on backend.');
    } finally {
      setIsSavingProfile(false);
    }
  };

  const handleAddMedication = async () => {
    if (!newMed.trim()) return;
    const updated = [...profile.medications, newMed.trim()];
    const user = db.getCurrentUser();
    await patientService.updateProfile({ medications: updated }, user?.id);
    setProfile(prev => ({ ...prev, medications: updated }));
    setNewMed('');
  };

  const handleRemoveMedication = async (index: number) => {
    const updated = profile.medications.filter((_, i) => i !== index);
    const user = db.getCurrentUser();
    await patientService.updateProfile({ medications: updated }, user?.id);
    setProfile(prev => ({ ...prev, medications: updated }));
  };

  const handleAddAllergy = async () => {
    if (!newAllergy.trim()) return;
    const updated = [...profile.allergies, newAllergy.trim()];
    const user = db.getCurrentUser();
    await patientService.updateProfile({ allergies: updated }, user?.id);
    setProfile(prev => ({ ...prev, allergies: updated }));
    setNewAllergy('');
  };

  const handleRemoveAllergy = async (index: number) => {
    const updated = profile.allergies.filter((_, i) => i !== index);
    const user = db.getCurrentUser();
    await patientService.updateProfile({ allergies: updated }, user?.id);
    setProfile(prev => ({ ...prev, allergies: updated }));
  };

  const handleConfirmRevokeConsent = async () => {
    if (!revokingConsentId) return;
    setIsRevoking(true);
    try {
      await consentService.revokeConsent(revokingConsentId);
      setRevokingConsentId(null);
      const user = db.getCurrentUser();
      const updatedConsents = await consentService.getConsents(user?.id);
      setConsents(updatedConsents);
      alert('Hospital medical record access consent revoked successfully.');
    } catch (err: any) {
      console.error('Revoke consent failed:', err);
      alert(err?.message || 'Failed to revoke consent on server.');
    } finally {
      setIsRevoking(false);
    }
  };

  const filteredRecords = medicalRecords.filter(rec => {
    const matchesSearch = !searchQuery ||
      rec.fileName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (rec.ocrExtractedData.doctorName && rec.ocrExtractedData.doctorName.toLowerCase().includes(searchQuery.toLowerCase())) ||
      (rec.ocrExtractedData.hospitalName && rec.ocrExtractedData.hospitalName.toLowerCase().includes(searchQuery.toLowerCase()));

    const matchesCategory = selectedCategory === 'ALL' || rec.category === selectedCategory;

    return matchesSearch && matchesCategory;
  });

  return (
    <div style={{ maxWidth: '1080px', margin: '0 auto', padding: '10px 0 40px' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px', marginBottom: '20px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
            <Badge variant="teal">HEALTH VAULT &amp; PROFILE</Badge>
            <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>ABDM-Compliant Unified Record</span>
          </div>
          <h1 style={{ fontSize: '1.75rem', color: 'var(--text-heading)', margin: 0 }}>
            Medical Records &amp; Health Profile
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', margin: '4px 0 0' }}>
            Manage extracted prescriptions, diagnostic lab reports, vitals, allergies, and hospital consent permissions.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '10px' }}>
          <Button
            variant="teal"
            onClick={() => onOpenUploadOCR ? onOpenUploadOCR() : setIsOCROpen(true)}
            leftIcon={<Upload size={16} />}
          >
            Upload Report (OCR)
          </Button>
        </div>
      </div>

      <DisclaimerBanner text="Medical records stored in CHIKITSA-X are protected under consent-first encryption. Treating doctors can only inspect your clinical history after your explicit authorization." />

      {isLoading && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '12px 16px', background: 'rgba(2, 132, 199, 0.08)', borderRadius: '10px', marginBottom: '16px', color: 'var(--primary-teal)', fontSize: '0.9rem' }}>
          <Loader2 size={18} className="spin" />
          <span>Syncing medical records and consents with CHIKITSA-X cloud...</span>
        </div>
      )}

      {loadError && (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '12px 16px', background: 'rgba(220, 38, 38, 0.08)', border: '1px solid #DC2626', borderRadius: '10px', marginBottom: '16px', color: '#DC2626', fontSize: '0.9rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <AlertCircle size={18} />
            <span>{loadError}</span>
          </div>
          <Button variant="outline" size="sm" onClick={() => loadData()} leftIcon={<RotateCcw size={14} />}>
            Retry
          </Button>
        </div>
      )}

      {/* Tabs */}
      <div
        style={{
          display: 'flex',
          gap: '8px',
          borderBottom: '1px solid var(--border-light)',
          marginBottom: '24px',
          paddingBottom: '8px',
          overflowX: 'auto'
        }}
      >
        <button
          onClick={() => setActiveTab('RECORDS')}
          className={`btn btn-sm ${activeTab === 'RECORDS' ? 'btn-primary' : 'btn-ghost'}`}
        >
          <FileText size={15} /> Medical Records &amp; Prescriptions ({medicalRecords.length})
        </button>
        <button
          onClick={() => setActiveTab('VITALS_MEDS')}
          className={`btn btn-sm ${activeTab === 'VITALS_MEDS' ? 'btn-primary' : 'btn-ghost'}`}
        >
          <Heart size={15} /> Clinical Profile, Vitals &amp; Rx
        </button>
        <button
          onClick={() => setActiveTab('CONSENTS')}
          className={`btn btn-sm ${activeTab === 'CONSENTS' ? 'btn-primary' : 'btn-ghost'}`}
        >
          <Lock size={15} /> Hospital Access Consents ({consents.filter(c => c.status === 'GRANTED').length} Active)
        </button>
      </div>

      {/* TAB 1: MEDICAL RECORDS & OCR ARCHIVE */}
      {activeTab === 'RECORDS' && (
        <div>
          {/* Search and Category Filter Toolbar */}
          <div
            style={{
              background: 'var(--bg-card)',
              border: '1px solid var(--border-light)',
              borderRadius: '14px',
              padding: '14px 18px',
              display: 'flex',
              gap: '12px',
              flexWrap: 'wrap',
              alignItems: 'center',
              marginBottom: '20px'
            }}
          >
            <div style={{ flex: 1, minWidth: '220px', position: 'relative' }}>
              <Search size={16} color="var(--text-muted)" style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)' }} />
              <input
                type="text"
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                placeholder="Search records by title, doctor, or clinic..."
                className="form-control"
                style={{ paddingLeft: '36px', height: '38px', fontSize: '0.88rem' }}
              />
            </div>

            <div style={{ minWidth: '180px' }}>
              <select
                value={selectedCategory}
                onChange={e => setSelectedCategory(e.target.value)}
                className="form-control"
                style={{ height: '38px', fontSize: '0.88rem' }}
              >
                <option value="ALL">All Categories</option>
                <option value="Prescription">Prescriptions</option>
                <option value="Lab Report">Lab Reports</option>
                <option value="Discharge Summary">Discharge Summaries</option>
                <option value="Radiology Report">Radiology</option>
              </select>
            </div>
          </div>

          {/* Records Table / Cards */}
          {filteredRecords.length === 0 ? (
            <EmptyState
              icon={<FileText size={32} />}
              title="No Medical Records Found"
              description="Upload your prescription, lab report, or discharge summary to automatically extract medications, diagnoses, and lab values."
              actionLabel="Upload Medical Record"
              onAction={() => onOpenUploadOCR ? onOpenUploadOCR() : setIsOCROpen(true)}
              actionIcon={<Upload size={16} />}
            />
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {filteredRecords.map(rec => (
                <Card
                  key={rec.id}
                  padding="18px 22px"
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    flexWrap: 'wrap',
                    gap: '12px'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
                    <div
                      style={{
                        width: '44px',
                        height: '44px',
                        borderRadius: '12px',
                        background: 'rgba(2, 132, 199, 0.12)',
                        color: 'var(--primary-teal)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center'
                      }}
                    >
                      <FileText size={22} />
                    </div>
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '2px' }}>
                        <h4 style={{ margin: 0, fontSize: '1.05rem', color: 'var(--text-heading)' }}>
                          {rec.fileName}
                        </h4>
                        <Badge
                          variant={
                            rec.category === 'Prescription'
                              ? 'teal'
                              : rec.category === 'Lab Report'
                              ? 'green'
                              : 'purple'
                          }
                          size="sm"
                        >
                          {rec.category}
                        </Badge>
                      </div>
                      <p style={{ margin: 0, fontSize: '0.82rem', color: 'var(--text-muted)' }}>
                        Uploaded on {rec.uploadDate} • Format: {rec.fileType} • {rec.ocrExtractedData.medicinesExtracted?.length || 0} Extracted Meds
                      </p>
                    </div>
                  </div>

                  <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => handleDownloadRecord(rec.id, rec.fileName)}
                      disabled={downloadingId === rec.id}
                      leftIcon={<Download size={14} />}
                    >
                      {downloadingId === rec.id ? 'Downloading...' : 'Download'}
                    </Button>
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => setViewingRecord(rec)}
                      leftIcon={<Eye size={14} />}
                    >
                      View Extracted Record
                    </Button>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </div>
      )}

      {/* TAB 2: CLINICAL PROFILE, VITALS & MEDICATIONS */}
      {activeTab === 'VITALS_MEDS' && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '20px' }}>
          {/* Personal Info Card */}
          <Card padding="24px">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <h3 style={{ fontSize: '1.15rem', color: 'var(--text-heading)', margin: 0 }}>
                Patient Identity
              </h3>
              <Button
                variant={isEditingProfile ? 'teal' : 'secondary'}
                size="sm"
                isLoading={isSavingProfile}
                onClick={() => {
                  if (isEditingProfile) handleSaveProfile();
                  else setIsEditingProfile(true);
                }}
              >
                {isEditingProfile ? 'Save Details' : 'Edit Info'}
              </Button>
            </div>

            {isEditingProfile ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                <div>
                  <label className="form-label">Full Name</label>
                  <input
                    type="text"
                    value={fullName}
                    onChange={e => setFullName(e.target.value)}
                    className="form-control"
                  />
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                  <div>
                    <label className="form-label">Age</label>
                    <input
                      type="number"
                      value={age}
                      onChange={e => setAge(Number(e.target.value))}
                      className="form-control"
                    />
                  </div>
                  <div>
                    <label className="form-label">Blood Group</label>
                    <input
                      type="text"
                      value={bloodGroup}
                      onChange={e => setBloodGroup(e.target.value)}
                      className="form-control"
                    />
                  </div>
                </div>
                <div>
                  <label className="form-label">Phone</label>
                  <input
                    type="tel"
                    value={phone}
                    onChange={e => setPhone(e.target.value)}
                    className="form-control"
                  />
                </div>
                <div>
                  <label className="form-label">Emergency Phone</label>
                  <input
                    type="tel"
                    value={emergencyPhone}
                    onChange={e => setEmergencyPhone(e.target.value)}
                    className="form-control"
                  />
                </div>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '0.9rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border-light)', paddingBottom: '6px' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Name:</span>
                  <strong style={{ color: 'var(--text-heading)' }}>{profile.fullName}</strong>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border-light)', paddingBottom: '6px' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Age &amp; Gender:</span>
                  <span style={{ color: 'var(--text-main)' }}>{profile.age} yrs • {profile.gender}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border-light)', paddingBottom: '6px' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Blood Group:</span>
                  <span className="badge badge-red">{profile.bloodGroup}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border-light)', paddingBottom: '6px' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Contact:</span>
                  <span style={{ color: 'var(--text-main)' }}>{profile.phone}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Emergency Contact:</span>
                  <span style={{ color: 'var(--text-main)' }}>{profile.emergencyContact.name} ({profile.emergencyContact.phone})</span>
                </div>
              </div>
            )}
          </Card>

          {/* Active Medications Card */}
          <Card padding="24px">
            <h3 style={{ fontSize: '1.15rem', color: 'var(--text-heading)', margin: '0 0 14px' }}>
              Active Prescriptions (Extracted via OCR)
            </h3>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginBottom: '16px' }}>
              {profile.medications.map((med, i) => (
                <div
                  key={i}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '8px 12px',
                    borderRadius: '8px',
                    background: 'var(--bg-subtle)',
                    border: '1px solid var(--border-light)',
                    fontSize: '0.88rem'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <Pill size={14} color="#16A34A" />
                    <span>{med}</span>
                  </div>
                  <button
                    onClick={() => handleRemoveMedication(i)}
                    style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}
                    title="Remove Medication"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              ))}
            </div>

            <div style={{ display: 'flex', gap: '8px' }}>
              <input
                type="text"
                value={newMed}
                onChange={e => setNewMed(e.target.value)}
                placeholder="Add medication (e.g., Aspirin 75mg)..."
                className="form-control"
                style={{ height: '36px', fontSize: '0.85rem' }}
              />
              <Button variant="secondary" size="sm" onClick={handleAddMedication} leftIcon={<Plus size={14} />}>
                Add
              </Button>
            </div>
          </Card>

          {/* Known Allergies Card */}
          <Card padding="24px">
            <h3 style={{ fontSize: '1.15rem', color: 'var(--text-heading)', margin: '0 0 14px' }}>
              Known Allergies &amp; Red Flags
            </h3>

            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginBottom: '16px' }}>
              {profile.allergies.map((all, i) => (
                <div
                  key={i}
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '6px',
                    padding: '6px 12px',
                    borderRadius: '20px',
                    background: 'rgba(220, 38, 38, 0.12)',
                    border: '1px solid rgba(220, 38, 38, 0.25)',
                    color: '#DC2626',
                    fontSize: '0.82rem',
                    fontWeight: 600
                  }}
                >
                  <span>{all}</span>
                  <button
                    onClick={() => handleRemoveAllergy(i)}
                    style={{ background: 'none', border: 'none', color: '#DC2626', cursor: 'pointer', padding: 0 }}
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>

            <div style={{ display: 'flex', gap: '8px' }}>
              <input
                type="text"
                value={newAllergy}
                onChange={e => setNewAllergy(e.target.value)}
                placeholder="Add allergy (e.g., Sulfa drugs)..."
                className="form-control"
                style={{ height: '36px', fontSize: '0.85rem' }}
              />
              <Button variant="secondary" size="sm" onClick={handleAddAllergy} leftIcon={<Plus size={14} />}>
                Add
              </Button>
            </div>
          </Card>

          {/* Pre-existing History */}
          <Card padding="24px">
            <h3 style={{ fontSize: '1.15rem', color: 'var(--text-heading)', margin: '0 0 14px' }}>
              Pre-Existing Medical Conditions
            </h3>
            <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '0.88rem', color: 'var(--text-secondary)' }}>
              {profile.medicalHistory.map((hist, i) => (
                <li key={i} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <CheckCircle2 size={16} color="var(--primary-teal)" />
                  <span>{hist}</span>
                </li>
              ))}
            </ul>
          </Card>
        </div>
      )}

      {/* TAB 3: ACCESS CONSENTS */}
      {activeTab === 'CONSENTS' && (
        <div>
          <div style={{ marginBottom: '16px' }}>
            <h3 style={{ fontSize: '1.25rem', color: 'var(--text-heading)', margin: '0 0 4px' }}>
              Hospital &amp; Clinician Data Access Permissions
            </h3>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.88rem', margin: 0 }}>
              Under ABDM guidelines, treating physicians can only view your medical summary while your digital consent is active. You may revoke consent at any moment.
            </p>
          </div>

          {consents.length === 0 ? (
            <EmptyState
              icon={<ShieldCheck size={32} />}
              title="No Active Consent Requests"
              description="No healthcare facility currently holds medical record access permissions."
            />
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {consents.map(c => (
                <Card
                  key={c.id}
                  padding="20px 24px"
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    flexWrap: 'wrap',
                    gap: '12px'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
                    <div
                      style={{
                        padding: '10px',
                        borderRadius: '12px',
                        background: c.status === 'GRANTED' ? 'rgba(22, 163, 74, 0.12)' : 'rgba(220, 38, 38, 0.12)',
                        color: c.status === 'GRANTED' ? '#16A34A' : '#DC2626'
                      }}
                    >
                      {c.status === 'GRANTED' ? <Unlock size={22} /> : <Lock size={22} />}
                    </div>
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '2px' }}>
                        <h4 style={{ margin: 0, fontSize: '1.05rem', color: 'var(--text-heading)' }}>
                          {c.hospitalName}
                        </h4>
                        <Badge variant={c.status === 'GRANTED' ? 'green' : 'red'} size="sm">
                          {c.status}
                        </Badge>
                      </div>
                      <p style={{ margin: 0, fontSize: '0.82rem', color: 'var(--text-muted)' }}>
                        Requested: {c.requestedAt} {c.doctorName ? `by ${c.doctorName}` : ''} • Scope: Symptoms, OCR Records, Triage
                      </p>
                    </div>
                  </div>

                  {c.status === 'GRANTED' && (
                    <Button
                      variant="danger"
                      size="sm"
                      onClick={() => setRevokingConsentId(c.id)}
                    >
                      Revoke Consent
                    </Button>
                  )}
                </Card>
              ))}
            </div>
          )}
        </div>
      )}

      {/* VIEW EXTRACTED RECORD MODAL */}
      {viewingRecord && (
        <div className="modal-overlay" onClick={() => setViewingRecord(null)}>
          <div className="modal-content" style={{ maxWidth: '640px', padding: '24px' }} onClick={e => e.stopPropagation()}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <div>
                <Badge variant="teal">{viewingRecord.category}</Badge>
                <h3 style={{ margin: '4px 0 0', color: 'var(--text-heading)', fontSize: '1.25rem' }}>
                  {viewingRecord.fileName}
                </h3>
              </div>
              <button
                onClick={() => setViewingRecord(null)}
                style={{ background: 'none', border: 'none', fontSize: '1.4rem', cursor: 'pointer', color: 'var(--text-muted)' }}
              >
                ×
              </button>
            </div>

            <div style={{ background: 'var(--bg-subtle)', padding: '16px', borderRadius: '12px', border: '1px solid var(--border-light)', marginBottom: '16px', fontSize: '0.88rem' }}>
              <div style={{ marginBottom: '8px' }}>
                <span style={{ color: 'var(--text-muted)' }}>Upload Timestamp:</span> <strong>{viewingRecord.uploadDate}</strong>
              </div>
              {viewingRecord.ocrExtractedData.doctorName && (
                <div style={{ marginBottom: '8px' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Prescribing Doctor:</span> <strong>{viewingRecord.ocrExtractedData.doctorName}</strong>
                </div>
              )}
              {viewingRecord.ocrExtractedData.hospitalName && (
                <div style={{ marginBottom: '8px' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Hospital Clinic:</span> <strong>{viewingRecord.ocrExtractedData.hospitalName}</strong>
                </div>
              )}
              {viewingRecord.ocrExtractedData.diagnosisExtracted && (
                <div style={{ marginBottom: '8px' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Extracted Observations:</span> <strong>{viewingRecord.ocrExtractedData.diagnosisExtracted}</strong>
                </div>
              )}
            </div>

            {/* Extracted Medicines */}
            {viewingRecord.ocrExtractedData.medicinesExtracted && viewingRecord.ocrExtractedData.medicinesExtracted.length > 0 && (
              <div style={{ marginBottom: '16px' }}>
                <h4 style={{ fontSize: '0.92rem', color: 'var(--text-heading)', marginBottom: '8px' }}>
                  Extracted Medications &amp; Dosages
                </h4>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  {viewingRecord.ocrExtractedData.medicinesExtracted.map((m, i) => (
                    <div key={i} style={{ padding: '8px 12px', background: 'var(--bg-card)', border: '1px solid var(--border-light)', borderRadius: '8px', fontSize: '0.85rem' }}>
                      <Pill size={13} color="#16A34A" style={{ display: 'inline', marginRight: '6px' }} />
                      {m}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Extracted Lab Metrics */}
            {viewingRecord.ocrExtractedData.labResults && viewingRecord.ocrExtractedData.labResults.length > 0 && (
              <div style={{ marginBottom: '16px' }}>
                <h4 style={{ fontSize: '0.92rem', color: 'var(--text-heading)', marginBottom: '8px' }}>
                  Extracted Laboratory Metrics
                </h4>
                <table className="health-table">
                  <thead>
                    <tr>
                      <th>Test Name</th>
                      <th>Observed Value</th>
                      <th>Reference Range</th>
                    </tr>
                  </thead>
                  <tbody>
                    {viewingRecord.ocrExtractedData.labResults.map((lab, i) => (
                      <tr key={i}>
                        <td><strong>{lab.testName}</strong></td>
                        <td style={{ color: 'var(--primary-teal)', fontWeight: 700 }}>{lab.value} {lab.unit}</td>
                        <td style={{ color: 'var(--text-muted)' }}>{lab.range}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '20px' }}>
              <Button
                variant="teal"
                size="sm"
                onClick={() => handleDownloadRecord(viewingRecord.id, viewingRecord.fileName)}
                disabled={downloadingId === viewingRecord.id}
                leftIcon={<Download size={14} />}
              >
                {downloadingId === viewingRecord.id ? 'Downloading...' : 'Download Document'}
              </Button>
              <Button variant="secondary" onClick={() => setViewingRecord(null)}>
                Close
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* OCR Document Uploader Modal */}
      <MedicalRecordOCR
        isOpen={isOCROpen}
        onClose={() => setIsOCROpen(false)}
        onRecordSaved={() => {
          loadData();
          setIsOCROpen(false);
        }}
      />

      {/* CONFIRM REVOCATION DIALOG */}
      <ConfirmationDialog
        isOpen={Boolean(revokingConsentId)}
        title="Revoke Data Access Consent?"
        message="Treating doctors at this hospital will immediately lose access to your medical history, symptoms, and OCR records. You can grant access again at any time."
        confirmLabel={isRevoking ? 'Revoking Access...' : 'Yes, Revoke Access'}
        confirmVariant="danger"
        onConfirm={handleConfirmRevokeConsent}
        onCancel={() => setRevokingConsentId(null)}
      />
    </div>
  );
};
