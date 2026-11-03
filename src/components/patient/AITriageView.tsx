import React, { useState, useEffect } from 'react';
import { triageService, voiceService } from '../../services/apiServices';
import type { TriageResult } from '../../types';
import { db } from '../../db/database';
import { DisclaimerBanner } from '../common/DisclaimerBanner';
import {
  Mic,
  Sparkles,
  ArrowRight,
  CheckCircle2,
  AlertTriangle,
  Edit3,
  PhoneCall
} from 'lucide-react';
import { Button, Card, Badge } from '../common/UIComponents';

interface Props {
  onTriageComplete: (result: TriageResult) => void;
  onNavigateHospitals: () => void;
  onNavigateEmergency: () => void;
}

export const AITriageView: React.FC<Props> = ({
  onTriageComplete,
  onNavigateHospitals,
  onNavigateEmergency
}) => {
  const profile = db.getPatientProfile();
  const latestTriage = db.getLatestTriage();

  const [triage, setTriage] = useState<TriageResult | null>(latestTriage);
  const [isEditing, setIsEditing] = useState<boolean>(!latestTriage);

  useEffect(() => {
    let isMounted = true;
    const fetchLatestTriageFromBackend = async () => {
      try {
        const results = await triageService.getTriageResults();
        if (isMounted && results && results.length > 0) {
          setTriage(results[0]);
          setIsEditing(false);
        }
      } catch {
        // Fall back gracefully to local state if server has no records yet
      }
    };
    fetchLatestTriageFromBackend();
    return () => { isMounted = false; };
  }, []);

  // Form State
  const [symptomText, setSymptomText] = useState<string>(
    profile.symptoms.join(', ') || 'Chest tightness on exertion, mild shortness of breath'
  );
  const [duration, setDuration] = useState<string>('24 Hours');
  const [severity, setSeverity] = useState<'Mild' | 'Moderate' | 'Severe' | 'Critical'>('Moderate');
  const [bodyPart, setBodyPart] = useState<string>('Cardiovascular / Thoracic');

  const [isLoading, setIsLoading] = useState(false);
  const [isListening, setIsListening] = useState(false);

  // Web Speech API Voice Recognition (if supported)
  const handleVoiceInput = () => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert('Speech recognition is not supported in this browser. Please use text input or Chrome/Edge.');
      return;
    }

    try {
      const recognition = new SpeechRecognition();
      recognition.lang = 'en-IN';
      recognition.interimResults = false;

      recognition.onstart = () => setIsListening(true);
      recognition.onend = () => setIsListening(false);
      recognition.onerror = () => setIsListening(false);

      recognition.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript;
        setSymptomText(prev => prev ? `${prev}, ${transcript}` : transcript);
      };

      recognition.start();
    } catch {
      setIsListening(false);
    }
  };

  const handleAnalyzeSymptoms = async () => {
    if (!symptomText.trim()) {
      alert('Please enter or speak your symptoms before analysis.');
      return;
    }

    setIsLoading(true);
    try {
      // 1. Process structured symptom intake
      const intake = await voiceService.processVoiceTranscript(
        `${symptomText}. Duration: ${duration}. Severity: ${severity}. System: ${bodyPart}.`
      );

      // 2. Run clinical triage linked to persisted intake session
      const result = await triageService.runClinicalTriage(undefined, intake?.id);
      setTriage(result);
      setIsEditing(false);
      onTriageComplete(result);
    } catch (err: any) {
      alert('Triage analysis error: ' + (err?.message || 'Please try again.'));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: '960px', margin: '0 auto', padding: '10px 0 40px' }}>
      {/* Header */}
      <div style={{ marginBottom: '20px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
          <Badge variant="teal">CLINICAL TRIAGE</Badge>
          <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>AI-Assisted Urgency Stratification</span>
        </div>
        <h1 style={{ fontSize: '1.75rem', color: 'var(--text-heading)', margin: 0 }}>
          AI Symptom Checker &amp; Care Guidance
        </h1>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', margin: '4px 0 0' }}>
          Evaluate symptoms, assess clinical urgency, and discover the appropriate hospital specialty care.
        </p>
      </div>

      {/* Visible Emergency Notice (Mandatory Safety Rule) */}
      <div
        style={{
          background: 'rgba(220, 38, 38, 0.08)',
          border: '1.5px solid #DC2626',
          borderRadius: '16px',
          padding: '16px 20px',
          marginBottom: '24px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '12px'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ padding: '8px', background: 'rgba(220, 38, 38, 0.15)', borderRadius: '10px', color: '#DC2626' }}>
            <AlertTriangle size={24} />
          </div>
          <div>
            <div style={{ color: '#DC2626', fontWeight: 700, fontSize: '0.98rem' }}>
              EMERGENCY MEDICAL WARNING
            </div>
            <div style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
              If you have crushing chest pain, sudden difficulty breathing, facial drooping, or severe trauma, do not wait for AI output. Call emergency services immediately.
            </div>
          </div>
        </div>

        <Button
          variant="danger"
          size="sm"
          onClick={onNavigateEmergency}
          leftIcon={<PhoneCall size={15} />}
        >
          Call 108 Emergency
        </Button>
      </div>

      {/* INPUT FORM OR RESULTS SCREEN */}
      {isEditing || !triage ? (
        <Card padding="28px">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '18px' }}>
            <h3 style={{ fontSize: '1.25rem', color: 'var(--text-heading)', margin: 0 }}>
              Describe What You Are Experiencing
            </h3>
            {triage && (
              <Button variant="ghost" size="sm" onClick={() => setIsEditing(false)}>
                View Previous Assessment
              </Button>
            )}
          </div>

          {/* Symptom Input (Text + Voice) */}
          <div style={{ marginBottom: '20px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
              <label className="form-label" style={{ margin: 0 }}>Current Symptoms</label>
              <button
                type="button"
                onClick={handleVoiceInput}
                style={{
                  background: isListening ? '#DC2626' : 'var(--bg-subtle)',
                  color: isListening ? '#FFFFFF' : 'var(--primary-teal)',
                  border: '1px solid var(--border-light)',
                  borderRadius: '8px',
                  padding: '4px 10px',
                  fontSize: '0.8rem',
                  fontWeight: 600,
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '6px',
                  cursor: 'pointer'
                }}
              >
                <Mic size={14} />
                {isListening ? 'Listening...' : 'Speak via Mic'}
              </button>
            </div>
            <textarea
              rows={3}
              value={symptomText}
              onChange={e => setSymptomText(e.target.value)}
              placeholder="e.g., I have been feeling chest tightness and mild breathlessness when climbing stairs..."
              className="form-control"
              style={{ resize: 'vertical' }}
            />
          </div>

          {/* Follow-up Context Grid */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '16px', marginBottom: '24px' }}>
            {/* Duration */}
            <div>
              <label className="form-label">Symptom Duration</label>
              <select
                value={duration}
                onChange={e => setDuration(e.target.value)}
                className="form-control"
              >
                <option value="A few hours">Less than 6 Hours</option>
                <option value="12 Hours">12 Hours</option>
                <option value="24 Hours">24 Hours (Since yesterday)</option>
                <option value="2-3 Days">2 to 3 Days</option>
                <option value="1 Week">1 Week or longer</option>
              </select>
            </div>

            {/* Severity */}
            <div>
              <label className="form-label">Severity Level</label>
              <select
                value={severity}
                onChange={e => setSeverity(e.target.value as any)}
                className="form-control"
              >
                <option value="Mild">Mild (Noticeable but does not limit activity)</option>
                <option value="Moderate">Moderate (Interferes with daily routines)</option>
                <option value="Severe">Severe (Disabling or intense)</option>
                <option value="Critical">Critical (Sudden unbearable distress)</option>
              </select>
            </div>

            {/* Body System */}
            <div>
              <label className="form-label">Affected Body System</label>
              <select
                value={bodyPart}
                onChange={e => setBodyPart(e.target.value)}
                className="form-control"
              >
                <option value="Cardiovascular / Thoracic">Cardiovascular (Chest, Heart)</option>
                <option value="Respiratory / ENT">Respiratory (Lungs, Throat, Cough)</option>
                <option value="Gastrointestinal">Digestive / Abdominal</option>
                <option value="Neurological">Neurological (Headache, Dizziness)</option>
                <option value="Musculoskeletal">Joints, Spine &amp; Muscles</option>
                <option value="General">General / Constitutional Malaise</option>
              </select>
            </div>
          </div>

          {/* Action Buttons */}
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
            <Button
              variant="teal"
              size="md"
              isLoading={isLoading}
              onClick={handleAnalyzeSymptoms}
              rightIcon={<Sparkles size={16} />}
            >
              Analyze Symptoms &amp; Stratify Risk
            </Button>
          </div>
        </Card>
      ) : (
        /* READABLE RESULTS SCREEN */
        <div>
          {/* Risk Level & Urgency Card */}
          <Card
            padding="28px"
            style={{
              background:
                triage.riskLevel === 'HIGH'
                  ? 'rgba(220, 38, 38, 0.05)'
                  : triage.riskLevel === 'MODERATE'
                  ? 'rgba(217, 119, 6, 0.05)'
                  : 'rgba(22, 163, 74, 0.05)',
              border: `1.5px solid ${
                triage.riskLevel === 'HIGH'
                  ? '#DC2626'
                  : triage.riskLevel === 'MODERATE'
                  ? '#D97706'
                  : '#16A34A'
              }`,
              marginBottom: '24px'
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '16px', marginBottom: '16px' }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                  <Badge
                    variant={
                      triage.riskLevel === 'HIGH'
                        ? 'red'
                        : triage.riskLevel === 'MODERATE'
                        ? 'amber'
                        : 'green'
                    }
                  >
                    CLINICAL RISK: {triage.riskLevel}
                  </Badge>
                  <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                    Evaluated at {triage.timestamp}
                  </span>
                </div>

                <h2 style={{ fontSize: '1.65rem', color: 'var(--text-heading)', margin: '0 0 6px' }}>
                  Urgency: {triage.urgency}
                </h2>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.94rem', margin: 0 }}>
                  Recommended Specialty Care: <strong style={{ color: 'var(--primary-teal)' }}>{triage.recommendedSpecialty}</strong>
                </p>
              </div>

              <div style={{ display: 'flex', gap: '8px' }}>
                <Button variant="secondary" size="sm" onClick={() => setIsEditing(true)} leftIcon={<Edit3 size={14} />}>
                  Edit Answers
                </Button>
              </div>
            </div>

            {/* Next Action Recommendation */}
            <div
              style={{
                background: 'var(--bg-card)',
                borderRadius: '12px',
                padding: '16px',
                border: '1px solid var(--border-light)',
                marginBottom: '20px'
              }}
            >
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase' }}>
                Recommended Immediate Next Step:
              </div>
              <div style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-heading)', marginTop: '4px' }}>
                {triage.recommendedNextStep}
              </div>
            </div>

            {/* Action CTAs */}
            <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
              {triage.riskLevel === 'HIGH' ? (
                <Button
                  variant="danger"
                  onClick={onNavigateEmergency}
                  leftIcon={<AlertTriangle size={18} />}
                  style={{ flex: 1 }}
                >
                  Launch Emergency Trauma Center Pathway
                </Button>
              ) : (
                <Button
                  variant="teal"
                  onClick={onNavigateHospitals}
                  rightIcon={<ArrowRight size={18} />}
                  style={{ flex: 1 }}
                >
                  Find Recommended {triage.recommendedSpecialty} Hospitals
                </Button>
              )}
            </div>
          </Card>

          {/* Clinical Reasoning Breakdown */}
          <Card padding="24px" style={{ marginBottom: '24px' }}>
            <h3 style={{ fontSize: '1.15rem', color: 'var(--text-heading)', marginBottom: '14px' }}>
              Clinical Triage Reasoning
            </h3>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {triage.clinicalReasoning.map((reason, idx) => (
                <div
                  key={idx}
                  style={{
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: '10px',
                    fontSize: '0.9rem',
                    color: 'var(--text-secondary)'
                  }}
                >
                  <CheckCircle2 size={18} color="var(--primary-teal)" style={{ flexShrink: 0, marginTop: '2px' }} />
                  <span>{reason}</span>
                </div>
              ))}
            </div>

            <div style={{ marginTop: '20px', borderTop: '1px solid var(--border-light)', paddingTop: '14px' }}>
              <h4 style={{ fontSize: '0.85rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '8px' }}>
                Symptoms Evaluated in this Session
              </h4>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                {triage.symptomsConsidered.map((sym, i) => (
                  <span key={i} className="badge badge-purple" style={{ padding: '4px 10px' }}>
                    {sym}
                  </span>
                ))}
              </div>
            </div>
          </Card>

          <DisclaimerBanner text="Important: This AI assessment is for care navigation and triage guidance only. It does not constitute a certified medical diagnosis. Always consult a licensed physician." />
        </div>
      )}
    </div>
  );
};
