import React, { useState } from 'react';
import { db } from '../../db/database';
import { patientService } from '../../services/apiServices';
import {
  User,
  Heart,
  Globe,
  Sun,
  Moon,
  Laptop,
  LogOut,
  CheckCircle2,
  RotateCcw
} from 'lucide-react';
import { Button, Card, Badge, ConfirmationDialog } from '../common/UIComponents';

interface Props {
  themePreference: 'light' | 'dark' | 'system';
  onChangeThemePreference: (pref: 'light' | 'dark' | 'system') => void;
  onLogout: () => void;
  onResetDemo: () => void;
}

export const PatientSettingsView: React.FC<Props> = ({
  themePreference,
  onChangeThemePreference,
  onLogout,
  onResetDemo
}) => {
  const profile = db.getPatientProfile();

  const [fullName, setFullName] = useState(profile.fullName);
  const [email, setEmail] = useState(profile.email);
  const [phone, setPhone] = useState(profile.phone);
  const [address, setAddress] = useState(profile.address);
  const [city, setCity] = useState(profile.city);
  const [pincode, setPincode] = useState(profile.pincode);

  const [emergencyName, setEmergencyName] = useState(profile.emergencyContact.name);
  const [emergencyPhone, setEmergencyPhone] = useState(profile.emergencyContact.phone);
  const [emergencyRelation, setEmergencyRelation] = useState(profile.emergencyContact.relationship);

  const [language, setLanguage] = useState<string>(() => localStorage.getItem('chikitsax_lang') || 'English');
  const [smsNotifications, setSmsNotifications] = useState(true);
  const [whatsappNotifications, setWhatsappNotifications] = useState(true);

  const [isSaved, setIsSaved] = useState(false);
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false);

  const handleSave = () => {
    patientService.updateProfile({
      fullName,
      email,
      phone,
      address,
      city,
      pincode,
      emergencyContact: {
        name: emergencyName,
        phone: emergencyPhone,
        relationship: emergencyRelation
      }
    });
    localStorage.setItem('chikitsax_lang', language);
    setIsSaved(true);
    setTimeout(() => setIsSaved(false), 3000);
  };

  return (
    <div style={{ maxWidth: '820px', margin: '0 auto', padding: '10px 0 40px' }}>
      {/* Header */}
      <div style={{ marginBottom: '24px' }}>
        <Badge variant="teal">ACCOUNT &amp; PREFERENCES</Badge>
        <h1 style={{ fontSize: '1.75rem', color: 'var(--text-heading)', margin: '4px 0 0' }}>
          Profile &amp; Application Settings
        </h1>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', margin: '4px 0 0' }}>
          Manage your personal identity, emergency contacts, appearance theme, language, and security controls.
        </p>
      </div>

      {isSaved && (
        <div
          style={{
            padding: '12px 18px',
            background: 'rgba(22, 163, 74, 0.12)',
            border: '1px solid #16A34A',
            borderRadius: '12px',
            color: '#16A34A',
            fontSize: '0.9rem',
            marginBottom: '20px',
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}
        >
          <CheckCircle2 size={18} />
          <span>Profile changes and preferences saved successfully!</span>
        </div>
      )}

      {/* 1. APPEARANCE PREFERENCE (Light, Dark, System) */}
      <Card padding="24px" style={{ marginBottom: '24px' }}>
        <h3 style={{ fontSize: '1.15rem', color: 'var(--text-heading)', margin: '0 0 4px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Sun size={18} color="var(--primary-teal)" />
          Appearance &amp; Theme
        </h3>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.84rem', margin: '0 0 16px' }}>
          Choose your visual preference. Theme changes immediately without resetting your session or active forms.
        </p>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px' }}>
          <button
            type="button"
            onClick={() => onChangeThemePreference('light')}
            style={{
              padding: '14px',
              borderRadius: '12px',
              border: themePreference === 'light' ? '2px solid var(--primary-teal)' : '1px solid var(--border-light)',
              background: themePreference === 'light' ? 'rgba(2, 132, 199, 0.12)' : 'var(--bg-subtle)',
              color: 'var(--text-heading)',
              fontWeight: 600,
              fontSize: '0.88rem',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: '6px',
              cursor: 'pointer'
            }}
          >
            <Sun size={20} color="#D97706" />
            <span>Light</span>
          </button>

          <button
            type="button"
            onClick={() => onChangeThemePreference('dark')}
            style={{
              padding: '14px',
              borderRadius: '12px',
              border: themePreference === 'dark' ? '2px solid var(--primary-teal)' : '1px solid var(--border-light)',
              background: themePreference === 'dark' ? 'rgba(2, 132, 199, 0.12)' : 'var(--bg-subtle)',
              color: 'var(--text-heading)',
              fontWeight: 600,
              fontSize: '0.88rem',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: '6px',
              cursor: 'pointer'
            }}
          >
            <Moon size={20} color="#7C3AED" />
            <span>Dark</span>
          </button>

          <button
            type="button"
            onClick={() => onChangeThemePreference('system')}
            style={{
              padding: '14px',
              borderRadius: '12px',
              border: themePreference === 'system' ? '2px solid var(--primary-teal)' : '1px solid var(--border-light)',
              background: themePreference === 'system' ? 'rgba(2, 132, 199, 0.12)' : 'var(--bg-subtle)',
              color: 'var(--text-heading)',
              fontWeight: 600,
              fontSize: '0.88rem',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: '6px',
              cursor: 'pointer'
            }}
          >
            <Laptop size={20} color="var(--primary-teal)" />
            <span>System Default</span>
          </button>
        </div>
      </Card>

      {/* 2. PERSONAL IDENTITY */}
      <Card padding="24px" style={{ marginBottom: '24px' }}>
        <h3 style={{ fontSize: '1.15rem', color: 'var(--text-heading)', margin: '0 0 16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <User size={18} color="var(--primary-teal)" />
          Personal Profile &amp; Demographics
        </h3>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px', marginBottom: '14px' }}>
          <div>
            <label className="form-label">Full Legal Name</label>
            <input
              type="text"
              value={fullName}
              onChange={e => setFullName(e.target.value)}
              className="form-control"
            />
          </div>
          <div>
            <label className="form-label">Email Address</label>
            <input
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              className="form-control"
            />
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '14px', marginBottom: '14px' }}>
          <div>
            <label className="form-label">Phone Number</label>
            <input
              type="tel"
              value={phone}
              onChange={e => setPhone(e.target.value)}
              className="form-control"
            />
          </div>
          <div>
            <label className="form-label">City</label>
            <input
              type="text"
              value={city}
              onChange={e => setCity(e.target.value)}
              className="form-control"
            />
          </div>
          <div>
            <label className="form-label">PIN Code</label>
            <input
              type="text"
              value={pincode}
              onChange={e => setPincode(e.target.value)}
              className="form-control"
            />
          </div>
        </div>

        <div>
          <label className="form-label">Residential Address</label>
          <input
            type="text"
            value={address}
            onChange={e => setAddress(e.target.value)}
            className="form-control"
          />
        </div>
      </Card>

      {/* 3. EMERGENCY CONTACT */}
      <Card padding="24px" style={{ marginBottom: '24px' }}>
        <h3 style={{ fontSize: '1.15rem', color: 'var(--text-heading)', margin: '0 0 16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Heart size={18} color="#DC2626" />
          Emergency Contact Details
        </h3>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '14px' }}>
          <div>
            <label className="form-label">Contact Name</label>
            <input
              type="text"
              value={emergencyName}
              onChange={e => setEmergencyName(e.target.value)}
              className="form-control"
            />
          </div>
          <div>
            <label className="form-label">Relationship</label>
            <input
              type="text"
              value={emergencyRelation}
              onChange={e => setEmergencyRelation(e.target.value)}
              className="form-control"
            />
          </div>
          <div>
            <label className="form-label">Emergency Phone</label>
            <input
              type="tel"
              value={emergencyPhone}
              onChange={e => setEmergencyPhone(e.target.value)}
              className="form-control"
            />
          </div>
        </div>
      </Card>

      {/* 4. LANGUAGE & NOTIFICATIONS */}
      <Card padding="24px" style={{ marginBottom: '24px' }}>
        <h3 style={{ fontSize: '1.15rem', color: 'var(--text-heading)', margin: '0 0 16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Globe size={18} color="var(--primary-teal)" />
          Language &amp; Communication Preferences
        </h3>

        <div style={{ marginBottom: '16px' }}>
          <label className="form-label">Primary Interface Language</label>
          <select
            value={language}
            onChange={e => setLanguage(e.target.value)}
            className="form-control"
            style={{ maxWidth: '300px' }}
          >
            <option value="English">English</option>
            <option value="Hindi">हिंदी (Hindi)</option>
            <option value="Marathi">मराठी (Marathi)</option>
          </select>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontSize: '0.88rem' }}>
            <input
              type="checkbox"
              checked={smsNotifications}
              onChange={e => setSmsNotifications(e.target.checked)}
              style={{ width: '16px', height: '16px', accentColor: 'var(--primary-teal)' }}
            />
            <span>Receive SMS reminders for OPD appointment tokens</span>
          </label>

          <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontSize: '0.88rem' }}>
            <input
              type="checkbox"
              checked={whatsappNotifications}
              onChange={e => setWhatsappNotifications(e.target.checked)}
              style={{ width: '16px', height: '16px', accentColor: 'var(--primary-teal)' }}
            />
            <span>Receive WhatsApp digital QR pass and prescription alerts</span>
          </label>
        </div>
      </Card>

      {/* Save Button */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
        <div style={{ display: 'flex', gap: '10px' }}>
          <Button variant="danger" size="sm" onClick={() => setShowLogoutConfirm(true)} leftIcon={<LogOut size={14} />}>
            Sign Out
          </Button>
          <Button variant="ghost" size="sm" onClick={onResetDemo} leftIcon={<RotateCcw size={14} />}>
            Reset Demo Data
          </Button>
        </div>

        <Button variant="teal" onClick={handleSave} leftIcon={<CheckCircle2 size={16} />}>
          Save Settings &amp; Preferences
        </Button>
      </div>

      <ConfirmationDialog
        isOpen={showLogoutConfirm}
        title="Sign Out of CHIKITSA-X?"
        message="You will be logged out of your session. You can sign back in at any time with your credentials or one-click demo accounts."
        confirmLabel="Sign Out"
        confirmVariant="danger"
        onConfirm={onLogout}
        onCancel={() => setShowLogoutConfirm(false)}
      />
    </div>
  );
};
