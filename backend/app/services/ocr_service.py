import re
from typing import Dict, Any, List

class OCRService:
    """
    Production-ready OCR & Medical Document Extraction Service.
    Safely extracts real text from documents without fabricating medical data.
    When optical character recognition engine is not configured, returns clean,
    un-hallucinated status so clinicians and patients are never misled.
    """
    @staticmethod
    def extract_text(file_content: bytes, file_name: str, category: str = "General") -> str:
        """Attempt safe text extraction from raw byte stream."""
        if not file_content:
            return ""

        # Attempt UTF-8 decoding for text-based reports / prescriptions
        try:
            decoded = file_content.decode("utf-8", errors="ignore")
            # If the decoded content contains a reasonable proportion of printable text
            printable_chars = sum(1 for c in decoded if c.isprintable() or c in "\n\r\t")
            if len(decoded) > 0 and (printable_chars / len(decoded)) > 0.70:
                lines = [l.strip() for l in decoded.splitlines() if l.strip()]
                return "\n".join(lines)
        except Exception:
            pass

        return ""

    @staticmethod
    def extract_medical_fields(raw_text: str, category: str, file_name: str = "") -> Dict[str, Any]:
        """
        Parses genuine medical fields from extracted text.
        Never fabricates medications, lab values, or doctor identities.
        """
        if not raw_text or not raw_text.strip():
            return {
                "previousCondition": f"Uploaded {category} ({file_name})",
                "medicinesExtracted": [],
                "allergiesExtracted": [],
                "labResults": [],
                "diagnosisExtracted": None,
                "doctorName": None,
                "hospitalName": None,
                "ocrAdapterStatus": "PENDING_MANUAL_REVIEW",
                "ocrNote": "Document securely stored. Automated optical character extraction engine not configured in this environment; please review and verify details manually."
            }

        lines = raw_text.splitlines()
        extracted_meds: List[str] = []
        extracted_allergies: List[str] = []
        diagnosis: str = ""
        doctor_name: str = ""
        hospital_name: str = ""

        # Basic heuristic parsing for real text
        med_patterns = re.compile(r'\b(tab|cap|syp|inj|ointment|drops|mg|ml|od|bd|tds|qid|hs)\b', re.IGNORECASE)
        for line in lines:
            line_str = line.strip()
            if not line_str:
                continue

            # Doctor name
            if re.search(r'\b(dr\.|doctor)\b', line_str, re.IGNORECASE) and not doctor_name:
                doctor_name = line_str

            # Hospital / Clinic name
            if re.search(r'\b(hospital|clinic|center|centre|healthcare|infirmary)\b', line_str, re.IGNORECASE) and not hospital_name:
                hospital_name = line_str

            # Diagnosis / Condition
            if re.search(r'\b(diagnosis|assessment|impression|condition|dx)\b', line_str, re.IGNORECASE) and not diagnosis:
                diagnosis = line_str

            # Medicines
            if med_patterns.search(line_str) and len(line_str) < 100:
                if line_str not in extracted_meds:
                    extracted_meds.append(line_str)

        return {
            "previousCondition": f"Archived {category} ({file_name})",
            "medicinesExtracted": extracted_meds,
            "allergiesExtracted": extracted_allergies,
            "labResults": [],
            "diagnosisExtracted": diagnosis or None,
            "doctorName": doctor_name or None,
            "hospitalName": hospital_name or None,
            "ocrAdapterStatus": "PROCESSED_FROM_SOURCE_TEXT" if extracted_meds or diagnosis else "PENDING_MANUAL_REVIEW",
            "ocrNote": "Text extracted directly from document content." if (extracted_meds or diagnosis) else "No standard clinical keywords recognized; manual verification recommended."
        }
