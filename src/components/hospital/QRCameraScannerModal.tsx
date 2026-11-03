import React, { useState, useEffect, useRef } from 'react';
import jsQR from 'jsqr';
import { Camera, X, Upload, CheckCircle, AlertTriangle, RefreshCw, Sparkles, QrCode } from 'lucide-react';
import { db } from '../../db/database';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onScanSuccess: (scannedRefId: string) => void;
}

export const QRCameraScannerModal: React.FC<Props> = ({ isOpen, onClose, onScanSuccess }) => {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const [hasPermission, setHasPermission] = useState<boolean | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [scannedResult, setScannedResult] = useState<string | null>(null);
  const [isScanning, setIsScanning] = useState(false);

  const streamRef = useRef<MediaStream | null>(null);
  const animationFrameIdRef = useRef<number | null>(null);

  // Play audio beep feedback on scan success
  const playScanBeep = () => {
    try {
      const audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)();
      const osc = audioCtx.createOscillator();
      const gain = audioCtx.createGain();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(880, audioCtx.currentTime); // A5 note
      gain.gain.setValueAtTime(0.2, audioCtx.currentTime);
      osc.connect(gain);
      gain.connect(audioCtx.destination);
      osc.start();
      osc.stop(audioCtx.currentTime + 0.15);
    } catch (e) {
      console.warn('Audio beep unavailable', e);
    }
  };

  // Helper to parse reference ID from raw text or JSON payload
  const extractRefId = (rawText: string): string => {
    let cleanText = rawText.trim();
    if (cleanText.startsWith('{') && cleanText.endsWith('}')) {
      try {
        const parsed = JSON.parse(cleanText);
        if (parsed.referenceId) return parsed.referenceId;
        if (parsed.refId) return parsed.refId;
        if (parsed.id) return parsed.id;
      } catch {
        // Fallback to raw text
      }
    }
    return cleanText;
  };

  // Handle successful QR detection
  const handleSuccess = (rawQrText: string) => {
    const refId = extractRefId(rawQrText);
    playScanBeep();
    setScannedResult(refId);
    stopCamera();

    setTimeout(() => {
      onScanSuccess(refId);
      onClose();
      setScannedResult(null);
    }, 900);
  };

  // Stop video camera stream
  const stopCamera = () => {
    if (animationFrameIdRef.current) {
      cancelAnimationFrame(animationFrameIdRef.current);
      animationFrameIdRef.current = null;
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    setIsScanning(false);
  };

  // Start live web camera video stream
  const startCamera = async () => {
    setErrorMessage(null);
    setHasPermission(null);
    setScannedResult(null);

    try {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error('Camera access API is not supported by your browser.');
      }

      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: { ideal: 'environment' }, width: { ideal: 1280 }, height: { ideal: 720 } }
      });

      streamRef.current = stream;
      setHasPermission(true);
      setIsScanning(true);

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.setAttribute('playsinline', 'true');
        videoRef.current.play();
        scanFrames();
      }
    } catch (err: any) {
      console.warn('Camera Error:', err);
      setHasPermission(false);
      setIsScanning(false);
      setErrorMessage(err.message || 'Camera permission denied or camera device unavailable.');
    }
  };

  // Continuous frame scanning loop using jsQR
  const scanFrames = () => {
    const video = videoRef.current;
    const canvas = canvasRef.current;

    if (!video || !canvas) return;

    if (video.readyState === video.HAVE_ENOUGH_DATA) {
      const ctx = canvas.getContext('2d');
      if (ctx) {
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
        const code = jsQR(imageData.data, imageData.width, imageData.height, {
          inversionAttempts: 'dontInvert'
        });

        if (code && code.data) {
          handleSuccess(code.data);
          return;
        }
      }
    }

    animationFrameIdRef.current = requestAnimationFrame(scanFrames);
  };

  // Handle uploaded image file scanning
  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      const img = new Image();
      img.onload = () => {
        const canvas = document.createElement('canvas');
        canvas.width = img.width;
        canvas.height = img.height;
        const ctx = canvas.getContext('2d');
        if (ctx) {
          ctx.drawImage(img, 0, 0);
          const imageData = ctx.getImageData(0, 0, img.width, img.height);
          const code = jsQR(imageData.data, imageData.width, imageData.height);
          if (code && code.data) {
            handleSuccess(code.data);
          } else {
            alert('No valid QR code found in uploaded image file. Please try another image or use camera scanner.');
          }
        }
      };
      img.src = event.target?.result as string;
    };
    reader.readAsDataURL(file);
  };

  useEffect(() => {
    if (isOpen) {
      startCamera();
    } else {
      stopCamera();
    }

    return () => {
      stopCamera();
    };
  }, [isOpen]);

  if (!isOpen) return null;

  const activeAppointments = db.getOPDRegistrations();

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" style={{ maxWidth: '580px', padding: '24px' }} onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{ background: 'linear-gradient(135deg, #10B981 0%, #059669 100%)', padding: '10px', borderRadius: '12px', color: '#FFF' }}>
              <Camera size={22} />
            </div>
            <div>
              <h3 style={{ fontSize: '1.25rem', color: 'var(--text-heading)', margin: 0 }}>Hospital Camera QR Scanner</h3>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', margin: 0 }}>Point device camera at patient's OPD digital visit pass QR code</p>
            </div>
          </div>
          <button onClick={onClose} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', padding: '4px' }}>
            <X size={22} />
          </button>
        </div>

        {/* Success Scanner Result Banner */}
        {scannedResult ? (
          <div style={{
            background: 'rgba(21, 128, 61, 0.12)',
            border: '2px solid var(--accent-green)',
            borderRadius: '16px',
            padding: '24px',
            textAlign: 'center',
            margin: '20px 0'
          }}>
            <CheckCircle size={48} color="var(--accent-green)" style={{ margin: '0 auto 12px' }} />
            <h4 style={{ color: 'var(--accent-green)', fontSize: '1.2rem', fontWeight: 800, margin: '0 0 6px' }}>
              ✓ QR CODE DECODED SUCCESSFULLY!
            </h4>
            <div style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--primary-teal)', fontFamily: 'monospace', letterSpacing: '0.05em' }}>
              Reference ID: {scannedResult}
            </div>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginTop: '8px', margin: 0 }}>
              Verifying appointment & check-in records in hospital database...
            </p>
          </div>
        ) : (
          <div>
            {/* Live Camera Viewfinder Box */}
            <div style={{
              position: 'relative',
              width: '100%',
              height: '300px',
              borderRadius: '16px',
              overflow: 'hidden',
              background: '#0F172A',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginBottom: '16px',
              border: '2px solid var(--border-light)'
            }}>
              <video
                ref={videoRef}
                style={{ width: '100%', height: '100%', objectFit: 'cover', display: hasPermission === true ? 'block' : 'none' }}
              />
              <canvas ref={canvasRef} style={{ display: 'none' }} />

              {/* Camera Scanner Reticle Target Overlay */}
              {hasPermission === true && (
                <div style={{
                  position: 'absolute',
                  inset: 0,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  pointerEvents: 'none'
                }}>
                  <div style={{
                    width: '210px',
                    height: '210px',
                    border: '3px dashed #10B981',
                    borderRadius: '20px',
                    boxShadow: '0 0 0 9999px rgba(15, 23, 42, 0.55)',
                    position: 'relative'
                  }}>
                    {/* Laser Scanner animation line */}
                    <div style={{
                      position: 'absolute',
                      top: 0,
                      left: 0,
                      right: 0,
                      height: '3px',
                      background: 'linear-gradient(90deg, transparent 0%, #10B981 50%, transparent 100%)',
                      boxShadow: '0 0 10px #10B981',
                      animation: 'scanLine 2s infinite ease-in-out'
                    }} />
                  </div>
                  <style>{`
                    @keyframes scanLine {
                      0% { top: 0%; }
                      50% { top: 96%; }
                      100% { top: 0%; }
                    }
                  `}</style>
                </div>
              )}

              {/* Camera Permission / Error Fallback Screen */}
              {hasPermission === false && (
                <div style={{ textAlign: 'center', padding: '20px', color: '#F87171' }}>
                  <AlertTriangle size={42} style={{ margin: '0 auto 12px' }} />
                  <div style={{ fontWeight: 700, fontSize: '1rem', marginBottom: '6px' }}>Web Camera Access Unavailable</div>
                  <p style={{ fontSize: '0.82rem', color: '#CBD5E1', maxWidth: '340px', margin: '0 auto 14px' }}>
                    {errorMessage || 'Camera access was blocked or not found. You can use image upload or 1-click test simulation below.'}
                  </p>
                  <button onClick={startCamera} className="btn btn-secondary btn-sm">
                    <RefreshCw size={14} /> Retry Camera Access
                  </button>
                </div>
              )}
            </div>

            <p style={{ textAlign: 'center', fontSize: '0.82rem', color: 'var(--text-secondary)', marginBottom: '16px' }}>
              {isScanning ? '🔍 Scanning live video feed... Align patient visit pass QR inside reticle frame' : 'Camera inactive'}
            </p>

            {/* Alternative Scan Controls */}
            <div style={{ background: 'var(--bg-subtle)', border: '1px solid var(--border-light)', borderRadius: '12px', padding: '14px', marginBottom: '16px' }}>
              <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', fontWeight: 700, textTransform: 'uppercase', marginBottom: '10px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Sparkles size={14} color="var(--primary-teal)" /> Alternative QR Verification Options for Judges:
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {/* Image Upload Option */}
                <input
                  type="file"
                  ref={fileInputRef}
                  onChange={handleImageUpload}
                  accept="image/*"
                  style={{ display: 'none' }}
                />
                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  className="btn btn-secondary btn-sm"
                  style={{ justifyContent: 'flex-start', gap: '8px' }}
                >
                  <Upload size={16} color="var(--primary-teal)" />
                  Upload QR Code Image File from Device
                </button>

                {/* Quick 1-Click Simulation Buttons */}
                {activeAppointments.map(app => (
                  <button
                    key={app.id}
                    type="button"
                    onClick={() => handleSuccess(app.referenceId)}
                    className="btn btn-green btn-sm"
                    style={{ justifyContent: 'space-between' }}
                  >
                    <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <QrCode size={14} /> ⚡ Simulate Camera Scan: {app.referenceId}
                    </span>
                    <span style={{ fontSize: '0.75rem', opacity: 0.9 }}>({app.patientName})</span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
          <button onClick={onClose} className="btn btn-secondary">
            Close Scanner
          </button>
        </div>
      </div>
    </div>
  );
};
