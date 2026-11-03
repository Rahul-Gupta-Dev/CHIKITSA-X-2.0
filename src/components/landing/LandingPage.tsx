import React, { useState } from 'react';
import {
  Mic,
  Building2,
  CalendarCheck,
  Search,
  ShieldCheck,
  AlertTriangle,
  ArrowRight,
  Sparkles,
  Activity,
  FileCheck2,
  Wallet,
  CheckCircle2,
  Lock,
  Stethoscope
} from 'lucide-react';
import type { UserRole } from '../../types';
import { Button, Card, Badge } from '../common/UIComponents';

interface Props {
  onStartSymptoms: () => void;
  onOpenHospitals: (initialQuery?: string) => void;
  onBookAppointment: () => void;
  onOpenEmergency: () => void;
  onOpenFinancialAssistance: () => void;
  onSelectRole: (role: UserRole) => void;
  onOpenLogin: () => void;
  onOpenRegister: () => void;
}

export const LandingPage: React.FC<Props> = ({
  onStartSymptoms,
  onOpenHospitals,
  onBookAppointment,
  onOpenEmergency,
  onOpenFinancialAssistance,
  onSelectRole,
  onOpenLogin,
  onOpenRegister
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCity, setSelectedCity] = useState('All');

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    onOpenHospitals(searchQuery.trim());
  };

  const handleCityClick = (city: string) => {
    setSelectedCity(city);
    onOpenHospitals(city === 'All' ? '' : city);
  };

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', paddingBottom: '60px' }}>
      {/* 1. HERO SECTION */}
      <section
        style={{
          position: 'relative',
          padding: '44px 24px 48px',
          background: 'var(--bg-card)',
          borderRadius: '24px',
          border: '1px solid var(--border-light)',
          boxShadow: 'var(--shadow-sm)',
          marginBottom: '36px',
          marginTop: '8px',
          textAlign: 'center'
        }}
      >
        <div style={{ maxWidth: '820px', margin: '0 auto' }}>
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
            <Badge variant="teal" icon={<Sparkles size={14} />}>
              HEALTHCARE INNOVATION PLATFORM
            </Badge>
          </div>

          <h1
            style={{
              fontSize: 'clamp(2.1rem, 4.2vw, 3.4rem)',
              fontWeight: 800,
              lineHeight: 1.18,
              marginBottom: '16px',
              color: 'var(--text-heading)',
              letterSpacing: '-0.02em'
            }}
          >
            Intelligent Care Navigation &amp;{' '}
            <span style={{ color: 'var(--primary-teal)' }}>Financial Protection</span>
          </h1>

          <p
            style={{
              fontSize: 'clamp(1rem, 1.8vw, 1.2rem)',
              color: 'var(--text-secondary)',
              lineHeight: 1.6,
              margin: '0 auto 28px',
              maxWidth: '680px'
            }}
          >
            CHIKITSA-X connects clinical symptom triage, accredited hospital discovery, OPD appointment booking, and live financial gap coverage in a unified, privacy-first patient journey.
          </p>

          {/* Location-based Hospital Search Bar */}
          <form
            onSubmit={handleSearch}
            style={{
              display: 'flex',
              alignItems: 'center',
              background: 'var(--bg-subtle)',
              border: '2px solid var(--border-light)',
              borderRadius: '16px',
              padding: '6px 8px 6px 16px',
              maxWidth: '640px',
              margin: '0 auto 20px',
              boxShadow: 'var(--shadow-sm)',
              transition: 'border-color 0.2s ease'
            }}
          >
            <Search size={20} color="var(--text-muted)" style={{ marginRight: '10px', flexShrink: 0 }} />
            <input
              type="text"
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              placeholder="Search hospitals by name, specialty, or city (e.g. Cardiology, Pune)..."
              style={{
                flex: 1,
                border: 'none',
                background: 'transparent',
                outline: 'none',
                fontSize: '0.96rem',
                color: 'var(--text-main)',
                fontFamily: 'inherit'
              }}
            />
            <Button type="submit" variant="teal" size="sm" style={{ flexShrink: 0 }}>
              Find Care
            </Button>
          </form>

          {/* Quick Location Chips */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', flexWrap: 'wrap', marginBottom: '24px' }}>
            <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)', fontWeight: 600 }}>Quick Filter:</span>
            {['All', 'Pune', 'Mumbai', 'Nashik'].map(city => (
              <button
                key={city}
                type="button"
                onClick={() => handleCityClick(city)}
                style={{
                  background: selectedCity === city ? 'var(--primary-teal)' : 'var(--bg-subtle)',
                  color: selectedCity === city ? '#FFFFFF' : 'var(--text-secondary)',
                  border: '1px solid var(--border-light)',
                  padding: '4px 12px',
                  borderRadius: '14px',
                  fontSize: '0.8rem',
                  fontWeight: 600,
                  cursor: 'pointer'
                }}
              >
                {city}
              </button>
            ))}
          </div>

          {/* Emergency Alert Hotline Banner */}
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '10px',
              background: 'rgba(220, 38, 38, 0.08)',
              border: '1px solid rgba(220, 38, 38, 0.25)',
              padding: '8px 18px',
              borderRadius: '20px',
              fontSize: '0.85rem',
              color: '#DC2626'
            }}
          >
            <AlertTriangle size={16} />
            <span>Emergency? Immediate 24/7 Trauma Hotline: <strong>108 / 102</strong></span>
            <Button
              variant="danger"
              size="sm"
              onClick={onOpenEmergency}
              style={{ padding: '2px 10px', minHeight: '28px', fontSize: '0.78rem' }}
            >
              Emergency Care
            </Button>
          </div>
        </div>
      </section>

      {/* 2. THREE PRIMARY ACTION CARDS */}
      <section style={{ marginBottom: '48px' }}>
        <div style={{ textAlign: 'center', marginBottom: '24px' }}>
          <h2 style={{ fontSize: '1.6rem', color: 'var(--text-heading)', marginBottom: '6px' }}>
            Start What You Need Today
          </h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.92rem', margin: 0 }}>
            Choose an action to immediately begin your connected healthcare experience
          </p>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '20px' }}>
          {/* Action 1: Check Symptoms */}
          <Card hoverable padding="24px" style={{ display: 'flex', flexDirection: 'column' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '14px', marginBottom: '16px' }}>
              <div
                style={{
                  width: '50px',
                  height: '50px',
                  borderRadius: '14px',
                  background: 'rgba(2, 132, 199, 0.12)',
                  color: 'var(--primary-teal)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}
              >
                <Mic size={26} />
              </div>
              <div>
                <span className="badge badge-teal" style={{ marginBottom: '4px' }}>AI TRIAGE</span>
                <h3 style={{ fontSize: '1.25rem', color: 'var(--text-heading)', margin: 0 }}>Check Symptoms</h3>
              </div>
            </div>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.92rem', lineHeight: 1.5, flex: 1, marginBottom: '20px' }}>
              Describe symptoms via voice or text input. Receive instant clinical urgency assessment, potential risk stratification, and recommended specialty care.
            </p>
            <Button variant="teal" onClick={onStartSymptoms} rightIcon={<ArrowRight size={16} />}>
              Check Symptoms Now
            </Button>
          </Card>

          {/* Action 2: Find Hospitals */}
          <Card hoverable padding="24px" style={{ display: 'flex', flexDirection: 'column' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '14px', marginBottom: '16px' }}>
              <div
                style={{
                  width: '50px',
                  height: '50px',
                  borderRadius: '14px',
                  background: 'rgba(15, 23, 42, 0.08)',
                  color: 'var(--primary-navy)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}
              >
                <Building2 size={26} />
              </div>
              <div>
                <span className="badge badge-navy" style={{ marginBottom: '4px' }}>DISCOVERY</span>
                <h3 style={{ fontSize: '1.25rem', color: 'var(--text-heading)', margin: 0 }}>Find Hospitals</h3>
              </div>
            </div>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.92rem', lineHeight: 1.5, flex: 1, marginBottom: '20px' }}>
              Explore accredited tertiary hospitals ranked by the 5-factor CHIKITSA-X Care Score: clinical specialty fit, affordability, distance, and live bed availability.
            </p>
            <Button variant="primary" onClick={() => onOpenHospitals()} rightIcon={<ArrowRight size={16} />}>
              Explore Hospital Directory
            </Button>
          </Card>

          {/* Action 3: Book Appointment */}
          <Card hoverable padding="24px" style={{ display: 'flex', flexDirection: 'column' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '14px', marginBottom: '16px' }}>
              <div
                style={{
                  width: '50px',
                  height: '50px',
                  borderRadius: '14px',
                  background: 'rgba(22, 163, 74, 0.12)',
                  color: '#16A34A',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}
              >
                <CalendarCheck size={26} />
              </div>
              <div>
                <span className="badge badge-green" style={{ marginBottom: '4px' }}>DIRECT ACCESS</span>
                <h3 style={{ fontSize: '1.25rem', color: 'var(--text-heading)', margin: 0 }}>Book Appointment</h3>
              </div>
            </div>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.92rem', lineHeight: 1.5, flex: 1, marginBottom: '20px' }}>
              Select your doctor, choose a verified OPD date and time slot, and generate an encrypted Reference ID &amp; QR Pass for contactless hospital check-in.
            </p>
            <Button
              variant="outline"
              onClick={onBookAppointment}
              rightIcon={<ArrowRight size={16} />}
              style={{ color: '#16A34A', borderColor: '#16A34A' }}
            >
              Book OPD Slot
            </Button>
          </Card>
        </div>
      </section>

      {/* 3. HOW THE PLATFORM WORKS (Connected Care Journey) */}
      <section style={{ marginBottom: '48px', background: 'var(--bg-subtle)', borderRadius: '20px', padding: '36px 24px', border: '1px solid var(--border-light)' }}>
        <div style={{ textAlign: 'center', marginBottom: '32px' }}>
          <Badge variant="teal">INTEGRATED WORKFLOW</Badge>
          <h2 style={{ fontSize: '1.65rem', color: 'var(--text-heading)', marginTop: '8px', marginBottom: '6px' }}>
            How CHIKITSA-X Connects Your Care
          </h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.92rem', maxWidth: '640px', margin: '0 auto' }}>
            A seamless bridge from clinical assessment to hospital consultation and financial support
          </p>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '16px' }}>
          {[
            {
              step: '01',
              title: 'AI Symptom Triage',
              desc: 'Describe symptoms using voice or text. Get structured metrics, duration, and urgency scoring with explicit medical safety guardrails.',
              icon: <Activity size={20} color="var(--primary-teal)" />
            },
            {
              step: '02',
              title: 'Smart Hospital Match',
              desc: 'Transparent Care Score ranking evaluates specialty alignment, out-of-pocket costs, distance, and real-time bed capacity.',
              icon: <Building2 size={20} color="var(--primary-teal)" />
            },
            {
              step: '03',
              title: 'OPD Pass & QR Verification',
              desc: 'Book verified appointment slot. Receive digital token QR pass for fast hospital reception check-in and consent authorization.',
              icon: <FileCheck2 size={20} color="var(--primary-teal)" />
            },
            {
              step: '04',
              title: 'Financial Gap Coverage',
              desc: 'Match with Ayushman Bharat PM-JAY, state schemes, and NGO funds to eliminate out-of-pocket medical expenditure.',
              icon: <Wallet size={20} color="var(--primary-teal)" />
            }
          ].map(item => (
            <div
              key={item.step}
              style={{
                background: 'var(--bg-card)',
                borderRadius: '16px',
                padding: '20px',
                border: '1px solid var(--border-light)',
                position: 'relative'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
                <span style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--primary-teal)', opacity: 0.85 }}>
                  {item.step}
                </span>
                <div style={{ padding: '8px', background: 'var(--bg-subtle)', borderRadius: '10px' }}>
                  {item.icon}
                </div>
              </div>
              <h4 style={{ fontSize: '1.05rem', color: 'var(--text-heading)', marginBottom: '8px' }}>
                {item.title}
              </h4>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', lineHeight: 1.5, margin: 0 }}>
                {item.desc}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* 4. HEALTHCARE FINANCIAL ASSISTANCE HIGHLIGHT */}
      <section style={{ marginBottom: '48px' }}>
        <div
          style={{
            background: 'var(--bg-card)',
            border: '1px solid var(--border-light)',
            borderRadius: '20px',
            padding: '32px',
            display: 'flex',
            flexDirection: 'row',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: '24px',
            boxShadow: 'var(--shadow-sm)'
          }}
        >
          <div style={{ maxWidth: '640px' }}>
            <Badge variant="green" style={{ marginBottom: '10px' }}>
              CARE-TO-COST PROTECTION
            </Badge>
            <h2 style={{ fontSize: '1.6rem', color: 'var(--text-heading)', marginBottom: '10px' }}>
              No Family Should Face Poverty Due to Medical Costs
            </h2>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.94rem', lineHeight: 1.6, marginBottom: '16px' }}>
              CHIKITSA-X automatically checks eligibility for <strong>Ayushman Bharat PM-JAY</strong> (up to ₹5,00,000 coverage), state healthcare schemes, insurance policies, and philanthropic NGO grants like Tata Trusts and Being Human Foundation.
            </p>
            <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.85rem', color: 'var(--text-main)', fontWeight: 600 }}>
                <CheckCircle2 size={16} color="#16A34A" /> PM-JAY Scheme Matching
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.85rem', color: 'var(--text-main)', fontWeight: 600 }}>
                <CheckCircle2 size={16} color="#16A34A" /> Live Care-to-Cost Calculator
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.85rem', color: 'var(--text-main)', fontWeight: 600 }}>
                <CheckCircle2 size={16} color="#16A34A" /> Transparent Cost Scenarios
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', minWidth: '220px' }}>
            <Button variant="teal" onClick={onOpenFinancialAssistance} rightIcon={<ArrowRight size={16} />}>
              Check Scheme Eligibility
            </Button>
            <Button variant="secondary" onClick={() => onOpenHospitals()}>
              View Empaneled Hospitals
            </Button>
          </div>
        </div>
      </section>

      {/* 5. TRUST, PRIVACY & SAFETY INFORMATION */}
      <section style={{ marginBottom: '40px' }}>
        <div
          style={{
            background: 'var(--bg-subtle)',
            border: '1px solid var(--border-light)',
            borderRadius: '16px',
            padding: '24px',
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
            gap: '20px'
          }}
        >
          <div style={{ display: 'flex', gap: '12px', alignItems: 'flex-start' }}>
            <div style={{ padding: '8px', background: 'var(--bg-card)', borderRadius: '10px', color: '#DC2626' }}>
              <AlertTriangle size={20} />
            </div>
            <div>
              <h4 style={{ fontSize: '0.95rem', color: 'var(--text-heading)', marginBottom: '4px' }}>
                Emergency Medical Notice
              </h4>
              <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', lineHeight: 1.45, margin: 0 }}>
                AI assessments are clinical guidance tools and do not substitute professional medical diagnosis. Severe symptoms require immediate trauma or emergency room evaluation.
              </p>
            </div>
          </div>

          <div style={{ display: 'flex', gap: '12px', alignItems: 'flex-start' }}>
            <div style={{ padding: '8px', background: 'var(--bg-card)', borderRadius: '10px', color: 'var(--primary-teal)' }}>
              <Lock size={20} />
            </div>
            <div>
              <h4 style={{ fontSize: '0.95rem', color: 'var(--text-heading)', marginBottom: '4px' }}>
                Consent-First Data Privacy
              </h4>
              <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', lineHeight: 1.45, margin: 0 }}>
                In accordance with ABDM standards, your health records are encrypted. Doctors and hospitals can only access medical summaries when you explicitly grant digital consent.
              </p>
            </div>
          </div>

          <div style={{ display: 'flex', gap: '12px', alignItems: 'flex-start' }}>
            <div style={{ padding: '8px', background: 'var(--bg-card)', borderRadius: '10px', color: '#16A34A' }}>
              <ShieldCheck size={20} />
            </div>
            <div>
              <h4 style={{ fontSize: '0.95rem', color: 'var(--text-heading)', marginBottom: '4px' }}>
                Verified Healthcare Partners
              </h4>
              <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', lineHeight: 1.45, margin: 0 }}>
                All hospitals, doctors, and clinics listed on CHIKITSA-X undergo accreditation and registration verification before offering digital OPD passes.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* 6. ROLE QUICK PORTALS ACCESS */}
      <section
        style={{
          borderTop: '1px solid var(--border-light)',
          paddingTop: '32px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '16px'
        }}
      >
        <div>
          <h4 style={{ fontSize: '1rem', color: 'var(--text-heading)', margin: '0 0 4px' }}>
            Portals for Doctors &amp; Healthcare Facilities
          </h4>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', margin: 0 }}>
            Dedicated workflows tailored for clinical teams and healthcare facilities
          </p>
        </div>

        <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
          <Button
            variant="outline"
            size="sm"
            onClick={onOpenLogin}
          >
            Sign In
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={onOpenRegister}
          >
            Register
          </Button>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => onSelectRole('DOCTOR')}
            leftIcon={<Stethoscope size={14} />}
          >
            Doctor Portal
          </Button>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => onSelectRole('HOSPITAL_ADMIN')}
            leftIcon={<Building2 size={14} />}
          >
            Hospital Portal
          </Button>
        </div>
      </section>
    </div>
  );
};
