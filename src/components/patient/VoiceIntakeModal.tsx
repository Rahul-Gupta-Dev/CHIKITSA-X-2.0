import React, { useState } from 'react';
import { voiceService } from '../../services/apiServices';
import type { SymptomIntake } from '../../types';
import { DisclaimerBanner } from '../common/DisclaimerBanner';
import { Mic, MicOff, Volume2, CheckCircle, Sparkles, X, AlertTriangle, Info } from 'lucide-react';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onIntakeComplete: (intake: SymptomIntake) => void;
}

const DEMO_TRANSCRIPTS = [
  { label: 'Sample Test Scenario 1: Cardiac (Pre-written Template)', text: 'I have been experiencing chest discomfort, mild shortness of breath, and fatigue on walking since yesterday.' },
  { label: 'Sample Test Scenario 2: ENT / Fever (Pre-written Template)', text: 'I have high fever, severe sore throat, and body pain for two days.' },
  { label: 'Sample Test Scenario 3: Neurological (Pre-written Template)', text: 'Feeling persistent dizziness, mild headache, and fatigue after walking upstairs.' }
];

export const VoiceIntakeModal: React.FC<Props> = ({ isOpen, onClose, onIntakeComplete }) => {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [result, setResult] = useState<SymptomIntake | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [recognitionInstance, setRecognitionInstance] = useState<any>(null);

  const handleClose = () => {
    if (recognitionInstance) {
      try { recognitionInstance.stop(); } catch {}
    }
    setIsListening(false);
    setTranscript('');
    setResult(null);
    setStatusMessage(null);
    setErrorMessage(null);
    onClose();
  };

  const handleStartListening = () => {
    setErrorMessage(null);
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      try {
        const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
        const recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = true;
        recognition.lang = 'en-IN';

        recognition.onstart = () => {
          setIsListening(true);
          setStatusMessage('Listening... Speak your symptoms clearly.');
        };

        recognition.onresult = (event: any) => {
          const current = event.resultIndex;
          const text = event.results[current][0].transcript;
          setTranscript(text);
        };

        recognition.onerror = () => {
          setIsListening(false);
          setStatusMessage(null);
          setErrorMessage('Voice recognition is not supported or was denied in this browser. Please type your symptoms or choose a demo transcript.');
        };

        recognition.onend = () => {
          setIsListening(false);
          setStatusMessage(null);
        };

        setRecognitionInstance(recognition);
        recognition.start();
      } catch {
        setIsListening(false);
        setErrorMessage('Voice recognition is not supported in this browser. Please type your symptoms or choose a demo transcript.');
      }
    } else {
      setIsListening(false);
      setErrorMessage('Voice recognition is not supported in this browser. Please type your symptoms or choose a demo transcript.');
    }
  };

  const handleStopListening = () => {
    if (recognitionInstance) {
      try { recognitionInstance.stop(); } catch {}
    }
    setIsListening(false);
    setStatusMessage(null);
  };

  const handleSelectDemoTranscript = (sampleText: string) => {
    setTranscript(sampleText);
    setErrorMessage(null);
    setStatusMessage('Sample scenario loaded into draft box. Click Extract Symptoms to persist to server.');
  };

  const handleProcessIntake = async () => {
    if (!transcript.trim()) {
      setErrorMessage('Please record or enter your symptoms before continuing.');
      return;
    }
    setErrorMessage(null);
    setIsProcessing(true);
    try {
      const intakeData = await voiceService.processVoiceTranscript(transcript);
      setResult(intakeData);
    } catch (err: any) {
      setErrorMessage(err?.message || 'Failed to process clinical intake with server. Please try again.');
    } finally {
      setIsProcessing(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={handleClose}>
      <div className="modal-content" style={{ maxWidth: '640px' }} onClick={e => e.stopPropagation()}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{ background: 'linear-gradient(135deg, #0284C7 0%, #0369A1 100%)', padding: '8px', borderRadius: '10px', color: '#FFF' }}>
              <Mic size={22} />
            </div>
            <div>
              <h3 style={{ fontSize: '1.25rem', margin: 0, color: 'var(--text-heading)' }}>AI Voice Symptom Intake</h3>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem', margin: 0 }}>Speak naturally in your preferred language or type symptoms</p>
            </div>
          </div>
          <button onClick={handleClose} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}>
            <X size={20} />
          </button>
        </div>

        <DisclaimerBanner text="AI-Assisted Intake — Not a Medical Diagnosis. Clinical decisions must be made by a qualified healthcare professional." />

        {!result ? (
          <div style={{ padding: '12px 0' }}>
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', marginBottom: '16px' }}>
              <div
                onClick={isListening ? handleStopListening : handleStartListening}
                className={isListening ? 'mic-pulse' : ''}
                style={{
                  width: '84px',
                  height: '84px',
                  borderRadius: '50%',
                  background: isListening
                    ? 'linear-gradient(135deg, #EF4444 0%, #7C3AED 100%)'
                    : 'linear-gradient(135deg, #00B4D8 0%, #7C3AED 100%)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#FFF',
                  cursor: 'pointer',
                  boxShadow: '0 6px 20px rgba(0, 180, 216, 0.35)',
                  marginBottom: '10px'
                }}
              >
                {isListening ? <MicOff size={32} /> : <Mic size={32} />}
              </div>

              <p style={{ fontSize: '0.9rem', color: isListening ? '#EF4444' : 'var(--text-main)', fontWeight: 600, margin: 0 }}>
                {isListening ? 'Listening... Speak your symptoms clearly.' : 'Click microphone to start voice recording'}
              </p>
            </div>

            {statusMessage && (
              <div style={{ padding: '8px 12px', background: 'rgba(0, 180, 216, 0.12)', border: '1px solid rgba(0, 180, 216, 0.3)', borderRadius: '8px', color: 'var(--primary-teal-dark)', fontSize: '0.82rem', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Info size={14} /> {statusMessage}
              </div>
            )}

            {errorMessage && (
              <div style={{ padding: '10px 14px', background: 'rgba(239, 68, 68, 0.12)', border: '1px solid rgba(239, 68, 68, 0.3)', borderRadius: '8px', color: '#DC2626', fontSize: '0.85rem', marginBottom: '14px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <AlertTriangle size={16} /> {errorMessage}
              </div>
            )}

            <div style={{ background: 'var(--bg-main)', border: '1px solid var(--border-light)', borderRadius: '12px', padding: '12px', marginBottom: '16px' }}>
              <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: '8px', fontWeight: 600 }}>
                TRY DEMO TRANSCRIPTS (CLICK TO TEST DIFFERENT SYMPTOMS):
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                {DEMO_TRANSCRIPTS.map((item, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => handleSelectDemoTranscript(item.text)}
                    className="btn btn-secondary btn-sm"
                    style={{ justifyContent: 'flex-start', fontSize: '0.8rem', textTransform: 'none', textAlign: 'left' }}
                  >
                    <Volume2 size={13} style={{ color: 'var(--primary-teal)', flexShrink: 0 }} />
                    <span style={{ fontWeight: 600, marginRight: '4px' }}>[{item.label.split(':')[0]}]:</span> "{item.text}"
                  </button>
                ))}
              </div>
            </div>

            <div style={{ marginBottom: '18px' }}>
              <label className="form-label">Recognized / Entered Transcript (Editable):</label>
              <textarea
                value={transcript}
                onChange={(e) => {
                  setTranscript(e.target.value);
                  setErrorMessage(null);
                }}
                placeholder="Spoken symptoms will appear here, or type your symptoms directly..."
                rows={3}
                className="form-control"
              />
            </div>

            <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
              <button onClick={onClose} className="btn btn-secondary">
                Cancel
              </button>
              <button
                onClick={handleProcessIntake}
                disabled={isProcessing}
                className="btn btn-purple"
              >
                {isProcessing ? 'Processing AI Intake...' : 'Extract Symptoms & Continue'} <Sparkles size={16} />
              </button>
            </div>
          </div>
        ) : (
          <div>
            <div style={{ background: 'rgba(21, 128, 61, 0.08)', border: '1px solid var(--accent-green)', borderRadius: '14px', padding: '16px', marginBottom: '20px' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--accent-green)', fontWeight: 700, fontSize: '1rem' }}>
                  <CheckCircle size={20} /> AI Clinical Intake Processed
                </div>
                <span className="badge badge-teal" style={{ fontSize: '0.72rem' }}>
                  Persisted to Server (ID: {result.id})
                </span>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', fontSize: '0.88rem', color: 'var(--text-main)', marginTop: '12px' }}>
                <div>
                  <span style={{ color: 'var(--text-muted)' }}>Extracted Symptoms:</span>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', marginTop: '4px' }}>
                    {result.extractedSymptoms.map((sym, i) => (
                      <span key={i} className="badge badge-teal">{sym}</span>
                    ))}
                  </div>
                </div>

                <div>
                  <span style={{ color: 'var(--text-muted)' }}>Duration:</span>
                  <div style={{ fontWeight: 600, marginTop: '4px' }}>{result.duration}</div>
                </div>

                <div>
                  <span style={{ color: 'var(--text-muted)' }}>Severity Level:</span>
                  <div style={{ marginTop: '4px' }}>
                    <span className={`badge ${result.severity === 'Severe' ? 'badge-red' : 'badge-amber'}`}>
                      {result.severity}
                    </span>
                  </div>
                </div>

                <div>
                  <span style={{ color: 'var(--text-muted)' }}>Affected System:</span>
                  <div style={{ fontWeight: 600, marginTop: '4px' }}>{result.affectedBodyPart}</div>
                </div>
              </div>
            </div>

            {result.isEmergencyAlert && (
              <div style={{ background: 'rgba(239, 68, 68, 0.15)', border: '1px solid #EF4444', borderRadius: '12px', padding: '12px', marginBottom: '16px', color: '#DC2626', fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <AlertTriangle size={18} /> High Severity Flag: Immediate cardiac / emergency evaluation is recommended.
              </div>
            )}

            <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
              <button onClick={() => setResult(null)} className="btn btn-secondary">
                Re-record Intake
              </button>
              <button
                onClick={() => {
                  onIntakeComplete(result);
                  onClose();
                }}
                className="btn btn-primary"
              >
                Save & Update Health Profile →
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
