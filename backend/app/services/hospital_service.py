from typing import List, Dict, Any

class HospitalRecommendationService:
    """
    Care Score Hospital Recommendation Engine for Phase 1.
    Ranks hospitals based on weighted Care Score:
      - Clinical Fit = 35%
      - Affordability = 25%
      - Distance = 15%
      - Availability = 15%
      - Financial Support = 10%
    """
    @staticmethod
    def calculate_care_score_details(hospital: Dict[str, Any], budget_preference: str = "MEDIUM", target_specialty: str = None) -> Dict[str, Any]:
        fit = float(hospital.get("clinicalFitScore", hospital.get("clinical_fit_score", 85)))
        afford = float(hospital.get("affordabilityScore", hospital.get("affordability_score", 80)))
        dist = float(hospital.get("distanceKm", hospital.get("distance_km", 5.0)))
        avail = float(hospital.get("availabilityScore", hospital.get("availability_score", 85)))
        support = float(hospital.get("supportServicesScore", hospital.get("support_services_score", 85)))

        # Distance score: 100 for < 2km, decays by 5 per km
        distance_score = max(50.0, 100.0 - (dist * 5.0))

        # Adjust affordability score based on budget preference
        if budget_preference == "LOW":
            afford = min(100.0, afford * 1.15)
        elif budget_preference == "HIGH":
            fit = min(100.0, fit * 1.1)

        breakdown = {
            "clinical_fit": round(fit * 0.35, 1),
            "affordability": round(afford * 0.25, 1),
            "distance": round(distance_score * 0.15, 1),
            "availability": round(avail * 0.15, 1),
            "financial_support": round(support * 0.10, 1)
        }

        care_score = round(sum(breakdown.values()), 1)

        return {
            "care_score": care_score,
            "score_breakdown": breakdown
        }

    @classmethod
    def rank_hospitals(cls, hospitals: List[Dict[str, Any]], budget_preference: str = "MEDIUM") -> List[Dict[str, Any]]:
        ranked = []
        for h in hospitals:
            details = cls.calculate_care_score_details(h, budget_preference)
            h_copy = dict(h)
            h_copy["chikitsaxCareScore"] = details["care_score"]
            h_copy["chikitsax_care_score"] = details["care_score"]
            h_copy["care_score"] = details["care_score"]
            h_copy["score_breakdown"] = details["score_breakdown"]
            h_copy["hospital"] = {
                "id": h.get("id"),
                "name": h.get("name"),
                "code": h.get("code"),
                "address": h.get("address"),
                "city": h.get("city")
            }
            h_copy["availability"] = h.get("opdSlotAvailability") or "HIGH"
            h_copy["financial_support"] = h.get("acceptedGovSchemes") or h.get("accepted_gov_schemes") or []
            ranked.append(h_copy)

        ranked.sort(key=lambda x: x["care_score"], reverse=True)
        return ranked

