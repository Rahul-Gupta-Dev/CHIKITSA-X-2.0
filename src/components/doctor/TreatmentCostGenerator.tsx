import React, { useState } from 'react';
import { financeService } from '../../services/apiServices';
import type { TreatmentCostEstimate } from '../../types';
import { DisclaimerBanner } from '../common/DisclaimerBanner';
import { Calculator, X, Loader2, AlertCircle } from 'lucide-react';

interface Props {
  isOpen: boolean;
  hospitalId?: string;
  hospitalName: string;
  patientId?: string;
  patientName?: string;
  consultationId?: string;
  onClose: () => void;
  onEstimateGenerated: (estimate: TreatmentCostEstimate) => void;
}

export const TreatmentCostGenerator: React.FC<Props> = ({
  isOpen,
  hospitalId = 'hosp-1',
  hospitalName,
  patientId,
  patientName,
  consultationId,
  onClose,
  onEstimateGenerated
}) => {
  const [procedureName, setProcedureName] = useState('Coronary Angiography & Stenting Evaluation');
  const [roomCategory, setRoomCategory] = useState('Semi-Private AC Ward');
  const [procedureCost, setProcedureCost] = useState(65000);
  const [roomCharges, setRoomCharges] = useState(15000);
  const [investigationCost, setInvestigationCost] = useState(12000);
  const [medicationCost, setMedicationCost] = useState(8000);
  const [otherCharges, setOtherCharges] = useState(5000);
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatorError, setGeneratorError] = useState<string | null>(null);

  if (!isOpen) return null;

  const totalCalc = procedureCost + roomCharges + investigationCost + medicationCost + otherCharges;

  const handleGenerate = async () => {
    if (!procedureName.trim()) {
      setGeneratorError('Procedure / treatment name is required.');
      return;
    }

    if (procedureCost < 0 || roomCharges < 0 || investigationCost < 0 || medicationCost < 0 || otherCharges < 0) {
      setGeneratorError('Cost figures cannot be negative numbers.');
      return;
    }

    if (!patientId) {
      setGeneratorError('No patient selected. Please select a patient appointment to associate with this estimate.');
      return;
    }

    setIsGenerating(true);
    setGeneratorError(null);

    const totalMin = Math.round(totalCalc * 0.9);
    const totalMax = Math.round(totalCalc * 1.15);

    try {
      const est = await financeService.createTreatmentEstimate({
        patientId,
        hospitalId,
        hospitalName,
        procedureName: procedureName.trim(),
        roomCategory,
        estimatedCostMin: totalMin,
        estimatedCostMax: totalMax,
        breakdown: {
          procedureCost,
          roomCharges,
          investigationCost,
          medicationCost,
          otherCharges
        },
        consultationId
      });
      onEstimateGenerated(est);
      onClose();
    } catch (err: any) {
      console.error('Failed to create treatment estimate:', err);
      setGeneratorError(err?.message || 'Failed to save treatment cost estimate on server.');
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content" style={{ maxWidth: '640px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{ background: 'linear-gradient(135deg, #10B981 0%, #00B4D8 100%)', padding: '8px', borderRadius: '10px', color: '#FFF' }}>
              <Calculator size={22} />
            </div>
            <div>
              <h3 style={{ fontSize: '1.25rem', color: 'var(--text-heading)', margin: 0 }}>Treatment Cost Estimate Generator</h3>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', margin: 0 }}>
                {patientName ? `Patient: ${patientName} (${patientId})` : 'Indicative cost range for financial planning'}
              </p>
            </div>
          </div>
          <button onClick={onClose} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}>
            <X size={20} />
          </button>
        </div>

        <DisclaimerBanner type="FINANCIAL" text="Treatment costs are indicative estimates based on current hospital procedure tariffs. Final billing depends on actual clinical duration." />

        {generatorError && (
          <div style={{
            background: '#FEF2F2',
            border: '1px solid #FCA5A5',
            borderRadius: '10px',
            padding: '10px 14px',
            color: '#991B1B',
            fontSize: '0.85rem',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            marginBottom: '14px'
          }}>
            <AlertCircle size={16} />
            <span>{generatorError}</span>
          </div>
        )}

        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', marginBottom: '20px' }}>
          <div>
            <label className="form-label">Procedure / Treatment Name:</label>
            <input
              type="text"
              value={procedureName}
              onChange={(e) => setProcedureName(e.target.value)}
              className="form-control"
            />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
            <div>
              <label className="form-label">Room / Bed Category:</label>
              <select value={roomCategory} onChange={(e) => setRoomCategory(e.target.value)} className="form-control">
                <option value="General Ward">General Ward</option>
                <option value="Semi-Private AC Ward">Semi-Private AC Ward</option>
                <option value="Private Deluxe Room">Private Deluxe Room</option>
                <option value="Cardiac ICU">Cardiac ICU</option>
              </select>
            </div>

            <div>
              <label className="form-label">Procedure Charges (₹):</label>
              <input
                type="number"
                min="0"
                value={procedureCost}
                onChange={(e) => setProcedureCost(Math.max(0, Number(e.target.value)))}
                className="form-control"
              />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr', gap: '10px' }}>
            <div>
              <label className="form-label">Room (₹):</label>
              <input
                type="number"
                min="0"
                value={roomCharges}
                onChange={(e) => setRoomCharges(Math.max(0, Number(e.target.value)))}
                className="form-control"
              />
            </div>

            <div>
              <label className="form-label">Investigations (₹):</label>
              <input
                type="number"
                min="0"
                value={investigationCost}
                onChange={(e) => setInvestigationCost(Math.max(0, Number(e.target.value)))}
                className="form-control"
              />
            </div>

            <div>
              <label className="form-label">Medicines (₹):</label>
              <input
                type="number"
                min="0"
                value={medicationCost}
                onChange={(e) => setMedicationCost(Math.max(0, Number(e.target.value)))}
                className="form-control"
              />
            </div>

            <div>
              <label className="form-label">Other (₹):</label>
              <input
                type="number"
                min="0"
                value={otherCharges}
                onChange={(e) => setOtherCharges(Math.max(0, Number(e.target.value)))}
                className="form-control"
              />
            </div>
          </div>
        </div>

        {/* Live Calculation Output Card */}
        <div style={{ background: 'rgba(21, 128, 61, 0.08)', border: '1px solid var(--accent-green)', borderRadius: '14px', padding: '16px', marginBottom: '20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <div style={{ color: 'var(--text-muted)', fontSize: '0.82rem', fontWeight: 600 }}>INDICATIVE ESTIMATED COST RANGE</div>
            <div style={{ fontSize: '1.6rem', fontWeight: 800, color: 'var(--accent-green)', fontFamily: 'Outfit' }}>
              ₹{Math.round(totalCalc * 0.9).toLocaleString()} – ₹{Math.round(totalCalc * 1.15).toLocaleString()}
            </div>
          </div>
          <span className="badge badge-green">INDICATIVE TARIFF</span>
        </div>

        <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
          <button onClick={onClose} disabled={isGenerating} className="btn btn-secondary">
            Cancel
          </button>
          <button onClick={handleGenerate} disabled={isGenerating} className="btn btn-green">
            {isGenerating ? (
              <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Loader2 size={16} className="animate-spin" /> Saving Estimate...
              </span>
            ) : (
              'Save & Pass to Financial Planner ✓'
            )}
          </button>
        </div>
      </div>
    </div>
  );
};
