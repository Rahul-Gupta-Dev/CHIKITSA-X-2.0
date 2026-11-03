import React, { useState, useEffect } from 'react';
import type { UserRole, Hospital, OPDRegistration } from './types';
import { db } from './db/database';

import { RoleSwitcherBar } from './components/layout/RoleSwitcherBar';
import { Header } from './components/layout/Header';
import { Footer } from './components/layout/Footer';

import { LoginModal } from './components/auth/LoginModal';
import { RegisterModal } from './components/auth/RegisterModal';

import { EmergencyModal } from './components/common/EmergencyModal';
import { LandingPage } from './components/landing/LandingPage';
import { PatientDashboard } from './components/patient/PatientDashboard';
import { VoiceIntakeModal } from './components/patient/VoiceIntakeModal';
import { MedicalRecordOCR } from './components/patient/MedicalRecordOCR';
import { HealthProfileView } from './components/patient/HealthProfileView';
import { AITriageView } from './components/patient/AITriageView';
import { HospitalFinder } from './components/patient/HospitalFinder';
import { HospitalCompare } from './components/patient/HospitalCompare';
import { OPDRegistrationModal } from './components/patient/OPDRegistrationModal';
import { HospitalPassQR } from './components/patient/HospitalPassQR';
import { FinancialSupportView } from './components/patient/FinancialSupportView';
import { AIFinancePlanner } from './components/patient/AIFinancePlanner';
import { AppointmentBookingWorkflow } from './components/patient/AppointmentBookingWorkflow';
import { PatientAppointmentsView } from './components/patient/PatientAppointmentsView';
import { PatientSettingsView } from './components/patient/PatientSettingsView';

import { DoctorDashboard } from './components/doctor/DoctorDashboard';
import { HospitalAdminDashboard } from './components/hospital/HospitalAdminDashboard';

import { authService } from './services/apiServices';
import { Home, Building2, Calendar, FileText, Settings, X, Stethoscope, Lock, ShieldAlert } from 'lucide-react';

export const App: React.FC = () => {
  // Theme Preference State: Light, Dark, System
  const [themePreference, setThemePreference] = useState<'light' | 'dark' | 'system'>(() => {
    const saved = localStorage.getItem('chikitsax_theme_preference') || localStorage.getItem('chikitsax_theme');
    if (saved === 'dark' || saved === 'light' || saved === 'system') return saved;
    return 'light';
  });

  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const updateTheme = () => {
      let resolvedTheme: 'light' | 'dark' = 'light';
      if (themePreference === 'system') {
        resolvedTheme = mediaQuery.matches ? 'dark' : 'light';
      } else {
        resolvedTheme = themePreference;
      }
      document.documentElement.setAttribute('data-theme', resolvedTheme);
      localStorage.setItem('chikitsax_theme_preference', themePreference);
      localStorage.setItem('chikitsax_theme', resolvedTheme);
    };

    updateTheme();

    if (themePreference === 'system') {
      mediaQuery.addEventListener('change', updateTheme);
      return () => mediaQuery.removeEventListener('change', updateTheme);
    }
  }, [themePreference]);

  // Auth & Roles State (Patient, Doctor, Hospital Admin)
  const [, setCurrentUser] = useState<any>(() => db.getCurrentUser());
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(() => {
    return Boolean(localStorage.getItem('chikitsax_auth_token') && db.getCurrentUser());
  });
  const [currentRole, setCurrentRole] = useState<UserRole>(() => {
    const user = db.getCurrentUser();
    const role = user?.role;
    return (role === 'PATIENT' || role === 'DOCTOR' || role === 'HOSPITAL_ADMIN') ? role : 'PATIENT';
  });
  const [activeTab, setActiveTab] = useState<string>('LANDING');

  const [isLoginOpen, setIsLoginOpen] = useState(false);
  const [isRegisterOpen, setIsRegisterOpen] = useState(false);

  // Session Restoration: Validate stored token on mount via /api/auth/me
  useEffect(() => {
    const token = localStorage.getItem('chikitsax_auth_token');
    if (token) {
      authService.getCurrentUser().then(userProfile => {
        if (userProfile && userProfile.id) {
          const userObj = {
            id: userProfile.id,
            email: userProfile.email,
            name: userProfile.name,
            role: userProfile.role as UserRole,
            phone: userProfile.phone,
            avatar: userProfile.avatar,
            hospitalId: userProfile.hospitalId,
            doctorProfile: userProfile.doctorProfile,
            patientProfile: userProfile.patientProfile
          };
          db.setCurrentUser(userObj);
          setCurrentUser(userObj);
          setCurrentRole(userObj.role);
          setIsAuthenticated(true);
        } else {
          // Token is invalid or expired
          authService.logout();
          db.clearCurrentUser();
          setCurrentUser(null);
          setIsAuthenticated(false);
        }
      }).catch(() => {
        // If server is unreachable, retain current session if token exists
      });
    } else {
      setIsAuthenticated(false);
    }
  }, []);

  // Modals & Navigation State
  const [isEmergencyOpen, setIsEmergencyOpen] = useState(false);
  const [isVoiceIntakeOpen, setIsVoiceIntakeOpen] = useState(false);
  const [isOCROpen, setIsOCROpen] = useState(false);
  const [isCompareOpen, setIsCompareOpen] = useState(false);
  const [isFinancePlannerOpen, setIsFinancePlannerOpen] = useState(false);

  // Active Flow Entities
  const [selectedHospital, setSelectedHospital] = useState<Hospital | null>(null);
  const [isOPDModalOpen, setIsOPDModalOpen] = useState(false);
  const [activeOPDPass, setActiveOPDPass] = useState<OPDRegistration | null>(() => {
    const list = db.getOPDRegistrations();
    return list.length > 0 ? list[0] : null;
  });
  const [isQRModalOpen, setIsQRModalOpen] = useState(false);

  // Hospital query passed from Landing page search
  const [hospitalSearchQuery, setHospitalSearchQuery] = useState('');

  const handleRoleChange = async (role: UserRole) => {
    setCurrentRole(role);
    const users = db.getDemoUsers();
    const matched = users.find(u => u.role === role) || users[0];
    try {
      const authRes = await authService.login(matched.email, 'demo123', matched.role);
      if (authRes && authRes.user) {
        db.setCurrentUser(authRes.user);
        setCurrentUser(authRes.user);
        setIsAuthenticated(true);
      }
    } catch {
      db.setCurrentUser(matched);
      setCurrentUser(matched);
    }

    if (role === 'PATIENT') setActiveTab('DASHBOARD');
    else if (role === 'DOCTOR') setActiveTab('DOCTOR_DASHBOARD');
    else if (role === 'HOSPITAL_ADMIN') setActiveTab('HOSPITAL_DASHBOARD');
  };

  const handleLoginSuccess = (role: UserRole) => {
    const user = db.getCurrentUser();
    setCurrentUser(user);
    setIsAuthenticated(true);
    setCurrentRole(role);
    if (role === 'PATIENT') setActiveTab('DASHBOARD');
    else if (role === 'DOCTOR') setActiveTab('DOCTOR_DASHBOARD');
    else if (role === 'HOSPITAL_ADMIN') setActiveTab('HOSPITAL_DASHBOARD');
  };

  const handleLogout = () => {
    authService.logout();
    db.clearCurrentUser();
    setCurrentUser(null);
    setIsAuthenticated(false);
    setCurrentRole('PATIENT');
    setActiveTab('LANDING');
  };

  const handleSelectHospital = (hosp: Hospital) => {
    setSelectedHospital(hosp);
    // Switch directly to the full 4-step OPD booking flow
    setActiveTab('BOOK_APPOINTMENT');
  };

  const handleBookingConfirmed = (opd: OPDRegistration) => {
    setActiveOPDPass(opd);
    setIsQRModalOpen(true);
    setActiveTab('PATIENT_APPOINTMENTS');
  };

  const handleResetDemo = () => {
    if (confirm('Reset all demo state back to initial seed data?')) {
      db.resetDemoState();
      window.location.reload();
    }
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', background: 'var(--bg-main)', color: 'var(--text-main)', paddingBottom: '60px' }}>
      {/* Top Role Switcher Bar for SIH Judges & Evaluators */}
      <RoleSwitcherBar
        currentRole={currentRole}
        onRoleChange={handleRoleChange}
      />

      {/* Main Header with 3-Appearance Preference & Auth */}
      <Header
        currentRole={currentRole}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        onOpenEmergency={() => setIsEmergencyOpen(true)}
        onResetDemo={handleResetDemo}
        themePreference={themePreference}
        onThemeChange={setThemePreference}
        onOpenLogin={() => setIsLoginOpen(true)}
        onOpenRegister={() => setIsRegisterOpen(true)}
        onLogout={handleLogout}
      />

      {/* Main Content Area */}
      <main style={{ flex: 1, padding: '20px 16px', maxWidth: '1360px', margin: '0 auto', width: '100%' }}>
        {/* PUBLIC HOME / LANDING */}
        {activeTab === 'LANDING' && (
          <LandingPage
            onStartSymptoms={() => {
              setIsVoiceIntakeOpen(true);
            }}
            onOpenHospitals={(query) => {
              if (query) setHospitalSearchQuery(query);
              setActiveTab('FIND_HOSPITAL');
            }}
            onBookAppointment={() => setActiveTab('BOOK_APPOINTMENT')}
            onOpenEmergency={() => setIsEmergencyOpen(true)}
            onOpenFinancialAssistance={() => setActiveTab('FINANCIAL_SUPPORT')}
            onSelectRole={handleRoleChange}
            onOpenLogin={() => setIsLoginOpen(true)}
            onOpenRegister={() => setIsRegisterOpen(true)}
          />
        )}

        {/* PROTECTED ROUTE AUTHENTICATION BARRIER */}
        {!isAuthenticated && ['DASHBOARD', 'PATIENT_APPOINTMENTS', 'HEALTH_PROFILE', 'SETTINGS', 'BOOK_APPOINTMENT', 'DOCTOR_DASHBOARD', 'HOSPITAL_DASHBOARD'].includes(activeTab) && (
          <div style={{ maxWidth: '580px', margin: '40px auto', padding: '32px', background: 'var(--bg-card)', borderRadius: '16px', border: '1px solid var(--border-light)', textAlign: 'center', boxShadow: 'var(--shadow-lg)' }}>
            <div style={{ width: '56px', height: '56px', borderRadius: '14px', background: 'rgba(2, 132, 199, 0.12)', color: 'var(--primary-teal)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 16px' }}>
              <Lock size={28} />
            </div>
            <h2 style={{ fontSize: '1.4rem', color: 'var(--text-heading)', margin: '0 0 8px' }}>
              Authentication Required
            </h2>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '24px', lineHeight: 1.5 }}>
              You are attempting to access a protected portal ({activeTab.replace('_', ' ')}). Please sign in with your verified credentials to continue.
            </p>
            <div style={{ display: 'flex', gap: '12px', justifyContent: 'center' }}>
              <button onClick={() => setIsLoginOpen(true)} className="btn btn-primary" style={{ padding: '10px 20px' }}>
                Sign In to Portal
              </button>
              <button onClick={() => setIsRegisterOpen(true)} className="btn btn-secondary" style={{ padding: '10px 20px' }}>
                Create Patient Account
              </button>
            </div>
          </div>
        )}

        {/* ROLE-BASED ACCESS GATE FOR DOCTOR DASHBOARD */}
        {isAuthenticated && activeTab === 'DOCTOR_DASHBOARD' && currentRole !== 'DOCTOR' && (
          <div style={{ maxWidth: '580px', margin: '40px auto', padding: '32px', background: 'var(--bg-card)', borderRadius: '16px', border: '1px solid var(--border-light)', textAlign: 'center', boxShadow: 'var(--shadow-lg)' }}>
            <div style={{ width: '56px', height: '56px', borderRadius: '14px', background: 'rgba(239, 68, 68, 0.12)', color: 'var(--danger-red)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 16px' }}>
              <ShieldAlert size={28} />
            </div>
            <h2 style={{ fontSize: '1.4rem', color: 'var(--text-heading)', margin: '0 0 8px' }}>
              Doctor Access Denied
            </h2>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '24px', lineHeight: 1.5 }}>
              Your account is authenticated as <strong>{currentRole}</strong>. The Doctor Workspace is strictly restricted to verified clinical practitioners.
            </p>
            <button onClick={() => setActiveTab('DASHBOARD')} className="btn btn-primary" style={{ padding: '10px 20px' }}>
              Return to Your Dashboard
            </button>
          </div>
        )}

        {/* ROLE-BASED ACCESS GATE FOR HOSPITAL DASHBOARD */}
        {isAuthenticated && activeTab === 'HOSPITAL_DASHBOARD' && currentRole !== 'HOSPITAL_ADMIN' && (
          <div style={{ maxWidth: '580px', margin: '40px auto', padding: '32px', background: 'var(--bg-card)', borderRadius: '16px', border: '1px solid var(--border-light)', textAlign: 'center', boxShadow: 'var(--shadow-lg)' }}>
            <div style={{ width: '56px', height: '56px', borderRadius: '14px', background: 'rgba(239, 68, 68, 0.12)', color: 'var(--danger-red)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 16px' }}>
              <ShieldAlert size={28} />
            </div>
            <h2 style={{ fontSize: '1.4rem', color: 'var(--text-heading)', margin: '0 0 8px' }}>
              Hospital Admin Access Denied
            </h2>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '24px', lineHeight: 1.5 }}>
              Your account is authenticated as <strong>{currentRole}</strong>. The Hospital Admin & Check-In Portal is strictly restricted to authorized hospital administrative staff.
            </p>
            <button onClick={() => setActiveTab('DASHBOARD')} className="btn btn-primary" style={{ padding: '10px 20px' }}>
              Return to Your Dashboard
            </button>
          </div>
        )}

        {/* PATIENT DASHBOARD */}
        {isAuthenticated && activeTab === 'DASHBOARD' && currentRole === 'PATIENT' && (
          <PatientDashboard
            onOpenVoiceIntake={() => setIsVoiceIntakeOpen(true)}
            onOpenOCR={() => setIsOCROpen(true)}
            onOpenHealthProfile={() => setActiveTab('HEALTH_PROFILE')}
            onOpenTriage={() => setActiveTab('TRIAGE')}
            onOpenHospitals={() => setActiveTab('FIND_HOSPITAL')}
            onOpenBookAppointment={() => setActiveTab('BOOK_APPOINTMENT')}
            onOpenMyAppointments={() => setActiveTab('PATIENT_APPOINTMENTS')}
            onOpenFinancialSupport={() => setActiveTab('FINANCIAL_SUPPORT')}
            onOpenFinancePlanner={() => setIsFinancePlannerOpen(true)}
            onOpenEmergency={() => setIsEmergencyOpen(true)}
          />
        )}

        {/* PATIENT APPOINTMENT BOOKING WORKFLOW (4-Step Wizard) */}
        {isAuthenticated && activeTab === 'BOOK_APPOINTMENT' && (
          <AppointmentBookingWorkflow
            initialHospital={selectedHospital}
            onBookingComplete={handleBookingConfirmed}
            onCancel={() => setActiveTab('FIND_HOSPITAL')}
          />
        )}

        {/* PATIENT APPOINTMENTS LIST & QR PASSES */}
        {isAuthenticated && activeTab === 'PATIENT_APPOINTMENTS' && (
          <PatientAppointmentsView
            onBookNew={() => setActiveTab('BOOK_APPOINTMENT')}
            onNavigateHospitals={() => setActiveTab('FIND_HOSPITAL')}
          />
        )}

        {/* PATIENT HEALTH PROFILE & RECORDS */}
        {isAuthenticated && activeTab === 'HEALTH_PROFILE' && (
          <HealthProfileView
            onOpenUploadOCR={() => setIsOCROpen(true)}
          />
        )}

        {/* PATIENT AI CLINICAL TRIAGE */}
        {activeTab === 'TRIAGE' && (
          <AITriageView
            onTriageComplete={() => db.updateCareStage(4)}
            onNavigateHospitals={() => setActiveTab('FIND_HOSPITAL')}
            onNavigateEmergency={() => setIsEmergencyOpen(true)}
          />
        )}

        {/* HOSPITAL DIRECTORY & FINDER */}
        {activeTab === 'FIND_HOSPITAL' && (
          <HospitalFinder
            initialSearchQuery={hospitalSearchQuery}
            onSelectHospital={handleSelectHospital}
            onOpenCompare={() => setIsCompareOpen(true)}
          />
        )}

        {/* FINANCIAL SUPPORT & PM-JAY DIRECTORY */}
        {activeTab === 'FINANCIAL_SUPPORT' && (
          <FinancialSupportView
            onOpenPlanner={() => setIsFinancePlannerOpen(true)}
          />
        )}

        {/* PATIENT PROFILE & SETTINGS */}
        {isAuthenticated && activeTab === 'SETTINGS' && (
          <PatientSettingsView
            themePreference={themePreference}
            onChangeThemePreference={setThemePreference}
            onLogout={handleLogout}
            onResetDemo={handleResetDemo}
          />
        )}

        {/* DOCTOR CLINICAL WORKSPACE */}
        {isAuthenticated && activeTab === 'DOCTOR_DASHBOARD' && currentRole === 'DOCTOR' && (
          <DoctorDashboard
            onCostEstimateCreated={() => {
              setActiveTab('FINANCIAL_SUPPORT');
              alert('Treatment Cost Estimate saved! Switched to Financial Support view.');
            }}
          />
        )}

        {/* HOSPITAL ADMIN & CHECK-IN DASHBOARD */}
        {isAuthenticated && activeTab === 'HOSPITAL_DASHBOARD' && currentRole === 'HOSPITAL_ADMIN' && (
          <HospitalAdminDashboard
            onConsentRequested={() => {
              alert('Consent access requested! Patient can approve from Health Profile.');
            }}
          />
        )}
      </main>

      {/* Global Modals & Utilities */}
      <LoginModal
        isOpen={isLoginOpen}
        onClose={() => setIsLoginOpen(false)}
        onLoginSuccess={handleLoginSuccess}
        onOpenRegister={() => setIsRegisterOpen(true)}
      />

      <RegisterModal
        isOpen={isRegisterOpen}
        onClose={() => setIsRegisterOpen(false)}
        onRegisterSuccess={handleLoginSuccess}
        onOpenLogin={() => setIsLoginOpen(true)}
      />

      <EmergencyModal
        isOpen={isEmergencyOpen}
        onClose={() => setIsEmergencyOpen(false)}
        onSelectHospital={handleSelectHospital}
      />

      <VoiceIntakeModal
        isOpen={isVoiceIntakeOpen}
        onClose={() => setIsVoiceIntakeOpen(false)}
        onIntakeComplete={() => {
          setActiveTab('TRIAGE');
        }}
      />

      <MedicalRecordOCR
        isOpen={isOCROpen}
        onClose={() => setIsOCROpen(false)}
        onRecordSaved={() => {
          setActiveTab('HEALTH_PROFILE');
        }}
      />

      <OPDRegistrationModal
        isOpen={isOPDModalOpen}
        selectedHospital={selectedHospital}
        onClose={() => setIsOPDModalOpen(false)}
        onBookingConfirmed={handleBookingConfirmed}
      />

      <HospitalCompare
        isOpen={isCompareOpen}
        onClose={() => setIsCompareOpen(false)}
        onSelectHospital={handleSelectHospital}
      />

      <AIFinancePlanner
        isOpen={isFinancePlannerOpen}
        onClose={() => setIsFinancePlannerOpen(false)}
      />

      {/* Digital QR Visit Pass Modal */}
      {isQRModalOpen && activeOPDPass && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(15, 23, 42, 0.75)',
          backdropFilter: 'blur(5px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1100,
          padding: '16px'
        }}>
          <div style={{
            background: 'var(--bg-card)',
            borderRadius: '16px',
            maxWidth: '640px',
            width: '100%',
            maxHeight: '90vh',
            overflowY: 'auto',
            position: 'relative',
            border: '1px solid var(--border-light)',
            boxShadow: 'var(--shadow-xl)',
            padding: '20px'
          }}>
            <button
              onClick={() => setIsQRModalOpen(false)}
              className="btn btn-secondary btn-sm"
              style={{ position: 'absolute', top: '16px', right: '16px', padding: '6px' }}
              title="Close QR Pass"
            >
              <X size={18} />
            </button>

            <HospitalPassQR
              opd={activeOPDPass}
              onSimulateHospitalVerify={() => {
                db.verifyQRPass(activeOPDPass.referenceId, 'Staff Desk Reception');
                const updated = db.getOPDRegistrations().find(r => r.referenceId === activeOPDPass.referenceId);
                if (updated) setActiveOPDPass(updated);
                alert(`Appointment Reference ${activeOPDPass.referenceId} verified successfully!`);
              }}
            />

            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '12px' }}>
              <button
                onClick={() => setIsQRModalOpen(false)}
                className="btn btn-primary btn-sm"
              >
                Close Pass
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Mobile Fixed 5-Tab Bottom Navigation */}
      <nav className="mobile-bottom-nav">
        <button
          onClick={() => setActiveTab('LANDING')}
          style={{
            background: 'none',
            border: 'none',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: '2px',
            color: activeTab === 'LANDING' ? 'var(--primary-teal)' : 'var(--text-muted)',
            fontSize: '0.68rem',
            fontWeight: activeTab === 'LANDING' ? 700 : 500,
            cursor: 'pointer'
          }}
        >
          <Home size={18} />
          <span>Home</span>
        </button>

        <button
          onClick={() => setActiveTab('FIND_HOSPITAL')}
          style={{
            background: 'none',
            border: 'none',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: '2px',
            color: activeTab === 'FIND_HOSPITAL' ? 'var(--primary-teal)' : 'var(--text-muted)',
            fontSize: '0.68rem',
            fontWeight: activeTab === 'FIND_HOSPITAL' ? 700 : 500,
            cursor: 'pointer'
          }}
        >
          <Building2 size={18} />
          <span>Hospitals</span>
        </button>

        {currentRole === 'PATIENT' && (
          <button
            onClick={() => setActiveTab('BOOK_APPOINTMENT')}
            style={{
              background: 'none',
              border: 'none',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: '2px',
              color: (activeTab === 'BOOK_APPOINTMENT' || activeTab === 'PATIENT_APPOINTMENTS') ? 'var(--primary-teal)' : 'var(--text-muted)',
              fontSize: '0.68rem',
              fontWeight: (activeTab === 'BOOK_APPOINTMENT' || activeTab === 'PATIENT_APPOINTMENTS') ? 700 : 500,
              cursor: 'pointer'
            }}
          >
            <Calendar size={18} />
            <span>Book OPD</span>
          </button>
        )}

        {currentRole === 'DOCTOR' && (
          <button
            onClick={() => setActiveTab('DOCTOR_DASHBOARD')}
            style={{
              background: 'none',
              border: 'none',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: '2px',
              color: activeTab === 'DOCTOR_DASHBOARD' ? 'var(--primary-teal)' : 'var(--text-muted)',
              fontSize: '0.68rem',
              fontWeight: activeTab === 'DOCTOR_DASHBOARD' ? 700 : 500,
              cursor: 'pointer'
            }}
          >
            <Stethoscope size={18} />
            <span>Workspace</span>
          </button>
        )}

        {currentRole === 'HOSPITAL_ADMIN' && (
          <button
            onClick={() => setActiveTab('HOSPITAL_DASHBOARD')}
            style={{
              background: 'none',
              border: 'none',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: '2px',
              color: activeTab === 'HOSPITAL_DASHBOARD' ? 'var(--primary-teal)' : 'var(--text-muted)',
              fontSize: '0.68rem',
              fontWeight: activeTab === 'HOSPITAL_DASHBOARD' ? 700 : 500,
              cursor: 'pointer'
            }}
          >
            <Building2 size={18} />
            <span>Check-In</span>
          </button>
        )}

        <button
          onClick={() => setActiveTab('HEALTH_PROFILE')}
          style={{
            background: 'none',
            border: 'none',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: '2px',
            color: activeTab === 'HEALTH_PROFILE' ? 'var(--primary-teal)' : 'var(--text-muted)',
            fontSize: '0.68rem',
            fontWeight: activeTab === 'HEALTH_PROFILE' ? 700 : 500,
            cursor: 'pointer'
          }}
        >
          <FileText size={18} />
          <span>Records</span>
        </button>

        <button
          onClick={() => setActiveTab('SETTINGS')}
          style={{
            background: 'none',
            border: 'none',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: '2px',
            color: activeTab === 'SETTINGS' ? 'var(--primary-teal)' : 'var(--text-muted)',
            fontSize: '0.68rem',
            fontWeight: activeTab === 'SETTINGS' ? 700 : 500,
            cursor: 'pointer'
          }}
        >
          <Settings size={18} />
          <span>Profile</span>
        </button>
      </nav>

      {/* Global Footer */}
      <Footer
        onNavigate={setActiveTab}
        onSelectRole={handleRoleChange}
        onOpenEmergency={() => setIsEmergencyOpen(true)}
      />
    </div>
  );
};
