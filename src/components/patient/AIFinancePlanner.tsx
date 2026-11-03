import React, { useState, useEffect } from 'react';
import { financeService } from '../../services/apiServices';
import { db } from '../../db/database';
import { DisclaimerBanner } from '../common/DisclaimerBanner';
import { X, Loader2 } from 'lucide-react';
import type { FinanceScenario } from '../../types';

interface Props {
  isOpen: boolean;
  onClose: () => void;
}

export const AIFinancePlanner: React.FC<Props> = ({ isOpen, onClose }) => {
  const latestCost = db.getLatestCostEstimate();
  const baseCost = latestCost ? latestCost.estimatedCostRange.min : 120000;

  const [scenarios, setScenarios] = useState<FinanceScenario[]>([]);
  const [selectedScenario, setSelectedScenario] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isOpen) return;

    let mounted = true;
    const fetchScenarios = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const [planA, planB, planC] = await Promise.all([
          financeService.generateFinancePlan({
            treatmentCost: baseCost,
            insuranceCoverage: Math.round(baseCost * 0.45)
          }),
          financeService.generateFinancePlan({
            treatmentCost: baseCost,
            insuranceCoverage: Math.round(baseCost * 0.45),
            governmentSupport: Math.round(baseCost * 0.35)
          }),
          financeService.generateFinancePlan({
            treatmentCost: baseCost,
            insuranceCoverage: Math.round(baseCost * 0.45),
            governmentSupport: Math.round(baseCost * 0.35),
            ngoSupport: Math.round(baseCost * 0.20)
          })
        ]);

        if (mounted) {
          const loaded: FinanceScenario[] = [
            {
              ...planA,
              id: 'scen-a',
              scenarioTitle: 'Scenario A: Empaneled Tertiary Hospital (Insurance Only)'
            },
            {
              ...planB,
              id: 'scen-b',
              scenarioTitle: 'Scenario B: Gov Scheme + Insurance Optimized Plan'
            },
            {
              ...planC,
              id: 'scen-c',
              scenarioTitle: 'Scenario C: Comprehensive Aid (Gov Scheme + NGO Grant)'
            }
          ];
          setScenarios(loaded);
          setSelectedScenario(loaded[0]?.id || '');
        }
      } catch (err: any) {
        if (mounted) {
          setError(err?.message || 'Failed to calculate backend financial scenarios.');
        }
      } finally {
        if (mounted) setIsLoading(false);
      }
    };

    fetchScenarios();
    return () => { mounted = false; };
  }, [isOpen, baseCost]);

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" style={{ maxWidth: '850px' }} onClick={e => e.stopPropagation()}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <div>
            <span className="badge badge-purple">AI SCENARIO PLANNER</span>
            <h3 style={{ color: 'var(--text-heading)', fontSize: '1.4rem', margin: '4px 0 0' }}>Care-to-Cost AI Finance Scenario Comparison</h3>
          </div>
          <button onClick={onClose} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', fontSize: '1.4rem', cursor: 'pointer' }}>
            <X size={20} />
          </button>
        </div>

        <DisclaimerBanner type="FINANCIAL" text="Financial figures are computed via verified backend policy calculations and hospital tariff algorithms." />

        {isLoading ? (
          <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
            <Loader2 size={32} className="animate-spin" style={{ margin: '0 auto 12px', color: 'var(--primary-teal)' }} />
            <p>Evaluating real financial benefits against backend policies...</p>
          </div>
        ) : error ? (
          <div style={{ padding: '16px', background: '#FEF2F2', border: '1px solid #FCA5A5', color: '#991B1B', borderRadius: '12px', margin: '20px 0' }}>
            {error}
          </div>
        ) : (
          /* Scenarios Grid */
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '16px', margin: '20px 0' }}>
            {scenarios.map((scen) => {
              const isSelected = selectedScenario === scen.id;

              return (
                <div
                  key={scen.id}
                  onClick={() => setSelectedScenario(scen.id)}
                  style={{
                    background: isSelected ? 'rgba(2, 132, 199, 0.08)' : 'var(--bg-subtle)',
                    border: `2px solid ${isSelected ? 'var(--primary-teal)' : 'var(--border-light)'}`,
                    borderRadius: '16px',
                    padding: '20px',
                    cursor: 'pointer',
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'space-between',
                    transition: 'transform 0.2s'
                  }}
                >
                  <div>
                    <span className={`badge ${scen.remainingGap === 0 ? 'badge-green' : 'badge-teal'}`} style={{ marginBottom: '8px' }}>
                      {scen.recommendationTag}
                    </span>
                    <h4 style={{ color: 'var(--text-heading)', fontSize: '1.05rem', margin: '6px 0 12px' }}>{scen.scenarioTitle}</h4>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', fontSize: '0.84rem', color: 'var(--text-main)', marginBottom: '16px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span style={{ color: 'var(--text-muted)' }}>Estimated Cost:</span>
                        <strong style={{ color: 'var(--text-heading)' }}>₹{scen.estimatedCost.toLocaleString()}</strong>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span style={{ color: 'var(--text-muted)' }}>Insurance:</span>
                        <span style={{ color: 'var(--primary-teal-dark)', fontWeight: 600 }}>-₹{scen.insuranceBenefit.toLocaleString()}</span>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span style={{ color: 'var(--text-muted)' }}>Gov Scheme:</span>
                        <span style={{ color: 'var(--accent-green)', fontWeight: 600 }}>-₹{scen.governmentBenefit.toLocaleString()}</span>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span style={{ color: 'var(--text-muted)' }}>NGO Aid:</span>
                        <span style={{ color: 'var(--accent-purple)', fontWeight: 600 }}>-₹{scen.ngoBenefit.toLocaleString()}</span>
                      </div>
                    </div>
                  </div>

                  <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-light)', padding: '10px 12px', borderRadius: '10px', marginTop: 'auto' }}>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600 }}>NET PATIENT OUT-OF-POCKET GAP:</div>
                    <div style={{ fontSize: '1.3rem', fontWeight: 800, color: scen.remainingGap === 0 ? 'var(--accent-green)' : 'var(--warning-amber)', fontFamily: 'Outfit' }}>
                      ₹{scen.remainingGap.toLocaleString()}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Savings Insight Banner */}
        <div style={{ background: 'rgba(21, 128, 61, 0.1)', border: '1px solid var(--accent-green)', borderRadius: '14px', padding: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
          <div>
            <div style={{ color: 'var(--accent-green)', fontWeight: 700, fontSize: '0.95rem' }}>
              💡 Out-of-Pocket Affordability Guidance
            </div>
            <div style={{ color: 'var(--text-main)', fontSize: '0.82rem', marginTop: '2px' }}>
              Combining PM-JAY / State Health Cards with empaneled hospital tiering can reduce net patient expense to zero.
            </div>
          </div>
          <button className="btn btn-secondary" onClick={onClose} style={{ fontSize: '0.82rem' }}>
            Close Comparison
          </button>
        </div>
      </div>
    </div>
  );
};
