from typing import Dict, Any, List

class TriageService:
    """
    AI-Assisted Clinical Triage Engine for Phase 1D.
    Evaluates patient symptoms, medical history, and intake details
    to produce clinical decision support guidance and risk prioritization.
    
    IMPORTANT MEDICAL / LEGAL DISCLAIMER:
    AI-assisted triage decision support only. This system does NOT provide a disease diagnosis.
    Final clinical decisions remain with qualified healthcare professionals.
    """
    @staticmethod
    def evaluate_triage(symptoms: List[str], medical_history: List[str], is_emergency: bool = False, severity: str = "Moderate") -> Dict[str, Any]:
        symptoms_str = " ".join(symptoms).lower()
        history_str = " ".join(medical_history).lower()

        has_chest = "chest" in symptoms_str or "chhati" in symptoms_str
        has_breath = "breath" in symptoms_str or "saans" in symptoms_str or "dyspnea" in symptoms_str
        has_fever = "fever" in symptoms_str or "bukhar" in symptoms_str
        has_throat = "throat" in symptoms_str or "cough" in symptoms_str or "khansi" in symptoms_str
        has_neuro = "dizzy" in symptoms_str or "headache" in symptoms_str or "chakkar" in symptoms_str
        has_cardiac_history = any(term in history_str for term in ["diabetes", "hypertension", "cardiac", "heart", "bp", "bypass"])

        if is_emergency or severity == "Severe" or (has_chest and has_breath and has_cardiac_history):
            risk_level = "HIGH"
            urgency = "Urgent Evaluation (Immediate)"
            recommended_specialty = "Cardiology & Emergency Medicine"
            recommended_next_step = "Direct patient toward immediate local emergency medical care and trauma Cath Lab evaluation."
            is_emergency_triggered = True
            reasoning = [
                "Detected acute cardiorespiratory indicators (chest discomfort and shortness of breath).",
                "Co-existing cardiovascular history noted (Hypertension / Diabetes).",
                "Immediate ECG and cardiac biomarkers recommended within 1 hour."
            ]
        elif has_chest or has_breath:
            risk_level = "MODERATE"
            urgency = "Prompt Consultation (24h)"
            recommended_specialty = "Cardiology & Internal Medicine"
            recommended_next_step = "Schedule priority OPD consultation with a Cardiologist within 24 hours."
            is_emergency_triggered = False
            reasoning = [
                "Cardiovascular / thoracic discomfort noted with moderate onset.",
                "Patient history indicates active medical management.",
                "Elective Cardiology consultation and vital monitoring advised."
            ]
        elif has_fever or has_throat:
            risk_level = "LOW"
            urgency = "Routine Outpatient Consultation"
            recommended_specialty = "General Medicine / ENT"
            recommended_next_step = "Schedule routine OPD booking at a General Medicine clinic."
            is_emergency_triggered = False
            reasoning = [
                "Symptoms suggestive of mild upper respiratory / febrile condition.",
                "No acute cardiac or neurological red-flag distress indicators detected."
            ]
        elif has_neuro:
            risk_level = "LOW"
            urgency = "Routine Consultation (48h)"
            recommended_specialty = "General Medicine / Neurology"
            recommended_next_step = "Book Outpatient consultation for neurological and vital sign check."
            is_emergency_triggered = False
            reasoning = [
                "Reported dizziness / headache symptoms requiring routine clinical evaluation.",
                "Hydration, blood pressure check, and physician consultation advised."
            ]
        else:
            risk_level = "LOW"
            urgency = "Routine Consultation"
            recommended_specialty = "General Medicine / Outpatient Care"
            recommended_next_step = "Schedule routine OPD appointment at a convenient facility."
            is_emergency_triggered = False
            reasoning = [
                "Mild constitutional symptom profile without acute distress indicators.",
                "Routine clinical consultation and health profile review advised."
            ]

        return {
            "risk_level": risk_level,
            "urgency": urgency,
            "symptoms_considered": symptoms,
            "clinical_reasoning": reasoning,
            "recommended_specialty": recommended_specialty,
            "recommended_next_step": recommended_next_step,
            "is_emergency_triggered": is_emergency_triggered,
            "disclaimer": "AI-assisted triage decision support only. Does not constitute a disease diagnosis. Final clinical decisions are made by qualified healthcare professionals."
        }
