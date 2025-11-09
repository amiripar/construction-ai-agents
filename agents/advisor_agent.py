#!/usr/bin/env python3
"""
Advisor Agent for Construction Estimation Project (MVP)
Provides cost optimization, anomaly alerts, technical advice, and quality level recommendations.
Extensible for future features.
"""

from typing import Dict, Any, List

class AdvisorAgent:
    def __init__(self):
        # In future: load reference data, thresholds, or configs if needed
        pass

    def analyze(self, estimation: Dict[str, Any], quality_level: str = "standard") -> Dict[str, List[str]]:
        return {
            "optimization_suggestions": self._optimization_suggestions(estimation, quality_level),
            "anomaly_alerts": self._anomaly_alerts(estimation),
            "technical_advice": self._technical_advice(estimation),
            "quality_level_recommendations": self._quality_level_recommendations(quality_level)
        }

    def _optimization_suggestions(self, estimation: Dict[str, Any], quality_level: str) -> List[str]:
        # Example logic: suggest cheaper alternatives for top costly items
        suggestions = []
        top_items = estimation.get("top_items", [])
        for item in top_items:
            name = item["name"]
            if name == "flooring":
                if quality_level == "economic":
                    suggestions.append("You can reduce costs by using laminate flooring instead of hardwood.")
                elif quality_level == "luxury":
                    suggestions.append("Consider using premium hardwood flooring for a luxury finish.")
            if name == "window" and quality_level == "economic":
                suggestions.append("Consider reducing the number or size of windows to lower expenses.")
        return suggestions

    def _anomaly_alerts(self, estimation: Dict[str, Any]) -> List[str]:
        # Example: alert if any item's percent > 15%
        alerts = []
        for item in estimation.get("pie_chart_data", []):
            if item["percent"] > 15:
                alerts.append(f"The cost share of {item['name']} is {item['percent']}%, which is higher than typical projects.")
        return alerts

    def _technical_advice(self, estimation: Dict[str, Any]) -> List[str]:
        # Example: always recommend not to remove insulation
        advice = []
        for d in estimation.get("estimation_details", []):
            if d["name"] == "insulation":
                advice.append("Do not remove thermal insulation as it is essential for energy efficiency.")
        return advice

    def _quality_level_recommendations(self, quality_level: str) -> List[str]:
        recs = []
        if quality_level == "economic":
            recs.append("For economic level, use standard doors instead of luxury models.")
            recs.append("Choose basic kitchen cabinets to save costs.")
        elif quality_level == "luxury":
            recs.append("For luxury level, consider adding smart home systems.")
            recs.append("Use premium materials for flooring and windows.")
        else:
            recs.append("Standard level: balance quality and cost for best value.")
        return recs

# Test function
if __name__ == "__main__":
    # Example input (simulate Estimator Agent output)
    estimation = {
        "estimation_details": [
            {"name": "lumber", "quantity": 32, "unit": "m3", "unit_price": 650, "total_price": 20800, "description": "Structural wood for framing (per m3)"},
            {"name": "window", "quantity": 60, "unit": "m2", "unit_price": 250, "total_price": 15000, "description": "Double-glazed windows (per m2)"},
            {"name": "flooring", "quantity": 400, "unit": "m2", "unit_price": 30, "total_price": 12000, "description": "Laminate or hardwood flooring (per m2)"},
            {"name": "insulation", "quantity": 480, "unit": "m2", "unit_price": 2.5, "total_price": 1200, "description": "Thermal insulation for walls and roof (per m2)"}
        ],
        "total_cost": 87216.0,
        "pie_chart_data": [
            {"name": "lumber", "total_price": 20800, "percent": 23.85},
            {"name": "window", "total_price": 15000, "percent": 17.2},
            {"name": "flooring", "total_price": 12000, "percent": 13.76},
            {"name": "insulation", "total_price": 1200, "percent": 1.38}
        ],
        "top_items": [
            {"name": "lumber", "total_price": 20800, "percent": 23.85},
            {"name": "window", "total_price": 15000, "percent": 17.2},
            {"name": "flooring", "total_price": 12000, "percent": 13.76}
        ],
        "cost_per_area": 218.04,
        "area_unit": "m2"
    }
    agent = AdvisorAgent()
    result = agent.analyze(estimation, quality_level="economic")
    print("Advisor Agent Output:")
    for k, v in result.items():
        print(f"{k}:")
        for item in v:
            print(f"  - {item}")

async def run_advisor(estimator_result: dict, project_input: dict) -> dict:
    """
    Wrapper function for Coordinate Agent compatibility
    """
    quality_level = project_input.get("quality_level", "standard")
    agent = AdvisorAgent()
    return agent.analyze(estimator_result, quality_level=quality_level)