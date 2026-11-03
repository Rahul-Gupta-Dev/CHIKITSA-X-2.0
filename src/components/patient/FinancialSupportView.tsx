import React, { useState, useEffect } from 'react';
import { financeService, mockFinanceService } from '../../services/apiServices';
import { db } from '../../db/database';
import type { GovernmentScheme, NGOSupport, InsurancePolicy, TreatmentCostEstimate, CareToCostAssessment } from '../../types';
import { DisclaimerBanner } from '../common/DisclaimerBanner';
import {
  ShieldCheck,
  HeartHandshake,
  CheckCircle2,
  Layers,
  Search,
  ExternalLink,
  Phone,
  HelpCircle,
  Loader2,
  AlertCircle,
  FileText
} from 'lucide-react';
import { Button, Card, Badge } from '../common/UIComponents';

interface Props {
  onOpenPlanner: () => void;
}

export const FinancialSupportView: React.FC<Props> = ({ onOpenPlanner }) => {
  const profile = db.getPatientProfile();

  const [estimatedCost, setEstimatedCost] = useState<number>(120000);
  const [selectedEstimate, setSelectedEstimate] = useState<TreatmentCostEstimate | null>(null);

  const [activeDirectoryTab, setActiveDirectoryTab] = useState<'SCHEMES' | 'INSURANCE' | 'NGO'>('SCHEMES');
  const [searchQuery, setSearchQuery] = useState('');

  // Live gap calculation state
  const [insuranceAmount] = useState(60000);
  const [govSchemeAmount] = useState(30000);
  const [ngoAmount, setNgoAmount] = useState(15000);
  const [selfPayAmount, setSelfPayAmount] = useState(15000);

  const [isInsuranceApplied, setIsInsuranceApplied] = useState(true);
  const [isSchemeApplied, setIsSchemeApplied] = useState(true);

  // Backend Data State
  const [govSchemes, setGovSchemes] = useState<GovernmentScheme[]>([]);
  const [insurancePolicies, setInsurancePolicies] = useState<InsurancePolicy[]>([]);
  const [ngoList, setNgoList] = useState<NGOSupport[]>([]);
  const [treatmentEstimates, setTreatmentEstimates] = useState<TreatmentCostEstimate[]>([]);
  const [savedAssessments, setSavedAssessments] = useState<CareToCostAssessment[]>([]);

  const [isLoadingData, setIsLoadingData] = useState<boolean>(true);
  const [dataError, setDataError] = useState<string | null>(null);

  const [isSaving, setIsSaving] = useState<boolean>(false);
  const [saveMessage, setSaveMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Detail Modal State
  const [viewingScheme, setViewingScheme] = useState<GovernmentScheme | null>(null);
  const [viewingNGO, setViewingNGO] = useState<NGOSupport | null>(null);

  // Eligibility Checker Questionnaire State
  const [showEligibilityModal, setShowEligibilityModal] = useState(false);
  const [rationCardInput, setRationCardInput] = useState<string>(profile.rationCardType || 'BPL');
  const [annualIncomeInput, setAnnualIncomeInput] = useState<string>('UNDER_2_5_LAKH');
  const [eligibilityResult, setEligibilityResult] = useState<string | null>(null);

  const schemeEligibility = mockFinanceService.checkGovSchemeEligibility();

  // Load backend financial data
  const loadFinancialData = async () => {
    setIsLoadingData(true);
    setDataError(null);
    try {
      const [schemes, policies, ngos, estimates, assessments] = await Promise.allSettled([
        financeService.getGovSchemes(),
        financeService.getPatientInsurance(),
        financeService.getNGOSupport(),
        financeService.getTreatmentEstimatesForPatient(),
        financeService.getPatientAssessments()
      ]);

      if (schemes.status === 'fulfilled' && schemes.value.length > 0) {
        setGovSchemes(schemes.value);
      } else {
        setGovSchemes(db.getGovSchemes());
      }

      if (policies.status === 'fulfilled' && policies.value.length > 0) {
        setInsurancePolicies(policies.value as any);
      } else {
        setInsurancePolicies(db.getInsurancePolicies());
      }

      if (ngos.status === 'fulfilled' && ngos.value.length > 0) {
        setNgoList(ngos.value);
      } else {
        setNgoList(db.getNGOSupport());
      }

      if (estimates.status === 'fulfilled' && estimates.value.length > 0) {
        setTreatmentEstimates(estimates.value);
        setSelectedEstimate(estimates.value[0]);
        setEstimatedCost(estimates.value[0].estimatedCostRange.min);
      } else {
        const localEst = db.getLatestCostEstimate();
        if (localEst) {
          setEstimatedCost(localEst.estimatedCostRange.min);
        }
      }

      if (assessments.status === 'fulfilled') {
        setSavedAssessments(assessments.value);
      }
    } catch (err: any) {
      console.warn('Could not fully synchronize financial directory:', err);
      setDataError('Some financial directory items could not be loaded from the live server.');
      setGovSchemes(db.getGovSchemes());
      setInsurancePolicies(db.getInsurancePolicies());
      setNgoList(db.getNGOSupport());
    } finally {
      setIsLoadingData(false);
    }
  };

  useEffect(() => {
    loadFinancialData();
  }, []);

  const totalFunding =
    (isInsuranceApplied ? insuranceAmount : 0) +
    (isSchemeApplied ? govSchemeAmount : 0) +
    ngoAmount +
    selfPayAmount;

  const financialGap = Math.max(0, estimatedCost - totalFunding);

  const handleApplyNGO = (ngoId: string) => {
    db.updateNGOStatus(ngoId, 'APPLIED');
    setNgoAmount(ngoAmount + 10000);
    alert('Philanthropic financial grant request dispatched to the NGO desk.');
  };

  const handleSaveAssessment = async () => {
    setIsSaving(true);
    setSaveMessage(null);
    try {
      const saved = await financeService.assessCareToCost({
        treatmentCost: estimatedCost,
        insuranceCoverage: isInsuranceApplied ? insuranceAmount : 0,
        governmentSupport: isSchemeApplied ? govSchemeAmount : 0,
        ngoAssistance: ngoAmount,
        patientSelfContribution: selfPayAmount,
        hasInsurance: isInsuranceApplied,
        rationCardType: rationCardInput
      });

      setSaveMessage({
        type: 'success',
        text: `Care-to-Cost Plan saved and persisted to SQLite (ID: ${saved.id})!`
      });

      // Refresh saved assessments
      try {
        const fresh = await financeService.getPatientAssessments();
        setSavedAssessments(fresh);
      } catch {
        // ignore
      }
    } catch (err: any) {
      console.error('Failed to save assessment:', err);
      setSaveMessage({
        type: 'error',
        text: err?.message || 'Failed to save financial assessment on server. Please check your connection and login.'
      });
    } finally {
      setIsSaving(false);
    }
  };

  const handleRunEligibilityTest = () => {
    const isEligible = rationCardInput === 'BPL' || rationCardInput === 'AAY' || annualIncomeInput === 'UNDER_2_5_LAKH';
    if (isEligible) {
      setEligibilityResult('ELIGIBLE');
      db.updatePatientProfile({ rationCardType: rationCardInput as any, hasGovernmentCard: true });
    } else {
      setEligibilityResult('INELIGIBLE');
    }
  };

  return (
    <div style={{ maxWidth: '1100px', margin: '0 auto', padding: '10px 0 40px' }}>
      {/* Page Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px', marginBottom: '20px' }}>
        <div>
          <Badge variant="green">FINANCIAL ASSISTANCE &amp; FINTECH</Badge>
          <h1 style={{ fontSize: '1.75rem', color: 'var(--text-heading)', margin: '4px 0 0' }}>
            Care-to-Cost &amp; Financial Protection Platform
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', margin: '4px 0 0' }}>
            Bridge your medical treatment expenditure by combining private insurance, Ayushman Bharat PM-JAY, state schemes, and philanthropic NGO grants.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '10px' }}>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowEligibilityModal(true)}
            leftIcon={<HelpCircle size={15} />}
          >
            Check Scheme Eligibility
          </Button>
          <Button
            variant="teal"
            size="sm"
            onClick={onOpenPlanner}
            leftIcon={<Layers size={16} />}
          >
            AI Finance Scenario Planner
          </Button>
        </div>
      </div>

      <DisclaimerBanner
        type="FINANCIAL"
        text="All healthcare scheme eligibility criteria, insurance cashless pre-authorizations, and NGO grants are indicative assessments. Official empanelment terms apply."
      />

      {isLoadingData && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '12px 16px', borderRadius: '10px', background: 'var(--bg-subtle)', marginBottom: '16px', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
          <Loader2 size={16} className="animate-spin" />
          <span>Synchronizing live financial directories and treatment estimates from database...</span>
        </div>
      )}

      {dataError && (
        <div style={{ background: '#FEF3C7', border: '1px solid #F59E0B', color: '#92400E', padding: '10px 14px', borderRadius: '10px', fontSize: '0.85rem', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <AlertCircle size={16} />
          <span>{dataError}</span>
        </div>
      )}

      {/* DOCTOR ESTIMATES SECTION (If Available from Backend) */}
      {treatmentEstimates.length > 0 && (
        <Card padding="20px 24px" style={{ marginBottom: '20px', border: '1px solid var(--border-light)', background: 'rgba(2, 132, 199, 0.04)' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '10px', marginBottom: '12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <FileText size={18} color="var(--primary-teal)" />
              <h3 style={{ fontSize: '1.05rem', color: 'var(--text-heading)', margin: 0 }}>
                Doctor's Treatment Cost Estimates ({treatmentEstimates.length})
              </h3>
            </div>
            <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
              Source: Hospital Clinical Tariff Database
            </span>
          </div>

          <div style={{ display: 'flex', gap: '12px', overflowX: 'auto', paddingBottom: '6px' }}>
            {treatmentEstimates.map(est => {
              const isSelected = selectedEstimate?.id === est.id;
              return (
                <div
                  key={est.id}
                  onClick={() => {
                    setSelectedEstimate(est);
                    setEstimatedCost(est.estimatedCostRange.min);
                  }}
                  style={{
                    minWidth: '260px',
                    padding: '12px 16px',
                    borderRadius: '12px',
                    background: isSelected ? 'var(--bg-card)' : 'var(--bg-subtle)',
                    border: `2px solid ${isSelected ? 'var(--primary-teal)' : 'var(--border-light)'}`,
                    cursor: 'pointer',
                    transition: 'all 0.2s'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                    <span style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-muted)' }}>{est.roomCategory}</span>
                    <Badge variant={isSelected ? 'teal' : 'gray'} size="sm">
                      {isSelected ? 'Active Selection' : 'Click to Apply'}
                    </Badge>
                  </div>
                  <strong style={{ fontSize: '0.92rem', color: 'var(--text-heading)', display: 'block', marginBottom: '6px' }}>
                    {est.procedureName}
                  </strong>
                  <div style={{ fontSize: '1.15rem', fontWeight: 800, color: 'var(--accent-green)', fontFamily: 'Outfit' }}>
                    ₹{est.estimatedCostRange.min.toLocaleString()} – ₹{est.estimatedCostRange.max.toLocaleString()}
                  </div>
                </div>
              );
            })}
          </div>
        </Card>
      )}

      {/* 1. INTERACTIVE LIVE CARE-TO-COST FINANCIAL GAP CARD */}
      <Card
        padding="28px"
        style={{
          border: '1.5px solid var(--primary-teal)',
          marginBottom: '32px',
          background: 'var(--bg-card)'
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', flexWrap: 'wrap', gap: '12px' }}>
          <div>
            <span style={{ color: 'var(--text-muted)', fontSize: '0.82rem', fontWeight: 600, textTransform: 'uppercase' }}>
              Estimated Treatment Cost
            </span>
            <div style={{ fontSize: '2.2rem', fontWeight: 800, color: 'var(--text-heading)', fontFamily: 'Outfit' }}>
              ₹{estimatedCost.toLocaleString()}
            </div>
            <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
              Based on {selectedEstimate?.procedureName || 'Cardiology Angioplasty & Stenting'}
            </span>
          </div>

          <div style={{ textAlign: 'right' }}>
            <span style={{ color: 'var(--text-muted)', fontSize: '0.82rem', fontWeight: 600, textTransform: 'uppercase' }}>
              Remaining Out-of-Pocket Gap
            </span>
            <div
              style={{
                fontSize: '2.2rem',
                fontWeight: 800,
                color: financialGap === 0 ? '#16A34A' : '#D97706',
                fontFamily: 'Outfit'
              }}
            >
              ₹{financialGap.toLocaleString()}
            </div>
            {financialGap === 0 ? (
              <span className="badge badge-green">✓ 100% FUNDED — ZERO GAP</span>
            ) : (
              <span className="badge badge-amber">REMAINING EXPOSURE</span>
            )}
          </div>
        </div>

        {/* Live Formula Stack Breakdown */}
        <div
          style={{
            background: 'var(--bg-subtle)',
            border: '1px solid var(--border-light)',
            borderRadius: '16px',
            padding: '20px',
            marginBottom: '20px'
          }}
        >
          <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: '14px', fontWeight: 700 }}>
            Dynamic Care-to-Cost Subsidy Stack:
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(190px, 1fr))', gap: '12px', textAlign: 'center' }}>
            <div style={{ background: 'var(--bg-card)', border: '1px solid var(--primary-teal)', borderRadius: '12px', padding: '12px' }}>
              <div style={{ color: 'var(--primary-teal)', fontSize: '0.78rem', fontWeight: 700 }}>1. Cashless Insurance</div>
              <div style={{ color: 'var(--text-heading)', fontWeight: 800, fontSize: '1.25rem', marginTop: '2px' }}>
                ₹{(isInsuranceApplied ? insuranceAmount : 0).toLocaleString()}
              </div>
              <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Indicative Policy Coverage</span>
            </div>

            <div style={{ background: 'var(--bg-card)', border: '1px solid #16A34A', borderRadius: '12px', padding: '12px' }}>
              <div style={{ color: '#16A34A', fontSize: '0.78rem', fontWeight: 700 }}>2. PM-JAY / State Subsidy</div>
              <div style={{ color: 'var(--text-heading)', fontWeight: 800, fontSize: '1.25rem', marginTop: '2px' }}>
                ₹{(isSchemeApplied ? govSchemeAmount : 0).toLocaleString()}
              </div>
              <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Ayushman Bharat BPL (Estimated)</span>
            </div>

            <div style={{ background: 'var(--bg-card)', border: '1px solid #7C3AED', borderRadius: '12px', padding: '12px' }}>
              <div style={{ color: '#7C3AED', fontSize: '0.78rem', fontWeight: 700 }}>3. Philanthropic NGO Grants</div>
              <div style={{ color: 'var(--text-heading)', fontWeight: 800, fontSize: '1.25rem', marginTop: '2px' }}>
                ₹{ngoAmount.toLocaleString()}
              </div>
              <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Philanthropic Support (Subject to Review)</span>
            </div>

            <div style={{ background: 'var(--bg-card)', border: '1px solid #D97706', borderRadius: '12px', padding: '12px' }}>
              <div style={{ color: '#D97706', fontSize: '0.78rem', fontWeight: 700 }}>4. Patient Contribution</div>
              <div style={{ color: 'var(--text-heading)', fontWeight: 800, fontSize: '1.25rem', marginTop: '2px' }}>
                ₹{selfPayAmount.toLocaleString()}
              </div>
              <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Self / Family Co-Pay</span>
            </div>
          </div>

          {/* Interactive Self-Pay Slider */}
          <div style={{ marginTop: '20px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-main)', fontSize: '0.85rem', marginBottom: '6px' }}>
              <span>Simulate Patient Out-of-Pocket Contribution:</span>
              <strong style={{ color: '#D97706' }}>₹{selfPayAmount.toLocaleString()}</strong>
            </div>
            <input
              type="range"
              min="0"
              max="50000"
              step="1000"
              value={selfPayAmount}
              onChange={e => setSelfPayAmount(Number(e.target.value))}
              style={{ width: '100%', accentColor: 'var(--primary-teal)', cursor: 'pointer' }}
            />
          </div>
        </div>

        {saveMessage && (
          <div style={{
            padding: '12px 16px',
            borderRadius: '10px',
            fontSize: '0.86rem',
            marginBottom: '16px',
            background: saveMessage.type === 'success' ? '#ECFDF5' : '#FEF2F2',
            border: `1px solid ${saveMessage.type === 'success' ? '#A7F3D0' : '#FCA5A5'}`,
            color: saveMessage.type === 'success' ? '#065F46' : '#991B1B',
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}>
            {saveMessage.type === 'success' ? <CheckCircle2 size={16} /> : <AlertCircle size={16} />}
            <span>{saveMessage.text}</span>
          </div>
        )}

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '10px' }}>
          <div style={{ display: 'flex', gap: '16px', fontSize: '0.84rem' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={isInsuranceApplied}
                onChange={e => setIsInsuranceApplied(e.target.checked)}
                style={{ width: '16px', height: '16px', accentColor: 'var(--primary-teal)' }}
              />
              <span>Include Insurance Pre-Auth</span>
            </label>
            <label style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={isSchemeApplied}
                onChange={e => setIsSchemeApplied(e.target.checked)}
                style={{ width: '16px', height: '16px', accentColor: '#16A34A' }}
              />
              <span>Include PM-JAY Scheme</span>
            </label>
          </div>

          <Button
            variant="teal"
            onClick={handleSaveAssessment}
            disabled={isSaving}
            leftIcon={isSaving ? <Loader2 size={16} className="animate-spin" /> : <CheckCircle2 size={16} />}
          >
            {isSaving ? 'Persisting Plan...' : 'Save Financial Plan to Profile'}
          </Button>
        </div>

        {/* PREVIOUS SAVED ASSESSMENTS */}
        {savedAssessments.length > 0 && (
          <div style={{ marginTop: '20px', borderTop: '1px solid var(--border-light)', paddingTop: '16px' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Persisted Profile Plans ({savedAssessments.length})
            </span>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginTop: '10px' }}>
              {savedAssessments.slice(0, 3).map(a => (
                <div
                  key={a.id}
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    background: 'var(--bg-subtle)',
                    padding: '10px 14px',
                    borderRadius: '8px',
                    fontSize: '0.84rem'
                  }}
                >
                  <div>
                    <strong>{a.hospitalName}</strong> • Treatment: ₹{a.estimatedTreatmentCost.toLocaleString()}
                    <span style={{ color: 'var(--text-muted)', marginLeft: '8px', fontSize: '0.78rem' }}>{a.calculatedAt}</span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ color: a.financialGap === 0 ? '#16A34A' : '#D97706', fontWeight: 700 }}>
                      Gap: ₹{a.financialGap.toLocaleString()}
                    </span>
                    <Badge variant={a.isFundingComplete ? 'green' : 'amber'} size="sm">
                      {a.isFundingComplete ? '100% Funded' : 'Partial Gap'}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </Card>

      {/* 2. SEARCHABLE FINANCIAL AID DIRECTORY */}
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '12px' }}>
          <div>
            <h2 style={{ fontSize: '1.35rem', color: 'var(--text-heading)', margin: 0 }}>
              Searchable Financial Aid Directory
            </h2>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.86rem', margin: '2px 0 0' }}>
              Informational listings of Government Schemes, Insurance policies, and Philanthropic NGOs
            </p>
          </div>

          {/* Directory Tabs */}
          <div style={{ display: 'flex', gap: '6px', background: 'var(--bg-subtle)', padding: '3px', borderRadius: '10px' }}>
            <button
              onClick={() => setActiveDirectoryTab('SCHEMES')}
              className={`btn btn-sm ${activeDirectoryTab === 'SCHEMES' ? 'btn-primary' : 'btn-ghost'}`}
              style={{ minHeight: '32px', fontSize: '0.82rem' }}
            >
              Gov Schemes ({govSchemes.length})
            </button>
            <button
              onClick={() => setActiveDirectoryTab('INSURANCE')}
              className={`btn btn-sm ${activeDirectoryTab === 'INSURANCE' ? 'btn-primary' : 'btn-ghost'}`}
              style={{ minHeight: '32px', fontSize: '0.82rem' }}
            >
              Insurance Policies ({insurancePolicies.length})
            </button>
            <button
              onClick={() => setActiveDirectoryTab('NGO')}
              className={`btn btn-sm ${activeDirectoryTab === 'NGO' ? 'btn-primary' : 'btn-ghost'}`}
              style={{ minHeight: '32px', fontSize: '0.82rem' }}
            >
              NGO Grants ({ngoList.length})
            </button>
          </div>
        </div>

        {/* Search Bar */}
        <div style={{ position: 'relative', marginBottom: '16px' }}>
          <Search size={16} color="var(--text-muted)" style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)' }} />
          <input
            type="text"
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            placeholder="Search by program name, organization, or eligibility condition..."
            className="form-control"
            style={{ paddingLeft: '36px', height: '40px', fontSize: '0.9rem' }}
          />
        </div>

        {/* 2A. GOVERNMENT SCHEMES LIST */}
        {activeDirectoryTab === 'SCHEMES' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <div style={{ background: 'var(--bg-subtle)', padding: '10px 14px', borderRadius: '8px', fontSize: '0.82rem', color: 'var(--text-muted)', border: '1px solid var(--border-light)' }}>
              ℹ️ <strong>Directory Disclosure:</strong> Listed schemes are informational. Eligibility determination and actual benefit approvals are subject to official verification by government nodal authorities upon physical document scrutiny.
            </div>
            {govSchemes
              .filter(s => !searchQuery || s.schemeName.toLowerCase().includes(searchQuery.toLowerCase()) || s.description.toLowerCase().includes(searchQuery.toLowerCase()))
              .map(s => {
                const matchInfo = schemeEligibility.find(se => se.schemeId === s.id);
                const isEligible = matchInfo?.isEligible ?? true;

                return (
                  <Card key={s.id} padding="20px 24px">
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '12px', marginBottom: '10px' }}>
                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600 }}>{s.schemeCode}</span>
                          <Badge variant={isEligible ? 'green' : 'amber'} size="sm">
                            {isEligible ? 'Potential Fit on Record' : 'Verification Required'}
                          </Badge>
                        </div>
                        <h3 style={{ fontSize: '1.2rem', color: 'var(--text-heading)', margin: 0 }}>
                          {s.schemeName}
                        </h3>
                        <p style={{ color: 'var(--text-secondary)', fontSize: '0.86rem', margin: '4px 0 0', maxWidth: '700px' }}>
                          {s.description}
                        </p>
                      </div>

                      <div style={{ textAlign: 'right' }}>
                        <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Indicative Maximum Benefit</span>
                        <div style={{ fontSize: '1.3rem', fontWeight: 800, color: '#16A34A' }}>
                          Up to ₹{s.maxBenefitAmount.toLocaleString()}
                        </div>
                      </div>
                    </div>

                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '10px', borderTop: '1px solid var(--border-light)', paddingTop: '12px' }}>
                      <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
                        <Phone size={13} style={{ display: 'inline', marginRight: '4px' }} /> Helpline: <strong>{s.contactHelpline}</strong>
                      </div>

                      <div style={{ display: 'flex', gap: '8px' }}>
                        <Button variant="secondary" size="sm" onClick={() => setViewingScheme(s)}>
                          View Details &amp; Docs
                        </Button>
                        <a
                          href="https://beneficiary.nha.gov.in/"
                          target="_blank"
                          rel="noreferrer"
                          style={{ textDecoration: 'none' }}
                        >
                          <Button variant="teal" size="sm" rightIcon={<ExternalLink size={13} />}>
                            Apply on Official Portal
                          </Button>
                        </a>
                      </div>
                    </div>
                  </Card>
                );
              })}
          </div>
        )}

        {/* 2B. INSURANCE POLICIES LIST */}
        {activeDirectoryTab === 'INSURANCE' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <div style={{ background: 'var(--bg-subtle)', padding: '10px 14px', borderRadius: '8px', fontSize: '0.82rem', color: 'var(--text-muted)', border: '1px solid var(--border-light)' }}>
              ℹ️ <strong>Insurance Disclosure:</strong> Cashless coverage is subject to insurer pre-authorization at hospital admission based on policy terms, waiting periods, and deductibles.
            </div>
            {insurancePolicies.length === 0 ? (
              <div style={{ padding: '30px', textAlign: 'center', color: 'var(--text-muted)' }}>
                No active insurance policies linked to this patient profile.
              </div>
            ) : (
              insurancePolicies
                .filter(p => !searchQuery || p.providerName.toLowerCase().includes(searchQuery.toLowerCase()) || p.policyNumber.toLowerCase().includes(searchQuery.toLowerCase()))
                .map(p => (
                  <Card key={p.id} padding="20px 24px">
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                          <ShieldCheck size={18} color="var(--primary-teal)" />
                          <h3 style={{ fontSize: '1.15rem', color: 'var(--text-heading)', margin: 0 }}>
                            {p.providerName}
                          </h3>
                          <Badge variant="green" size="sm">{p.status}</Badge>
                        </div>
                        <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', margin: 0 }}>
                          Policy Number: <strong>{p.policyNumber}</strong> • Cashless Hospital Network: <strong>Active</strong>
                        </p>
                      </div>

                      <div style={{ textAlign: 'right' }}>
                        <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Sum Insured</span>
                        <div style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--primary-teal)' }}>
                          ₹{p.sumInsured.toLocaleString()}
                        </div>
                        <span style={{ fontSize: '0.75rem', color: '#16A34A' }}>Available: ₹{p.availableBalance.toLocaleString()}</span>
                      </div>
                    </div>
                  </Card>
                ))
            )}
          </div>
        )}

        {/* 2C. NGO & PHILANTHROPIC GRANTS */}
        {activeDirectoryTab === 'NGO' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <div style={{ background: 'var(--bg-subtle)', padding: '10px 14px', borderRadius: '8px', fontSize: '0.82rem', color: 'var(--text-muted)', border: '1px solid var(--border-light)' }}>
              ℹ️ <strong>Philanthropic Disclosure:</strong> NGO financial assistance is disbursed by independent foundations following case evaluation. Submitting a request initiates informational referral.
            </div>
            {ngoList
              .filter(n => !searchQuery || n.organizationName.toLowerCase().includes(searchQuery.toLowerCase()) || n.supportType.toLowerCase().includes(searchQuery.toLowerCase()))
              .map(n => (
                <Card key={n.id} padding="20px 24px">
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '12px', marginBottom: '10px' }}>
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                        <HeartHandshake size={18} color="#7C3AED" />
                        <h3 style={{ fontSize: '1.2rem', color: 'var(--text-heading)', margin: 0 }}>
                          {n.organizationName}
                        </h3>
                        <Badge variant="purple" size="sm">{n.supportType}</Badge>
                      </div>
                      <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', margin: 0, maxWidth: '680px' }}>
                        {n.eligibilityDescription}
                      </p>
                    </div>

                    <div style={{ textAlign: 'right' }}>
                      <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Maximum Grant</span>
                      <div style={{ fontSize: '1.25rem', fontWeight: 800, color: '#7C3AED' }}>
                        Up to ₹{n.maxAssistanceAmount.toLocaleString()}
                      </div>
                    </div>
                  </div>

                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: '1px solid var(--border-light)', paddingTop: '10px' }}>
                    <Button variant="ghost" size="sm" onClick={() => setViewingNGO(n)}>
                      View Required Documents
                    </Button>

                    <Button
                      variant="teal"
                      size="sm"
                      disabled={n.applicationStatus === 'APPLIED'}
                      onClick={() => handleApplyNGO(n.id)}
                    >
                      {n.applicationStatus === 'APPLIED' ? '✓ Referral Initiated' : 'Request NGO Referral'}
                    </Button>
                  </div>
                </Card>
              ))}
          </div>
        )}
      </div>

      {/* SCHEME DETAIL MODAL */}
      {viewingScheme && (
        <div className="modal-overlay" onClick={() => setViewingScheme(null)}>
          <div className="modal-content" style={{ maxWidth: '600px', padding: '24px' }} onClick={e => e.stopPropagation()}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <div>
                <Badge variant="green">{viewingScheme.schemeCode}</Badge>
                <h3 style={{ margin: '4px 0 0', color: 'var(--text-heading)', fontSize: '1.3rem' }}>
                  {viewingScheme.schemeName}
                </h3>
              </div>
              <button onClick={() => setViewingScheme(null)} style={{ background: 'none', border: 'none', fontSize: '1.4rem', cursor: 'pointer', color: 'var(--text-muted)' }}>
                ×
              </button>
            </div>

            <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '16px' }}>
              {viewingScheme.description}
            </p>

            <div style={{ background: 'var(--bg-subtle)', borderRadius: '12px', padding: '16px', marginBottom: '16px', fontSize: '0.86rem' }}>
              <div style={{ marginBottom: '8px' }}>
                <span style={{ color: 'var(--text-muted)' }}>Eligible Ration Categories:</span> <strong>{viewingScheme.eligibilityCriteria.rationCardTypes.join(', ')}</strong>
              </div>
              <div style={{ marginBottom: '8px' }}>
                <span style={{ color: 'var(--text-muted)' }}>Income Ceiling:</span> <strong>₹{viewingScheme.eligibilityCriteria.maxAnnualIncome.toLocaleString()} / year</strong>
              </div>
              <div>
                <span style={{ color: 'var(--text-muted)' }}>Official Helpline:</span> <strong>{viewingScheme.contactHelpline}</strong>
              </div>
            </div>

            <div style={{ marginBottom: '20px' }}>
              <h4 style={{ fontSize: '0.92rem', color: 'var(--text-heading)', marginBottom: '8px' }}>
                Mandatory Documentation Required:
              </h4>
              <ul style={{ listStyle: 'disc', paddingLeft: '20px', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                {viewingScheme.requiredDocuments.map((doc, idx) => (
                  <li key={idx}>{doc}</li>
                ))}
              </ul>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
              <Button variant="secondary" onClick={() => setViewingScheme(null)}>
                Close
              </Button>
              <a href="https://beneficiary.nha.gov.in/" target="_blank" rel="noreferrer" style={{ textDecoration: 'none' }}>
                <Button variant="teal" rightIcon={<ExternalLink size={14} />}>
                  Proceed to Government Portal
                </Button>
              </a>
            </div>
          </div>
        </div>
      )}

      {/* NGO DETAIL MODAL */}
      {viewingNGO && (
        <div className="modal-overlay" onClick={() => setViewingNGO(null)}>
          <div className="modal-content" style={{ maxWidth: '580px', padding: '24px' }} onClick={e => e.stopPropagation()}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <div>
                <Badge variant="purple">{viewingNGO.supportType}</Badge>
                <h3 style={{ margin: '4px 0 0', color: 'var(--text-heading)', fontSize: '1.3rem' }}>
                  {viewingNGO.organizationName}
                </h3>
              </div>
              <button onClick={() => setViewingNGO(null)} style={{ background: 'none', border: 'none', fontSize: '1.4rem', cursor: 'pointer', color: 'var(--text-muted)' }}>
                ×
              </button>
            </div>

            <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '16px' }}>
              {viewingNGO.eligibilityDescription}
            </p>

            <div style={{ marginBottom: '20px' }}>
              <h4 style={{ fontSize: '0.92rem', color: 'var(--text-heading)', marginBottom: '8px' }}>
                Required Verification Documents:
              </h4>
              <ul style={{ listStyle: 'disc', paddingLeft: '20px', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                {viewingNGO.requiredDocuments.map((doc, idx) => (
                  <li key={idx}>{doc}</li>
                ))}
              </ul>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
              <Button variant="secondary" onClick={() => setViewingNGO(null)}>
                Close
              </Button>
              <Button
                variant="teal"
                disabled={viewingNGO.applicationStatus === 'APPLIED'}
                onClick={() => {
                  handleApplyNGO(viewingNGO.id);
                  setViewingNGO(null);
                }}
              >
                {viewingNGO.applicationStatus === 'APPLIED' ? 'Already Requested' : 'Submit Referral Request'}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* INSTANT ELIGIBILITY CHECKER MODAL */}
      {showEligibilityModal && (
        <div className="modal-overlay" onClick={() => setShowEligibilityModal(false)}>
          <div className="modal-content" style={{ maxWidth: '540px', padding: '24px' }} onClick={e => e.stopPropagation()}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <div>
                <Badge variant="green">INSTANT ELIGIBILITY CHECK</Badge>
                <h3 style={{ margin: '4px 0 0', color: 'var(--text-heading)', fontSize: '1.25rem' }}>
                  Check Scheme Subsidy Eligibility
                </h3>
              </div>
              <button onClick={() => setShowEligibilityModal(false)} style={{ background: 'none', border: 'none', fontSize: '1.4rem', cursor: 'pointer', color: 'var(--text-muted)' }}>
                ×
              </button>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', marginBottom: '20px' }}>
              <div>
                <label className="form-label">Ration Card Category (NFSA)</label>
                <select
                  value={rationCardInput}
                  onChange={e => setRationCardInput(e.target.value)}
                  className="form-control"
                >
                  <option value="AAY">Antyodaya Anna Yojana (AAY - Priority Subsidy)</option>
                  <option value="BPL">Below Poverty Line (BPL - 100% PM-JAY Eligible)</option>
                  <option value="APL">Above Poverty Line (APL - General)</option>
                </select>
              </div>

              <div>
                <label className="form-label">Annual Family Income Bracket</label>
                <select
                  value={annualIncomeInput}
                  onChange={e => setAnnualIncomeInput(e.target.value)}
                  className="form-control"
                >
                  <option value="UNDER_2_5_LAKH">Below ₹2.5 Lakh / annum</option>
                  <option value="2_5_TO_5_LAKH">₹2.5 Lakh to ₹5 Lakh / annum</option>
                  <option value="ABOVE_5_LAKH">Above ₹5 Lakh / annum</option>
                </select>
              </div>

              <Button variant="teal" onClick={handleRunEligibilityTest}>
                Check Live Eligibility
              </Button>
            </div>

            {eligibilityResult && (
              <div
                style={{
                  padding: '16px',
                  borderRadius: '12px',
                  background: eligibilityResult === 'ELIGIBLE' ? 'rgba(22, 163, 74, 0.1)' : 'rgba(217, 119, 6, 0.1)',
                  border: `1px solid ${eligibilityResult === 'ELIGIBLE' ? '#16A34A' : '#D97706'}`,
                  marginBottom: '16px'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: eligibilityResult === 'ELIGIBLE' ? '#16A34A' : '#D97706', fontWeight: 700, fontSize: '0.95rem' }}>
                  <CheckCircle2 size={18} />
                  {eligibilityResult === 'ELIGIBLE' ? 'Eligible for Ayushman Bharat PM-JAY' : 'Standard Healthcare Scheme Tier'}
                </div>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.84rem', margin: '4px 0 0' }}>
                  {eligibilityResult === 'ELIGIBLE'
                    ? 'Your criteria qualifies for up to ₹5,00,000 cashless secondary and tertiary hospitalization cover across empaneled hospitals.'
                    : 'While statutory PM-JAY requires BPL / AAY certification, you may still access state insurance (MJPJAY) and NGO funding grants.'}
                </p>
              </div>
            )}

            <div style={{ textAlign: 'right' }}>
              <Button variant="secondary" onClick={() => setShowEligibilityModal(false)}>
                Done
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
