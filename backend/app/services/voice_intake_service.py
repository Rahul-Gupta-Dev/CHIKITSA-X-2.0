from typing import List, Dict, Any

class VoiceIntakeService:
    """
    Dynamic Symptom & Intake NLP Service Adapter for Phase 1D.
    Extracts symptoms, duration, severity, body system, and red flags
    from voice / text transcripts captured by browser Speech API or manual input.
    
    IMPORTANT DISCLAIMER:
    AI-assisted symptom extraction only. Does NOT provide a disease diagnosis.
    Final clinical decisions remain with qualified healthcare professionals.
    """
    @staticmethod
    def process_transcript(raw_transcript: str) -> Dict[str, Any]:
        text_lower = raw_transcript.lower().strip()
        extracted_symptoms: List[str] = []
        red_flags: List[str] = []
        is_emergency = False
        severity = "Moderate"
        duration = "Recent onset (1-3 days)"
        body_system = "General / Constitutional"

        # Symptom keyword detection rules
        if "chest" in text_lower or "discomfort" in text_lower or "chhati" in text_lower or "pressure" in text_lower:
            extracted_symptoms.append("Chest Discomfort / Tightness")
            body_system = "Cardiovascular / Thoracic"
        if "breath" in text_lower or "breathing" in text_lower or "saans" in text_lower or "dyspnea" in text_lower:
            extracted_symptoms.append("Shortness of Breath")
            body_system = "Cardiovascular / Respiratory"
        if "fatigue" in text_lower or "tired" in text_lower or "thakavat" in text_lower or "weakness" in text_lower:
            extracted_symptoms.append("Fatigue on Walking")
        if "fever" in text_lower or "bukhar" in text_lower or "chills" in text_lower or "temperature" in text_lower:
            extracted_symptoms.append("Fever & Chills")
            if body_system == "General / Constitutional": body_system = "Infectious / Systemic"
        if "headache" in text_lower or "sir dard" in text_lower or "migraine" in text_lower:
            extracted_symptoms.append("Headache")
            if body_system == "General / Constitutional": body_system = "Neurological"
        if "dizzy" in text_lower or "dizziness" in text_lower or "chakkar" in text_lower or "giddiness" in text_lower:
            extracted_symptoms.append("Dizziness / Lightheadedness")
            if body_system == "General / Constitutional": body_system = "Neurological"
        if "throat" in text_lower or "cough" in text_lower or "khansi" in text_lower or "sore" in text_lower:
            extracted_symptoms.append("Sore Throat & Cough")
            if body_system == "General / Constitutional": body_system = "Respiratory / ENT"
        if "stomach" in text_lower or "abdominal" in text_lower or "nausea" in text_lower or "vomit" in text_lower or "pet" in text_lower:
            extracted_symptoms.append("Abdominal Discomfort / Nausea")
            if body_system == "General / Constitutional": body_system = "Gastrointestinal"
        if "joint" in text_lower or "back" in text_lower or "muscle" in text_lower or "leg" in text_lower or "dard" in text_lower:
            extracted_symptoms.append("Joint & Muscle Pain")
            if body_system == "General / Constitutional": body_system = "Musculoskeletal"

        if not extracted_symptoms:
            extracted_symptoms = [f"Reported Discomfort: {raw_transcript[:40]}..."]

        # Duration detection rules
        if "yesterday" in text_lower or "24 hours" in text_lower or "1 day" in text_lower:
            duration = "24 Hours"
        elif "2 days" in text_lower or "two days" in text_lower or "48 hours" in text_lower:
            duration = "2 Days"
        elif "3 days" in text_lower or "three days" in text_lower:
            duration = "3 Days"
        elif "week" in text_lower:
            duration = "1 Week"
        elif "today" in text_lower or "morning" in text_lower or "hours" in text_lower:
            duration = "Acute (Less than 12 Hours)"

        # Severity & Red Flags rules
        if any(term in text_lower for term in ["severe", "crushing", "unbearable", "unconscious", "sweating", "faint", "behoshi"]):
            severity = "Severe"
            is_emergency = True
            red_flags.append("Severe intensity symptom description reported by patient")
        elif "mild" in text_lower or "slight" in text_lower or "minor" in text_lower:
            severity = "Mild"

        if "chest" in text_lower and ("breath" in text_lower or "shortness" in text_lower):
            red_flags.append("Concurrent chest discomfort and dyspnea (shortness of breath)")
            if severity != "Mild":
                severity = "Severe"
                is_emergency = True

        patient_summary = (
            f"Patient reported {', '.join(extracted_symptoms)} of {severity.lower()} severity with duration of {duration}."
        )

        return {
            "extracted_symptoms": extracted_symptoms,
            "duration": duration,
            "severity": severity,
            "affected_body_part": body_system,
            "red_flags": red_flags,
            "patient_summary": patient_summary,
            "is_emergency_alert": is_emergency,
            "disclaimer": "AI-assisted symptom extraction. Clinical evaluation by a qualified doctor is required."
        }
