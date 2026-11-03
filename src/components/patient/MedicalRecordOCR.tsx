import React, { useState, useRef } from 'react';
import { ocrService } from '../../services/apiServices';
import type { MedicalRecord } from '../../types';
import { DisclaimerBanner } from '../common/DisclaimerBanner';
import { FileText, Upload, CheckCircle2, Edit3, Plus, Trash2, X, Sparkles, File, AlertCircle } from 'lucide-react';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onRecordSaved: (record: MedicalRecord) => void;
}

export const MedicalRecordOCR: React.FC<Props> = ({ isOpen, onClose, onRecordSaved }) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [category, setCategory] = useState<MedicalRecord['category']>('Prescription');
  const [fileType, setFileType] = useState<'PDF' | 'JPG' | 'PNG'>('PDF');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const [step, setStep] = useState<'UPLOAD' | 'PROCESSING' | 'REVIEW'>('UPLOAD');
  const [extractedRecord, setExtractedRecord] = useState<MedicalRecord | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  // Editable fields
  const [editedMedicines, setEditedMedicines] = useState<string[]>([]);
  const [editedDiagnosis, setEditedDiagnosis] = useState('');
  const [editedCondition, setEditedCondition] = useState('');

  const handleClose = () => {
    setSelectedFile(null);
    setStep('UPLOAD');
    setExtractedRecord(null);
    setErrorMessage(null);
    onClose();
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const file = e.target.files[0];
      setSelectedFile(file);
      setErrorMessage(null);

      const extension = file.name.split('.').pop()?.toUpperCase();
      if (extension === 'PNG') setFileType('PNG');
      else if (extension === 'JPG' || extension === 'JPEG') setFileType('JPG');
      else setFileType('PDF');
    }
  };

  const handleUseDemoFile = () => {
    const demoContent = "CHIKITSA-X Sample Prescription\nDoctor: Dr. Rajesh Kulkarni\nHospital: CarePlus Super Specialty Hospital\nDiagnosis: Hypertension Evaluation\nRx:\nTab Telmisartan 40mg OD\nTab Metformin 500mg BD\nTab Atorvastatin 20mg HS";
    const demoBlob = new Blob([demoContent], { type: 'text/plain' });
    const demoFile = new (window as any).File([demoBlob], 'Prescription_Cardiology_2026.txt', { type: 'text/plain' }) as File;
    setSelectedFile(demoFile);
    setFileType('PDF');
    setCategory('Prescription');
    setErrorMessage(null);
  };

  const handleStartUpload = async () => {
    if (!selectedFile) {
      setErrorMessage('Please select a file (PDF, JPG, PNG) before proceeding.');
      return;
    }

    setStep('PROCESSING');
    try {
      const rec = await ocrService.processUploadedFile(selectedFile.name, fileType, category, selectedFile);
      setExtractedRecord(rec);

      // Populate editable fields
      setEditedMedicines(rec.ocrExtractedData.medicinesExtracted || []);
      setEditedDiagnosis(rec.ocrExtractedData.diagnosisExtracted || '');
      setEditedCondition(rec.ocrExtractedData.previousCondition || '');

      setStep('REVIEW');
    } catch (err: any) {
      setStep('UPLOAD');
      setErrorMessage(err?.message || 'Failed to upload and process medical document with server.');
    }
  };

  const handleSaveToProfile = () => {
    if (!extractedRecord) return;
    const finalRecord: MedicalRecord = {
      ...extractedRecord,
      ocrExtractedData: {
        ...extractedRecord.ocrExtractedData,
        medicinesExtracted: editedMedicines,
        diagnosisExtracted: editedDiagnosis,
        previousCondition: editedCondition
      },
      isVerifiedByPatient: true
    };
    onRecordSaved(finalRecord);
    onClose();
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' bytes';
    else if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / 1048576).toFixed(1) + ' MB';
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={handleClose}>
      <div className="modal-content" style={{ maxWidth: '680px' }} onClick={e => e.stopPropagation()}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{ background: 'linear-gradient(135deg, #0284C7 0%, #0369A1 100%)', padding: '8px', borderRadius: '10px', color: '#FFF' }}>
              <FileText size={22} />
            </div>
            <div>
              <h3 style={{ fontSize: '1.25rem', margin: 0, color: 'var(--text-heading)' }}>Medical Record Upload & OCR Engine</h3>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem', margin: 0 }}>Extract medicines & diagnostics from prescriptions or lab reports</p>
            </div>
          </div>
          <button onClick={handleClose} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}>
            <X size={20} />
          </button>
        </div>

        <DisclaimerBanner text="AI OCR extraction — verify and edit extracted clinical details before saving to your health profile." />

        {step === 'UPLOAD' && (
          <div>
            {/* Category selection */}
            <div style={{ marginBottom: '16px' }}>
              <label className="form-label">Document Category:</label>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: '8px' }}>
                {(['Prescription', 'Lab Report', 'Discharge Summary', 'Radiology Report', 'Other'] as const).map((cat) => (
                  <button
                    key={cat}
                    type="button"
                    onClick={() => setCategory(cat)}
                    className={`btn btn-sm ${category === cat ? 'btn-primary' : 'btn-secondary'}`}
                    style={{ fontSize: '0.82rem' }}
                  >
                    {cat}
                  </button>
                ))}
              </div>
            </div>

            {/* Hidden File Input */}
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileChange}
              accept=".pdf,.jpg,.jpeg,.png"
              style={{ display: 'none' }}
            />

            {/* Upload Area */}
            <div
              onClick={() => fileInputRef.current?.click()}
              style={{
                border: selectedFile ? '2px solid var(--primary-teal)' : '2px dashed var(--border-dark)',
                borderRadius: '14px',
                padding: '28px 20px',
                textAlign: 'center',
                background: selectedFile ? 'rgba(0, 180, 216, 0.08)' : 'var(--bg-main)',
                marginBottom: '16px',
                cursor: 'pointer',
                transition: 'all 0.2s ease'
              }}
            >
              <Upload size={36} color="var(--primary-teal)" style={{ margin: '0 auto 10px' }} />
              {selectedFile ? (
                <div>
                  <div style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', background: 'var(--bg-card)', padding: '8px 16px', borderRadius: '10px', border: '1px solid var(--border-light)' }}>
                    <File size={20} color="var(--primary-teal)" />
                    <div style={{ textAlign: 'left' }}>
                      <div style={{ fontWeight: 700, fontSize: '0.9rem', color: 'var(--text-main)' }}>{selectedFile.name}</div>
                      <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>{fileType} • {formatFileSize(selectedFile.size)}</div>
                    </div>
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        setSelectedFile(null);
                      }}
                      style={{ background: 'none', border: 'none', color: '#EF4444', marginLeft: '12px', cursor: 'pointer' }}
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                  <p style={{ fontSize: '0.8rem', color: 'var(--primary-teal-dark)', marginTop: '8px', margin: 0 }}>Click to change file</p>
                </div>
              ) : (
                <div>
                  <p style={{ fontWeight: '600', fontSize: '0.95rem', color: 'var(--text-main)', marginBottom: '4px' }}>
                    Click to Choose Document (PDF, JPG, PNG)
                  </p>
                  <p style={{ color: 'var(--text-muted)', fontSize: '0.82rem', margin: 0 }}>
                    Select a local medical record or prescription file from your device
                  </p>
                </div>
              )}
            </div>

            {/* Optional Demo Medical Record Button */}
            <div style={{ marginBottom: '20px', display: 'flex', justifyContent: 'center' }}>
              <button
                type="button"
                onClick={handleUseDemoFile}
                className="btn btn-secondary btn-sm"
                style={{ fontSize: '0.8rem' }}
              >
                📄 Try Demo Medical Record (Prescription_Cardiology_2024.pdf)
              </button>
            </div>

            {errorMessage && (
              <div style={{ padding: '10px 14px', background: 'rgba(239, 68, 68, 0.12)', border: '1px solid rgba(239, 68, 68, 0.3)', borderRadius: '10px', color: '#DC2626', fontSize: '0.85rem', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <AlertCircle size={16} /> {errorMessage}
              </div>
            )}

            <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
              <button onClick={onClose} className="btn btn-secondary">
                Cancel
              </button>
              <button
                onClick={handleStartUpload}
                disabled={!selectedFile}
                className="btn btn-primary"
                style={{ opacity: selectedFile ? 1 : 0.65, cursor: selectedFile ? 'pointer' : 'not-allowed' }}
              >
                Upload & Process OCR <Sparkles size={16} />
              </button>
            </div>
          </div>
        )}

        {step === 'PROCESSING' && (
          <div style={{ textAlign: 'center', padding: '40px 0' }}>
            <div style={{
              width: '56px',
              height: '56px',
              border: '4px solid rgba(0, 180, 216, 0.2)',
              borderTopColor: 'var(--primary-teal)',
              borderRadius: '50%',
              margin: '0 auto 20px',
              animation: 'spin 1s linear infinite'
            }} />
            <h4 style={{ fontSize: '1.2rem', marginBottom: '8px' }}>Scanning & Processing Document OCR...</h4>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>Extracting active medicines, diagnoses, and lab values from {selectedFile?.name}</p>
            <style>{`@keyframes spin { 100% { transform: rotate(360deg); } }`}</style>
          </div>
        )}

        {step === 'REVIEW' && extractedRecord && (
          <div>
            <div style={{ background: 'rgba(0, 180, 216, 0.1)', border: '1px solid rgba(0, 180, 216, 0.3)', borderRadius: '12px', padding: '14px', marginBottom: '20px' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '8px', marginBottom: '4px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--primary-teal-dark)', fontWeight: 700, fontSize: '0.95rem' }}>
                  <CheckCircle2 size={18} /> Extracted Document Summary ({category})
                </div>
                <span className={`badge ${extractedRecord.ocrExtractedData.ocrAdapterStatus === 'PROCESSED_FROM_SOURCE_TEXT' ? 'badge-teal' : 'badge-amber'}`} style={{ fontSize: '0.75rem' }}>
                  {extractedRecord.ocrExtractedData.ocrAdapterStatus === 'PROCESSED_FROM_SOURCE_TEXT' ? '✓ Text Extracted from Document' : 'ℹ️ Document Stored (Manual Entry)'}
                </span>
              </div>
              <p style={{ color: 'var(--text-main)', fontSize: '0.82rem', margin: 0 }}>
                File: <strong>{extractedRecord.fileName}</strong> • Doctor/Clinic: {extractedRecord.ocrExtractedData.doctorName || 'Not specified (manual review)'}
              </p>
              {extractedRecord.ocrExtractedData.ocrNote && (
                <p style={{ color: 'var(--text-muted)', fontSize: '0.75rem', marginTop: '4px', fontStyle: 'italic' }}>
                  {extractedRecord.ocrExtractedData.ocrNote}
                </p>
              )}
            </div>

            {/* Editable Extracted Medicines */}
            <div style={{ marginBottom: '16px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                <label className="form-label" style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <Edit3 size={14} color="var(--primary-teal)" /> Extracted Medicines (Editable):
                </label>
                <button
                  type="button"
                  onClick={() => setEditedMedicines([...editedMedicines, 'New Medicine 10mg OD'])}
                  className="btn btn-secondary btn-sm"
                  style={{ fontSize: '0.75rem', padding: '2px 8px' }}
                >
                  <Plus size={12} /> Add Medicine
                </button>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {editedMedicines.map((med, idx) => (
                  <div key={idx} style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                    <input
                      type="text"
                      value={med}
                      onChange={(e) => {
                        const copy = [...editedMedicines];
                        copy[idx] = e.target.value;
                        setEditedMedicines(copy);
                      }}
                      className="form-control"
                      style={{ padding: '8px 12px', fontSize: '0.88rem' }}
                    />
                    <button
                      type="button"
                      onClick={() => setEditedMedicines(editedMedicines.filter((_, i) => i !== idx))}
                      style={{ background: 'none', border: 'none', color: '#EF4444', cursor: 'pointer' }}
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                ))}
              </div>
            </div>

            {/* Editable Lab Values / Diagnosis */}
            <div style={{ marginBottom: '16px' }}>
              <label className="form-label">Extracted Condition / Diagnosis:</label>
              <input
                type="text"
                value={editedCondition || editedDiagnosis || 'Extracted Clinical Diagnosis'}
                onChange={(e) => setEditedCondition(e.target.value)}
                className="form-control"
              />
            </div>

            <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end', marginTop: '24px' }}>
              <button onClick={() => setStep('UPLOAD')} className="btn btn-secondary">
                Upload Different File
              </button>
              <button onClick={handleSaveToProfile} className="btn btn-green">
                Confirm & Add to Health Profile ✓
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
