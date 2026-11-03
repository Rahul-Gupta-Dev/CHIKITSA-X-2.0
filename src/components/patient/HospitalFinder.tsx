import React, { useState, useEffect, useMemo } from 'react';
import { hospitalService, mockHospitalService } from '../../services/apiServices';
import type { Hospital, Doctor } from '../../types';
import {
  Award,
  MapPin,
  Info,
  ArrowRight,
  Layers,
  Activity,
  Search,
  Building2,
  ShieldCheck,
  X
} from 'lucide-react';
import { Button, Card, Badge, EmptyState } from '../common/UIComponents';
import { HospitalDetailsModal } from './HospitalDetailsModal';

interface Props {
  initialSearchQuery?: string;
  onSelectHospital: (hospital: Hospital, doctor?: Doctor) => void;
  onOpenCompare: () => void;
}

export const HospitalFinder: React.FC<Props> = ({
  initialSearchQuery = '',
  onSelectHospital,
  onOpenCompare
}) => {
  const [filter, setFilter] = useState<'CARE_SCORE' | 'LOWEST_COST' | 'NEAREST'>('CARE_SCORE');
  const [searchQuery, setSearchQuery] = useState(initialSearchQuery);
  const [specialtyFilter, setSpecialtyFilter] = useState<string>('ALL');
  const [emergencyOnly, setEmergencyOnly] = useState<boolean>(false);
  const [selectedWhyHosp, setSelectedWhyHosp] = useState<Hospital | null>(null);
  const [detailsHospital, setDetailsHospital] = useState<Hospital | null>(null);
  const [hospitals, setHospitals] = useState<Hospital[]>(() => mockHospitalService.getRankedHospitals(filter));
  const [isLoading, setIsLoading] = useState(false);

  const handleFilterChange = (newFilter: 'CARE_SCORE' | 'LOWEST_COST' | 'NEAREST') => {
    setFilter(newFilter);
    setIsLoading(true);
  };

  useEffect(() => {
    let isMounted = true;
    hospitalService.recommendHospitals(filter, 'usr-patient-1')
      .then(res => {
        if (isMounted && res) {
          setHospitals(res);
        }
      })
      .finally(() => {
        if (isMounted) setIsLoading(false);
      });
    return () => { isMounted = false; };
  }, [filter]);

  // Extract all distinct specialties from available data
  const availableSpecialties = useMemo(() => {
    const specs = new Set<string>();
    hospitals.forEach(h => h.specialties.forEach(s => specs.add(s)));
    return Array.from(specs);
  }, [hospitals]);

  // Client-side filtering across name, city, address, PIN code, specialty, emergency
  const filteredHospitals = useMemo(() => {
    return hospitals.filter(h => {
      const q = searchQuery.toLowerCase().trim();
      const matchesSearch = !q ||
        h.name.toLowerCase().includes(q) ||
        h.city.toLowerCase().includes(q) ||
        h.address.toLowerCase().includes(q) ||
        h.specialties.some(s => s.toLowerCase().includes(q));

      const matchesSpecialty = specialtyFilter === 'ALL' ||
        h.specialties.some(s => s.toLowerCase() === specialtyFilter.toLowerCase());

      const matchesEmergency = !emergencyOnly || h.emergencyAvailable;

      return matchesSearch && matchesSpecialty && matchesEmergency;
    });
  }, [hospitals, searchQuery, specialtyFilter, emergencyOnly]);

  const handleClearFilters = () => {
    setSearchQuery('');
    setSpecialtyFilter('ALL');
    setEmergencyOnly(false);
  };

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '10px 0 40px' }}>
      {/* Header & Filter Controls */}
      <div style={{ marginBottom: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '16px', marginBottom: '16px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
              <Badge variant="teal">HOSPITAL DISCOVERY</Badge>
              <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>• Showing {filteredHospitals.length} of {hospitals.length} Verified Centers</span>
            </div>
            <h1 style={{ fontSize: '1.75rem', color: 'var(--text-heading)', margin: 0 }}>
              Hospital Directory &amp; Care Score Ranking
            </h1>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', margin: '4px 0 0' }}>
              Transparent algorithm evaluating Clinical Specialty Fit (35%), Affordability (25%), Distance (15%), Bed Availability (15%), and Scheme Coverage (10%).
            </p>
          </div>

          <div style={{ display: 'flex', gap: '10px', alignItems: 'center', flexWrap: 'wrap' }}>
            <Button
              variant="outline"
              size="sm"
              onClick={onOpenCompare}
              leftIcon={<Layers size={15} />}
            >
              Compare Hospitals
            </Button>
          </div>
        </div>

        {/* Search & Filter Toolbar */}
        <div
          style={{
            background: 'var(--bg-card)',
            border: '1px solid var(--border-light)',
            borderRadius: '16px',
            padding: '16px',
            display: 'flex',
            flexDirection: 'column',
            gap: '12px',
            boxShadow: 'var(--shadow-sm)'
          }}
        >
          <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
            {/* Search Input */}
            <div style={{ flex: 1, minWidth: '260px', position: 'relative' }}>
              <Search size={18} color="var(--text-muted)" style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)' }} />
              <input
                type="text"
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                placeholder="Search by hospital name, city, or specialty (e.g. Pune, Cardiology)..."
                className="form-control"
                style={{ paddingLeft: '38px' }}
              />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery('')}
                  style={{ position: 'absolute', right: '10px', top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)' }}
                >
                  <X size={16} />
                </button>
              )}
            </div>

            {/* Specialty Dropdown */}
            <div style={{ minWidth: '180px' }}>
              <select
                value={specialtyFilter}
                onChange={e => setSpecialtyFilter(e.target.value)}
                className="form-control"
                style={{ cursor: 'pointer' }}
              >
                <option value="ALL">All Specialties</option>
                {availableSpecialties.map(spec => (
                  <option key={spec} value={spec}>{spec}</option>
                ))}
              </select>
            </div>

            {/* Emergency 24/7 Filter Toggle */}
            <button
              onClick={() => setEmergencyOnly(prev => !prev)}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '8px',
                padding: '10px 14px',
                borderRadius: '10px',
                border: emergencyOnly ? '1px solid #DC2626' : '1px solid var(--border-light)',
                background: emergencyOnly ? 'rgba(220, 38, 38, 0.1)' : 'var(--bg-subtle)',
                color: emergencyOnly ? '#DC2626' : 'var(--text-secondary)',
                fontWeight: 600,
                fontSize: '0.88rem',
                cursor: 'pointer'
              }}
            >
              <Activity size={16} />
              <span>24/7 Emergency ICU</span>
            </button>
          </div>

          {/* Ranking Algorithm Sort Pills */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '8px', borderTop: '1px solid var(--border-light)', paddingTop: '12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
              <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)', fontWeight: 600 }}>Rank By:</span>
              <div style={{ display: 'flex', gap: '6px', background: 'var(--bg-subtle)', padding: '3px', borderRadius: '10px' }}>
                <button
                  onClick={() => handleFilterChange('CARE_SCORE')}
                  className={`btn btn-sm ${filter === 'CARE_SCORE' ? 'btn-primary' : 'btn-ghost'}`}
                  style={{ minHeight: '30px', padding: '4px 10px', fontSize: '0.8rem' }}
                >
                  Best Care Score
                </button>
                <button
                  onClick={() => handleFilterChange('LOWEST_COST')}
                  className={`btn btn-sm ${filter === 'LOWEST_COST' ? 'btn-primary' : 'btn-ghost'}`}
                  style={{ minHeight: '30px', padding: '4px 10px', fontSize: '0.8rem' }}
                >
                  Lowest Out-of-Pocket
                </button>
                <button
                  onClick={() => handleFilterChange('NEAREST')}
                  className={`btn btn-sm ${filter === 'NEAREST' ? 'btn-primary' : 'btn-ghost'}`}
                  style={{ minHeight: '30px', padding: '4px 10px', fontSize: '0.8rem' }}
                >
                  Nearest Distance
                </button>
              </div>
            </div>

            {(searchQuery || specialtyFilter !== 'ALL' || emergencyOnly) && (
              <button
                onClick={handleClearFilters}
                style={{ background: 'none', border: 'none', color: 'var(--primary-teal)', fontSize: '0.82rem', fontWeight: 600, cursor: 'pointer', textDecoration: 'underline' }}
              >
                Reset All Filters
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Hospital Cards Grid */}
      {isLoading ? (
        <div style={{ textAlign: 'center', padding: '48px 20px', color: 'var(--text-muted)' }}>
          <Activity className="spin-animate" size={28} style={{ margin: '0 auto 10px', color: 'var(--primary-teal)' }} />
          <div>Ranking accredited hospitals...</div>
        </div>
      ) : filteredHospitals.length === 0 ? (
        <EmptyState
          icon={<Building2 size={32} />}
          title="No Hospitals Found"
          description={`No hospitals match your active criteria "${searchQuery || specialtyFilter}". Try clearing your filters or search for another city.`}
          actionLabel="Clear Filters"
          onAction={handleClearFilters}
        />
      ) : (
        <div className="grid-hospitals">
          {filteredHospitals.map(hosp => (
            <Card
              key={hosp.id}
              hoverable
              padding="0"
              style={{ overflow: 'hidden', display: 'flex', flexDirection: 'column' }}
            >
              {/* Image & Overlay Header */}
              <div style={{ position: 'relative', height: '160px', overflow: 'hidden' }}>
                <img
                  src={hosp.image}
                  alt={hosp.name}
                  style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                />
                <div
                  style={{
                    position: 'absolute',
                    top: 0, left: 0, right: 0, bottom: 0,
                    background: 'linear-gradient(180deg, rgba(15, 23, 42, 0.15) 0%, rgba(15, 23, 42, 0.8) 100%)'
                  }}
                />

                {/* Care Score Pill */}
                <div style={{ position: 'absolute', top: '12px', right: '12px' }}>
                  <span className="care-score-pill">
                    <Award size={14} /> Care Score: {hosp.chikitsaxCareScore}/100
                  </span>
                </div>

                {/* Distance Badge */}
                <div style={{ position: 'absolute', bottom: '12px', left: '12px' }}>
                  <span className="badge badge-teal" style={{ backdropFilter: 'blur(8px)', background: 'rgba(15, 23, 42, 0.85)', color: '#FFF' }}>
                    <MapPin size={12} /> {hosp.distanceKm} km • {hosp.city}
                  </span>
                </div>

                {/* Accreditation Pill */}
                {hosp.accreditation && hosp.accreditation.length > 0 && (
                  <div style={{ position: 'absolute', top: '12px', left: '12px' }}>
                    <span className="badge badge-green" style={{ backdropFilter: 'blur(8px)', background: 'rgba(21, 128, 61, 0.85)', color: '#FFF' }}>
                      <ShieldCheck size={12} /> {hosp.accreditation[0]}
                    </span>
                  </div>
                )}
              </div>

              {/* Card Body */}
              <div style={{ padding: '20px', flex: 1, display: 'flex', flexDirection: 'column' }}>
                <div style={{ marginBottom: '8px' }}>
                  <h3 style={{ fontSize: '1.2rem', color: 'var(--text-heading)', margin: 0, lineHeight: 1.3 }}>
                    {hosp.name}
                  </h3>
                  <p style={{ color: 'var(--text-muted)', fontSize: '0.82rem', margin: '3px 0 0' }}>
                    {hosp.tagline}
                  </p>
                </div>

                {/* Key Metrics Summary */}
                <div
                  style={{
                    background: 'var(--bg-subtle)',
                    border: '1px solid var(--border-light)',
                    borderRadius: '12px',
                    padding: '12px',
                    marginBottom: '14px',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '6px',
                    fontSize: '0.84rem'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text-muted)' }}>Est. Cost:</span>
                    <strong style={{ color: '#16A34A' }}>
                      ₹{hosp.estimatedCostRange.min.toLocaleString()} – ₹{hosp.estimatedCostRange.max.toLocaleString()}
                    </strong>
                  </div>

                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text-muted)' }}>Emergency Trauma:</span>
                    {hosp.emergencyAvailable ? (
                      <span style={{ color: '#16A34A', fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                        <Activity size={12} /> 24/7 ({hosp.emergencyBedsFree} Beds Free)
                      </span>
                    ) : (
                      <span style={{ color: 'var(--text-muted)' }}>Routine OPD</span>
                    )}
                  </div>

                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text-muted)' }}>Financial Coverage:</span>
                    <span style={{ color: 'var(--primary-teal)', fontWeight: 600 }}>
                      {hosp.acceptedGovSchemes.length > 0 ? 'PM-JAY + Insurance' : 'Private Cashless'}
                    </span>
                  </div>
                </div>

                {/* Specialties Badges */}
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', marginBottom: '16px' }}>
                  {hosp.specialties.slice(0, 3).map((spec, i) => (
                    <span key={i} className="badge badge-purple" style={{ fontSize: '0.72rem' }}>
                      {spec}
                    </span>
                  ))}
                  {hosp.specialties.length > 3 && (
                    <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', alignSelf: 'center' }}>
                      +{hosp.specialties.length - 3} more
                    </span>
                  )}
                </div>

                {/* 3 Actions: View Details, Why Recommended?, Book OPD */}
                <div style={{ marginTop: 'auto', display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => setDetailsHospital(hosp)}
                    style={{ flex: 1 }}
                  >
                    View Details
                  </Button>

                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setSelectedWhyHosp(hosp)}
                    title="View 5-factor scoring explanation"
                    style={{ padding: '6px 10px' }}
                  >
                    <Info size={14} />
                  </Button>

                  <Button
                    variant="teal"
                    size="sm"
                    onClick={() => onSelectHospital(hosp)}
                    rightIcon={<ArrowRight size={14} />}
                    style={{ flex: 1.2 }}
                  >
                    Book OPD
                  </Button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Hospital Details Modal */}
      <HospitalDetailsModal
        hospital={detailsHospital}
        isOpen={Boolean(detailsHospital)}
        onClose={() => setDetailsHospital(null)}
        onBookWithDoctor={(h, doc) => onSelectHospital(h, doc)}
        onOpenCompare={() => onOpenCompare()}
      />

      {/* "Why Recommended?" Transparent Algorithm Modal */}
      {selectedWhyHosp && (
        <div className="modal-overlay" onClick={() => setSelectedWhyHosp(null)}>
          <div className="modal-content" style={{ maxWidth: '580px' }} onClick={e => e.stopPropagation()}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <div>
                <span className="badge badge-teal">ALGORITHM TRANSPARENCY</span>
                <h3 style={{ color: 'var(--text-heading)', fontSize: '1.3rem', margin: '4px 0 0' }}>
                  Why Recommended: {selectedWhyHosp.name}
                </h3>
              </div>
              <button
                onClick={() => setSelectedWhyHosp(null)}
                style={{ background: 'none', border: 'none', color: 'var(--text-muted)', fontSize: '1.4rem', cursor: 'pointer' }}
              >
                ×
              </button>
            </div>

            <div
              style={{
                background: 'var(--bg-subtle)',
                border: '1px solid var(--primary-teal)',
                borderRadius: '14px',
                padding: '16px',
                marginBottom: '20px',
                textAlign: 'center'
              }}
            >
              <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)', fontWeight: 600 }}>TOTAL CHIKITSA-X CARE SCORE</div>
              <div style={{ fontSize: '2.5rem', fontWeight: 800, color: 'var(--text-heading)', fontFamily: 'Outfit' }}>
                {selectedWhyHosp.chikitsaxCareScore}<span style={{ fontSize: '1.2rem', color: 'var(--primary-teal)' }}>/100</span>
              </div>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <div style={{ background: 'var(--bg-subtle)', border: '1px solid var(--border-light)', padding: '12px', borderRadius: '10px' }}>
                <div style={{ color: 'var(--primary-teal)', fontWeight: 700, fontSize: '0.88rem' }}>✓ Clinical Specialty Fit (35% Weight)</div>
                <div style={{ color: 'var(--text-main)', fontSize: '0.84rem', marginTop: '2px' }}>{selectedWhyHosp.whyRecommended.specialtyMatch}</div>
              </div>

              <div style={{ background: 'var(--bg-subtle)', border: '1px solid var(--border-light)', padding: '12px', borderRadius: '10px' }}>
                <div style={{ color: '#16A34A', fontWeight: 700, fontSize: '0.88rem' }}>✓ Cost &amp; Financial Feasibility (25% Weight)</div>
                <div style={{ color: 'var(--text-main)', fontSize: '0.84rem', marginTop: '2px' }}>{selectedWhyHosp.whyRecommended.costFeasibility}</div>
              </div>

              <div style={{ background: 'var(--bg-subtle)', border: '1px solid var(--border-light)', padding: '12px', borderRadius: '10px' }}>
                <div style={{ color: '#7C3AED', fontWeight: 700, fontSize: '0.88rem' }}>✓ Proximity &amp; Travel Distance (15% Weight)</div>
                <div style={{ color: 'var(--text-main)', fontSize: '0.84rem', marginTop: '2px' }}>{selectedWhyHosp.whyRecommended.proximityReason}</div>
              </div>

              <div style={{ background: 'var(--bg-subtle)', border: '1px solid var(--border-light)', padding: '12px', borderRadius: '10px' }}>
                <div style={{ color: '#D97706', fontWeight: 700, fontSize: '0.88rem' }}>✓ OPD &amp; ICU Bed Availability (15% Weight)</div>
                <div style={{ color: 'var(--text-main)', fontSize: '0.84rem', marginTop: '2px' }}>{selectedWhyHosp.whyRecommended.availabilityReason}</div>
              </div>

              <div style={{ background: 'var(--bg-subtle)', border: '1px solid var(--border-light)', padding: '12px', borderRadius: '10px' }}>
                <div style={{ color: 'var(--primary-teal)', fontWeight: 700, fontSize: '0.88rem' }}>✓ Scheme &amp; NGO Partnerships (10% Weight)</div>
                <div style={{ color: 'var(--text-main)', fontSize: '0.84rem', marginTop: '2px' }}>{selectedWhyHosp.whyRecommended.financialSupportReason}</div>
              </div>
            </div>

            <div style={{ marginTop: '20px', display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
              <Button variant="secondary" onClick={() => setSelectedWhyHosp(null)}>
                Close
              </Button>
              <Button
                variant="teal"
                onClick={() => {
                  onSelectHospital(selectedWhyHosp);
                  setSelectedWhyHosp(null);
                }}
              >
                Proceed to Book with {selectedWhyHosp.name} →
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
