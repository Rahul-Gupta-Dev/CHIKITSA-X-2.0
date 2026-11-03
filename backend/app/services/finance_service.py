from typing import Dict, Any

class FinanceService:
    """
    Care-to-Cost Financial Assistance Service Engine for Phase 1.
    Calculates estimated coverage breakdown across Insurance, Government Schemes, NGO/CSR grants,
    and remaining out-of-pocket patient financial gap.
    """
    @staticmethod
    def calculate_assessment(
        treatment_cost: float,
        has_insurance: bool = True,
        insurance_balance: float = 420000.0,
        has_gov_card: bool = True,
        ration_card_type: str = "BPL"
    ) -> Dict[str, Any]:
        cost = float(treatment_cost)
        insurance_coverage = 0.0
        gov_support = 0.0
        ngo_assistance = 0.0

        # Insurance calculation (up to 50% of cost or available balance)
        if has_insurance and insurance_balance > 0:
            insurance_coverage = min(cost * 0.50, insurance_balance)

        remaining_after_ins = max(0.0, cost - insurance_coverage)

        # Government scheme calculation (e.g. PM-JAY / MJPJAY for BPL/AAY)
        if has_gov_card and ration_card_type in ["AAY", "BPL", "Orange", "Yellow"]:
            gov_support = min(remaining_after_ins * 0.60, 300000.0)

        remaining_after_gov = max(0.0, remaining_after_ins - gov_support)

        # NGO / CSR Grant calculation
        if remaining_after_gov > 0:
            ngo_assistance = min(remaining_after_gov * 0.50, 30000.0)

        patient_gap = max(0.0, cost - (insurance_coverage + gov_support + ngo_assistance))
        is_funding_complete = patient_gap <= 0.0

        return {
            "estimated_treatment_cost": cost,
            "insurance_support": round(insurance_coverage, 2),
            "government_support": round(gov_support, 2),
            "ngo_support": round(ngo_assistance, 2),
            "estimated_patient_gap": round(patient_gap, 2),
            "is_funding_complete": is_funding_complete,
            "disclaimer": "Indicative financial assistance estimate. Final claim approval subject to insurer, government scheme nodal office, and hospital billing verification."
        }
