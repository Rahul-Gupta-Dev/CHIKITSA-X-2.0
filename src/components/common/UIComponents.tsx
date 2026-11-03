import React from 'react';
import { Loader2, AlertTriangle, Info } from 'lucide-react';

/* =========================================================================
   1. BUTTON COMPONENT
   ========================================================================= */
export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'teal' | 'danger' | 'emergency' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  isLoading = false,
  leftIcon,
  rightIcon,
  disabled,
  className = '',
  style,
  ...props
}) => {
  const sizeStyles: Record<string, React.CSSProperties> = {
    sm: { padding: '6px 14px', fontSize: '0.85rem', minHeight: '36px', borderRadius: '8px' },
    md: { padding: '10px 18px', fontSize: '0.92rem', minHeight: '44px', borderRadius: '10px' },
    lg: { padding: '14px 24px', fontSize: '1.02rem', minHeight: '50px', borderRadius: '12px' }
  };

  const getVariantStyle = (): React.CSSProperties => {
    switch (variant) {
      case 'primary':
        return {
          background: 'linear-gradient(135deg, #0F172A 0%, #1E293B 100%)',
          color: '#FFFFFF',
          border: '1px solid rgba(255, 255, 255, 0.12)',
          boxShadow: '0 2px 8px rgba(15, 23, 42, 0.25)'
        };
      case 'teal':
        return {
          background: 'linear-gradient(135deg, #0284C7 0%, #0369A1 100%)',
          color: '#FFFFFF',
          border: 'none',
          boxShadow: '0 2px 10px rgba(2, 132, 199, 0.3)'
        };
      case 'secondary':
        return {
          background: 'var(--bg-subtle)',
          color: 'var(--text-main)',
          border: '1px solid var(--border-light)'
        };
      case 'outline':
        return {
          background: 'transparent',
          color: 'var(--primary-teal)',
          border: '1px solid var(--primary-teal)'
        };
      case 'danger':
        return {
          background: '#DC2626',
          color: '#FFFFFF',
          border: 'none',
          boxShadow: '0 2px 8px rgba(220, 38, 38, 0.3)'
        };
      case 'emergency':
        return {
          background: 'linear-gradient(135deg, #DC2626 0%, #991B1B 100%)',
          color: '#FFFFFF',
          fontWeight: 700,
          border: 'none',
          boxShadow: '0 0 12px rgba(220, 38, 38, 0.45)'
        };
      case 'ghost':
        return {
          background: 'transparent',
          color: 'var(--text-main)',
          border: 'none'
        };
      default:
        return {};
    }
  };

  const isDisabled = disabled || isLoading;

  return (
    <button
      disabled={isDisabled}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '8px',
        fontWeight: 600,
        cursor: isDisabled ? 'not-allowed' : 'pointer',
        opacity: isDisabled ? 0.65 : 1,
        transition: 'all 0.18s ease-in-out',
        ...sizeStyles[size],
        ...getVariantStyle(),
        ...style
      }}
      className={`btn ${className}`}
      {...props}
    >
      {isLoading ? <Loader2 size={18} className="spin-animate" /> : leftIcon}
      <span>{children}</span>
      {!isLoading && rightIcon}
    </button>
  );
};

/* =========================================================================
   2. BADGE COMPONENT
   ========================================================================= */
export interface BadgeProps {
  children: React.ReactNode;
  variant?: 'teal' | 'navy' | 'green' | 'amber' | 'red' | 'purple' | 'gray';
  size?: 'sm' | 'md';
  icon?: React.ReactNode;
  style?: React.CSSProperties;
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'teal',
  size = 'md',
  icon,
  style
}) => {
  const getBadgeStyle = (): React.CSSProperties => {
    switch (variant) {
      case 'teal':
        return { background: 'rgba(2, 132, 199, 0.12)', color: 'var(--primary-teal)', border: '1px solid rgba(2, 132, 199, 0.25)' };
      case 'navy':
        return { background: 'rgba(15, 23, 42, 0.08)', color: 'var(--text-heading)', border: '1px solid var(--border-dark)' };
      case 'green':
        return { background: 'rgba(22, 163, 74, 0.12)', color: '#16A34A', border: '1px solid rgba(22, 163, 74, 0.25)' };
      case 'amber':
        return { background: 'rgba(217, 119, 6, 0.12)', color: '#D97706', border: '1px solid rgba(217, 119, 6, 0.25)' };
      case 'red':
        return { background: 'rgba(220, 38, 38, 0.12)', color: '#DC2626', border: '1px solid rgba(220, 38, 38, 0.25)' };
      case 'purple':
        return { background: 'rgba(109, 40, 217, 0.12)', color: '#7C3AED', border: '1px solid rgba(109, 40, 217, 0.25)' };
      case 'gray':
      default:
        return { background: 'var(--bg-subtle)', color: 'var(--text-secondary)', border: '1px solid var(--border-light)' };
    }
  };

  const sizeStyle: React.CSSProperties = size === 'sm'
    ? { fontSize: '0.72rem', padding: '2px 8px', borderRadius: '12px' }
    : { fontSize: '0.8rem', padding: '4px 10px', borderRadius: '16px' };

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '4px',
        fontWeight: 600,
        letterSpacing: '0.02em',
        textTransform: 'uppercase',
        ...sizeStyle,
        ...getBadgeStyle(),
        ...style
      }}
    >
      {icon}
      {children}
    </span>
  );
};

/* =========================================================================
   3. CARD COMPONENT
   ========================================================================= */
export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  hoverable?: boolean;
  padding?: string | number;
}

export const Card: React.FC<CardProps> = ({
  children,
  hoverable = false,
  padding = '20px',
  className = '',
  style,
  ...props
}) => {
  return (
    <div
      style={{
        background: 'var(--bg-card)',
        border: '1px solid var(--border-light)',
        borderRadius: '16px',
        padding,
        boxShadow: 'var(--shadow-sm)',
        color: 'var(--text-main)',
        transition: hoverable ? 'transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease' : undefined,
        ...style
      }}
      className={`glass-panel ${hoverable ? 'card-hoverable' : ''} ${className}`}
      {...props}
    >
      {children}
    </div>
  );
};

/* =========================================================================
   4. STEP INDICATOR COMPONENT
   ========================================================================= */
export interface StepIndicatorProps {
  steps: string[];
  currentStep: number; // 1-based
  onStepClick?: (step: number) => void;
}

export const StepIndicator: React.FC<StepIndicatorProps> = ({ steps, currentStep, onStepClick }) => {
  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '20px 0', flexWrap: 'wrap', gap: '8px' }}>
      {steps.map((label, index) => {
        const stepNum = index + 1;
        const isCompleted = stepNum < currentStep;
        const isActive = stepNum === currentStep;

        return (
          <React.Fragment key={label}>
            <div
              onClick={() => isCompleted && onStepClick && onStepClick(stepNum)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                cursor: isCompleted ? 'pointer' : 'default',
                opacity: stepNum > currentStep ? 0.5 : 1
              }}
            >
              <div
                style={{
                  width: '32px',
                  height: '32px',
                  borderRadius: '50%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontWeight: 700,
                  fontSize: '0.85rem',
                  background: isCompleted
                    ? '#16A34A'
                    : isActive
                    ? 'var(--primary-teal)'
                    : 'var(--bg-subtle)',
                  color: (isCompleted || isActive) ? '#FFFFFF' : 'var(--text-muted)',
                  border: isActive ? '2px solid var(--primary-teal)' : '1px solid var(--border-light)',
                  transition: 'all 0.2s'
                }}
              >
                {isCompleted ? '✓' : stepNum}
              </div>
              <span
                style={{
                  fontSize: '0.88rem',
                  fontWeight: isActive ? 700 : 500,
                  color: isActive ? 'var(--text-heading)' : 'var(--text-muted)'
                }}
              >
                {label}
              </span>
            </div>

            {index < steps.length - 1 && (
              <div
                style={{
                  flex: 1,
                  maxWidth: '40px',
                  height: '2px',
                  background: isCompleted ? '#16A34A' : 'var(--border-light)',
                  margin: '0 4px'
                }}
              />
            )}
          </React.Fragment>
        );
      })}
    </div>
  );
};

/* =========================================================================
   5. EMPTY STATE COMPONENT
   ========================================================================= */
export interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description: string;
  actionLabel?: string;
  onAction?: () => void;
  actionIcon?: React.ReactNode;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon,
  title,
  description,
  actionLabel,
  onAction,
  actionIcon
}) => {
  return (
    <div
      style={{
        textAlign: 'center',
        padding: '48px 24px',
        background: 'var(--bg-card)',
        borderRadius: '16px',
        border: '1px dashed var(--border-dark)',
        margin: '20px 0'
      }}
    >
      <div
        style={{
          width: '56px',
          height: '56px',
          borderRadius: '50%',
          background: 'var(--bg-subtle)',
          color: 'var(--primary-teal)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          margin: '0 auto 16px'
        }}
      >
        {icon || <Info size={28} />}
      </div>
      <h3 style={{ fontSize: '1.15rem', color: 'var(--text-heading)', marginBottom: '8px' }}>
        {title}
      </h3>
      <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', maxWidth: '420px', margin: '0 auto 20px' }}>
        {description}
      </p>
      {actionLabel && onAction && (
        <Button variant="teal" onClick={onAction} leftIcon={actionIcon}>
          {actionLabel}
        </Button>
      )}
    </div>
  );
};

/* =========================================================================
   6. CONFIRMATION DIALOG COMPONENT
   ========================================================================= */
export interface ConfirmationDialogProps {
  isOpen: boolean;
  title: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  confirmVariant?: 'danger' | 'primary' | 'teal';
  onConfirm: () => void;
  onCancel: () => void;
}

export const ConfirmationDialog: React.FC<ConfirmationDialogProps> = ({
  isOpen,
  title,
  message,
  confirmLabel = 'Confirm',
  cancelLabel = 'Cancel',
  confirmVariant = 'danger',
  onConfirm,
  onCancel
}) => {
  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onCancel}>
      <div
        className="modal-content"
        style={{ maxWidth: '440px', padding: '24px' }}
        onClick={e => e.stopPropagation()}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
          <div
            style={{
              padding: '10px',
              borderRadius: '12px',
              background: confirmVariant === 'danger' ? 'rgba(220, 38, 38, 0.12)' : 'rgba(2, 132, 199, 0.12)',
              color: confirmVariant === 'danger' ? '#DC2626' : 'var(--primary-teal)'
            }}
          >
            <AlertTriangle size={24} />
          </div>
          <div>
            <h3 style={{ margin: 0, fontSize: '1.2rem', color: 'var(--text-heading)' }}>{title}</h3>
          </div>
        </div>

        <p style={{ color: 'var(--text-secondary)', fontSize: '0.92rem', marginBottom: '24px', lineHeight: 1.5 }}>
          {message}
        </p>

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
          <Button variant="secondary" onClick={onCancel}>
            {cancelLabel}
          </Button>
          <Button variant={confirmVariant} onClick={onConfirm}>
            {confirmLabel}
          </Button>
        </div>
      </div>
    </div>
  );
};

/* =========================================================================
   7. BREADCRUMBS COMPONENT
   ========================================================================= */
export interface BreadcrumbItem {
  label: string;
  tabKey?: string;
  active?: boolean;
}

export interface BreadcrumbsProps {
  items: BreadcrumbItem[];
  onNavigate?: (tabKey: string) => void;
}

export const Breadcrumbs: React.FC<BreadcrumbsProps> = ({ items, onNavigate }) => {
  return (
    <nav style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.85rem', margin: '8px 0 16px' }}>
      {items.map((item, index) => (
        <React.Fragment key={item.label}>
          {item.tabKey && onNavigate && !item.active ? (
            <button
              onClick={() => onNavigate(item.tabKey!)}
              style={{
                background: 'none',
                border: 'none',
                color: 'var(--primary-teal)',
                cursor: 'pointer',
                padding: 0,
                fontSize: '0.85rem',
                fontWeight: 500,
                textDecoration: 'underline'
              }}
            >
              {item.label}
            </button>
          ) : (
            <span style={{ color: item.active ? 'var(--text-heading)' : 'var(--text-muted)', fontWeight: item.active ? 600 : 400 }}>
              {item.label}
            </span>
          )}
          {index < items.length - 1 && <span style={{ color: 'var(--text-muted)' }}>/</span>}
        </React.Fragment>
      ))}
    </nav>
  );
};
