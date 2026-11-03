import React, { useState } from 'react';
import type { UserRole } from '../../types';
import { db } from '../../db/database';
import { 
  AlertCircle, 
  RotateCcw, 
  HeartPulse, 
  Sun, 
  Moon, 
  Laptop, 
  LogIn, 
  LogOut, 
  Menu, 
  X, 
  Calendar, 
  FileText, 
  Building2, 
  DollarSign, 
  Settings, 
  Activity, 
  Stethoscope 
} from 'lucide-react';

interface Props {
  currentRole: UserRole;
  activeTab: string;
  setActiveTab: (tab: string) => void;
  onOpenEmergency: () => void;
  onResetDemo: () => void;
  themePreference: 'light' | 'dark' | 'system';
  onThemeChange: (pref: 'light' | 'dark' | 'system') => void;
  onOpenLogin: () => void;
  onOpenRegister: () => void;
  onLogout: () => void;
}

export const Header: React.FC<Props> = ({
  currentRole,
  activeTab,
  setActiveTab,
  onOpenEmergency,
  onResetDemo,
  themePreference,
  onThemeChange,
  onOpenLogin,
  onOpenRegister,
  onLogout
}) => {
  const currentUser = db.getCurrentUser();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [showThemeMenu, setShowThemeMenu] = useState(false);

  const handleNav = (tab: string) => {
    setActiveTab(tab);
    setMobileMenuOpen(false);
  };

  const getThemeIcon = () => {
    if (themePreference === 'light') return <Sun size={15} color="#F59E0B" />;
    if (themePreference === 'dark') return <Moon size={15} color="#818CF8" />;
    return <Laptop size={15} color="var(--primary-teal)" />;
  };

  const getThemeLabel = () => {
    if (themePreference === 'light') return 'Light';
    if (themePreference === 'dark') return 'Dark';
    return 'System';
  };

  return (
    <header style={{
      background: 'var(--bg-header)',
      borderBottom: '1px solid var(--border-light)',
      position: 'sticky',
      top: 0,
      zIndex: 100,
      boxShadow: 'var(--shadow-sm)',
      transition: 'background 0.2s ease, border-color 0.2s ease'
    }}>
      <div style={{
        maxWidth: '1360px',
        margin: '0 auto',
        padding: '10px 16px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: '12px'
      }}>
        {/* Brand Logo */}
        <div 
          style={{ display: 'flex', alignItems: 'center', gap: '10px', cursor: 'pointer', flexShrink: 0 }} 
          onClick={() => handleNav('LANDING')}
          title="Return to CHIKITSA-X Home"
        >
          <div style={{
            background: 'linear-gradient(135deg, #0284C7 0%, #0F172A 100%)',
            padding: '9px',
            borderRadius: '10px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#FFF',
            boxShadow: '0 3px 10px rgba(2, 132, 199, 0.35)'
          }}>
            <HeartPulse size={24} />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ fontSize: '1.35rem', fontWeight: 800, fontFamily: 'Outfit, sans-serif', color: 'var(--text-heading)', letterSpacing: '-0.02em' }}>
                CHIKITSA<span style={{ color: 'var(--primary-teal)' }}>-X</span>
              </span>
              <span className="badge badge-purple" style={{ fontSize: '0.65rem', padding: '1px 5px', fontWeight: 700 }}>
                HEALTH-AI
              </span>
            </div>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.7rem', margin: 0, display: 'none' }} className="desktop-tagline">
              Connected Healthcare & Care Navigation
            </p>
          </div>
        </div>

        {/* Desktop Navigation Links */}
        <nav style={{ display: 'flex', alignItems: 'center', gap: '4px', flexWrap: 'wrap' }} className="desktop-nav">
          <button
            onClick={() => handleNav('LANDING')}
            className={`btn btn-sm ${activeTab === 'LANDING' ? 'btn-primary' : 'btn-secondary'}`}
            style={{ fontSize: '0.82rem', padding: '6px 11px' }}
          >
            Home
          </button>

          {currentRole === 'PATIENT' && (
            <>
              <button
                onClick={() => handleNav('DASHBOARD')}
                className={`btn btn-sm ${activeTab === 'DASHBOARD' ? 'btn-primary' : 'btn-secondary'}`}
                style={{ fontSize: '0.82rem', padding: '6px 11px', display: 'inline-flex', alignItems: 'center', gap: '5px' }}
              >
                <Activity size={14} /> Dashboard
              </button>
              <button
                onClick={() => handleNav('FIND_HOSPITAL')}
                className={`btn btn-sm ${activeTab === 'FIND_HOSPITAL' ? 'btn-primary' : 'btn-secondary'}`}
                style={{ fontSize: '0.82rem', padding: '6px 11px', display: 'inline-flex', alignItems: 'center', gap: '5px' }}
              >
                <Building2 size={14} /> Find Hospitals
              </button>
              <button
                onClick={() => handleNav('BOOK_APPOINTMENT')}
                className={`btn btn-sm ${activeTab === 'BOOK_APPOINTMENT' ? 'btn-primary' : 'btn-secondary'}`}
                style={{ fontSize: '0.82rem', padding: '6px 11px', display: 'inline-flex', alignItems: 'center', gap: '5px' }}
              >
                <Calendar size={14} /> Book OPD
              </button>
              <button
                onClick={() => handleNav('PATIENT_APPOINTMENTS')}
                className={`btn btn-sm ${activeTab === 'PATIENT_APPOINTMENTS' ? 'btn-primary' : 'btn-secondary'}`}
                style={{ fontSize: '0.82rem', padding: '6px 11px', display: 'inline-flex', alignItems: 'center', gap: '5px' }}
              >
                My Bookings
              </button>
              <button
                onClick={() => handleNav('HEALTH_PROFILE')}
                className={`btn btn-sm ${activeTab === 'HEALTH_PROFILE' ? 'btn-primary' : 'btn-secondary'}`}
                style={{ fontSize: '0.82rem', padding: '6px 11px', display: 'inline-flex', alignItems: 'center', gap: '5px' }}
              >
                <FileText size={14} /> Records
              </button>
              <button
                onClick={() => handleNav('FINANCIAL_SUPPORT')}
                className={`btn btn-sm ${activeTab === 'FINANCIAL_SUPPORT' ? 'btn-primary' : 'btn-secondary'}`}
                style={{ fontSize: '0.82rem', padding: '6px 11px', display: 'inline-flex', alignItems: 'center', gap: '5px' }}
              >
                <DollarSign size={14} /> Schemes & Aid
              </button>
            </>
          )}

          {currentRole === 'DOCTOR' && (
            <>
              <button
                onClick={() => handleNav('DOCTOR_DASHBOARD')}
                className={`btn btn-sm ${activeTab === 'DOCTOR_DASHBOARD' ? 'btn-purple' : 'btn-secondary'}`}
                style={{ fontSize: '0.82rem', padding: '6px 11px', display: 'inline-flex', alignItems: 'center', gap: '5px' }}
              >
                <Stethoscope size={14} /> Doctor Workspace
              </button>
              <button
                onClick={() => handleNav('FIND_HOSPITAL')}
                className={`btn btn-sm ${activeTab === 'FIND_HOSPITAL' ? 'btn-primary' : 'btn-secondary'}`}
                style={{ fontSize: '0.82rem', padding: '6px 11px' }}
              >
                Hospital Directory
              </button>
            </>
          )}

          {currentRole === 'HOSPITAL_ADMIN' && (
            <>
              <button
                onClick={() => handleNav('HOSPITAL_DASHBOARD')}
                className={`btn btn-sm ${activeTab === 'HOSPITAL_DASHBOARD' ? 'btn-green' : 'btn-secondary'}`}
                style={{ fontSize: '0.82rem', padding: '6px 11px', display: 'inline-flex', alignItems: 'center', gap: '5px' }}
              >
                <Building2 size={14} /> Hospital Admin & Check-In
              </button>
              <button
                onClick={() => handleNav('FIND_HOSPITAL')}
                className={`btn btn-sm ${activeTab === 'FIND_HOSPITAL' ? 'btn-primary' : 'btn-secondary'}`}
                style={{ fontSize: '0.82rem', padding: '6px 11px' }}
              >
                Hospital Network
              </button>
            </>
          )}
        </nav>

        {/* Right Controls: Appearance, Emergency, Auth, Demo */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {/* Appearance Preference Switcher (Light / Dark / System) */}
          <div style={{ position: 'relative' }}>
            <button
              onClick={() => setShowThemeMenu(!showThemeMenu)}
              className="btn btn-secondary btn-sm"
              title={`Appearance: ${getThemeLabel()} (Click to change)`}
              style={{ padding: '6px 10px', display: 'inline-flex', alignItems: 'center', gap: '5px', fontSize: '0.8rem' }}
            >
              {getThemeIcon()}
              <span className="hide-on-mobile">{getThemeLabel()}</span>
            </button>

            {showThemeMenu && (
              <div 
                style={{
                  position: 'absolute',
                  top: '110%',
                  right: 0,
                  background: 'var(--bg-card)',
                  border: '1px solid var(--border-light)',
                  borderRadius: '10px',
                  boxShadow: 'var(--shadow-md)',
                  padding: '6px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '4px',
                  zIndex: 200,
                  minWidth: '120px'
                }}
              >
                <button
                  onClick={() => { onThemeChange('light'); setShowThemeMenu(false); }}
                  className={`btn btn-sm ${themePreference === 'light' ? 'btn-primary' : 'btn-secondary'}`}
                  style={{ justifyContent: 'flex-start', fontSize: '0.78rem', padding: '5px 8px' }}
                >
                  <Sun size={14} color="#F59E0B" /> Light
                </button>
                <button
                  onClick={() => { onThemeChange('dark'); setShowThemeMenu(false); }}
                  className={`btn btn-sm ${themePreference === 'dark' ? 'btn-primary' : 'btn-secondary'}`}
                  style={{ justifyContent: 'flex-start', fontSize: '0.78rem', padding: '5px 8px' }}
                >
                  <Moon size={14} color="#818CF8" /> Dark
                </button>
                <button
                  onClick={() => { onThemeChange('system'); setShowThemeMenu(false); }}
                  className={`btn btn-sm ${themePreference === 'system' ? 'btn-primary' : 'btn-secondary'}`}
                  style={{ justifyContent: 'flex-start', fontSize: '0.78rem', padding: '5px 8px' }}
                >
                  <Laptop size={14} color="var(--primary-teal)" /> System
                </button>
              </div>
            )}
          </div>

          {/* EMERGENCY Button */}
          <button
            onClick={onOpenEmergency}
            className="btn btn-emergency-pulse btn-sm"
            style={{ padding: '6px 11px', display: 'inline-flex', alignItems: 'center', gap: '5px', fontWeight: 700, fontSize: '0.8rem' }}
            title="Immediate Medical Emergency Services"
          >
            <AlertCircle size={15} /> <span className="hide-on-mobile">EMERGENCY</span>
          </button>

          {/* User Profile Pill / Auth Buttons */}
          {currentUser ? (
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              background: 'var(--bg-card)',
              padding: '3px 8px',
              borderRadius: '20px',
              border: '1px solid var(--border-light)',
              fontSize: '0.8rem'
            }}>
              <img
                src={currentUser.avatar || 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&q=80&w=150'}
                alt={currentUser.name}
                style={{ width: '26px', height: '26px', borderRadius: '50%', objectFit: 'cover' }}
              />
              <div style={{ display: 'flex', flexDirection: 'column' }} className="hide-on-mobile">
                <span style={{ fontWeight: 600, color: 'var(--text-main)', lineHeight: 1.1, maxWidth: '100px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {currentUser.name}
                </span>
                <span style={{ color: 'var(--primary-teal)', fontSize: '0.68rem', fontWeight: 700 }}>
                  {currentRole.replace('_', ' ')}
                </span>
              </div>
              <button
                onClick={() => handleNav('SETTINGS')}
                title="Account Settings"
                className="btn btn-secondary btn-sm"
                style={{ padding: '4px', border: 'none', background: 'transparent' }}
              >
                <Settings size={15} color="var(--text-muted)" />
              </button>
              <button
                onClick={onLogout}
                title="Sign Out"
                className="btn btn-secondary btn-sm"
                style={{ padding: '4px', border: 'none', background: 'transparent', color: 'var(--danger-red)' }}
              >
                <LogOut size={15} />
              </button>
            </div>
          ) : (
            <div style={{ display: 'flex', gap: '6px' }}>
              <button onClick={onOpenLogin} className="btn btn-secondary btn-sm" style={{ padding: '6px 10px', fontSize: '0.8rem' }}>
                <LogIn size={13} /> Sign In
              </button>
              <button onClick={onOpenRegister} className="btn btn-primary btn-sm hide-on-mobile" style={{ padding: '6px 10px', fontSize: '0.8rem' }}>
                Register
              </button>
            </div>
          )}

          {/* Reset Demo State button */}
          <button
            onClick={onResetDemo}
            title="Reset All Demo Data (for SIH evaluators)"
            className="btn btn-secondary btn-sm hide-on-mobile"
            style={{ padding: '6px 8px', color: 'var(--text-muted)' }}
          >
            <RotateCcw size={15} />
          </button>

          {/* Mobile Menu Hamburger Button */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="btn btn-secondary btn-sm mobile-menu-btn"
            style={{ padding: '6px 8px', display: 'none' }}
            title="Toggle Navigation Menu"
          >
            {mobileMenuOpen ? <X size={18} /> : <Menu size={18} />}
          </button>
        </div>
      </div>

      {/* Mobile Drawer Navigation Menu */}
      {mobileMenuOpen && (
        <div style={{
          background: 'var(--bg-card)',
          borderTop: '1px solid var(--border-light)',
          padding: '16px',
          display: 'flex',
          flexDirection: 'column',
          gap: '8px'
        }}>
          <button
            onClick={() => handleNav('LANDING')}
            className={`btn btn-sm ${activeTab === 'LANDING' ? 'btn-primary' : 'btn-secondary'}`}
            style={{ justifyContent: 'flex-start', padding: '10px 14px' }}
          >
            Home / Landing
          </button>

          {currentRole === 'PATIENT' && (
            <>
              <button
                onClick={() => handleNav('DASHBOARD')}
                className={`btn btn-sm ${activeTab === 'DASHBOARD' ? 'btn-primary' : 'btn-secondary'}`}
                style={{ justifyContent: 'flex-start', padding: '10px 14px' }}
              >
                <Activity size={16} /> Patient Dashboard
              </button>
              <button
                onClick={() => handleNav('FIND_HOSPITAL')}
                className={`btn btn-sm ${activeTab === 'FIND_HOSPITAL' ? 'btn-primary' : 'btn-secondary'}`}
                style={{ justifyContent: 'flex-start', padding: '10px 14px' }}
              >
                <Building2 size={16} /> Find Hospitals
              </button>
              <button
                onClick={() => handleNav('BOOK_APPOINTMENT')}
                className={`btn btn-sm ${activeTab === 'BOOK_APPOINTMENT' ? 'btn-primary' : 'btn-secondary'}`}
                style={{ justifyContent: 'flex-start', padding: '10px 14px' }}
              >
                <Calendar size={16} /> Book OPD Appointment
              </button>
              <button
                onClick={() => handleNav('PATIENT_APPOINTMENTS')}
                className={`btn btn-sm ${activeTab === 'PATIENT_APPOINTMENTS' ? 'btn-primary' : 'btn-secondary'}`}
                style={{ justifyContent: 'flex-start', padding: '10px 14px' }}
              >
                My Bookings & QR Passes
              </button>
              <button
                onClick={() => handleNav('HEALTH_PROFILE')}
                className={`btn btn-sm ${activeTab === 'HEALTH_PROFILE' ? 'btn-primary' : 'btn-secondary'}`}
                style={{ justifyContent: 'flex-start', padding: '10px 14px' }}
              >
                <FileText size={16} /> Medical Records & Health Profile
              </button>
              <button
                onClick={() => handleNav('FINANCIAL_SUPPORT')}
                className={`btn btn-sm ${activeTab === 'FINANCIAL_SUPPORT' ? 'btn-primary' : 'btn-secondary'}`}
                style={{ justifyContent: 'flex-start', padding: '10px 14px' }}
              >
                <DollarSign size={16} /> Government Schemes & Aid
              </button>
              <button
                onClick={() => handleNav('SETTINGS')}
                className={`btn btn-sm ${activeTab === 'SETTINGS' ? 'btn-primary' : 'btn-secondary'}`}
                style={{ justifyContent: 'flex-start', padding: '10px 14px' }}
              >
                <Settings size={16} /> Settings & Profile
              </button>
            </>
          )}

          {currentRole === 'DOCTOR' && (
            <button
              onClick={() => handleNav('DOCTOR_DASHBOARD')}
              className={`btn btn-sm ${activeTab === 'DOCTOR_DASHBOARD' ? 'btn-purple' : 'btn-secondary'}`}
              style={{ justifyContent: 'flex-start', padding: '10px 14px' }}
            >
              <Stethoscope size={16} /> Doctor Workspace
            </button>
          )}

          {currentRole === 'HOSPITAL_ADMIN' && (
            <button
              onClick={() => handleNav('HOSPITAL_DASHBOARD')}
              className={`btn btn-sm ${activeTab === 'HOSPITAL_DASHBOARD' ? 'btn-green' : 'btn-secondary'}`}
              style={{ justifyContent: 'flex-start', padding: '10px 14px' }}
            >
              <Building2 size={16} /> Hospital Admin & Check-In
            </button>
          )}

          <div style={{ display: 'flex', gap: '8px', marginTop: '10px', paddingTop: '10px', borderTop: '1px solid var(--border-light)' }}>
            <button onClick={onResetDemo} className="btn btn-secondary btn-sm" style={{ flex: 1 }}>
              <RotateCcw size={14} /> Reset Demo Data
            </button>
            {currentUser && (
              <button onClick={onLogout} className="btn btn-danger btn-sm" style={{ flex: 1 }}>
                <LogOut size={14} /> Sign Out
              </button>
            )}
          </div>
        </div>
      )}
    </header>
  );
};
