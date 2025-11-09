#!/usr/bin/env python3
"""
Estimator Agent for Construction Estimation Project
Reads material prices from a JSON file (prices_ontario.json)
"""

from typing import Dict, Any, List
import json
import os

PRICES_JSON_PATH = os.path.join(os.path.dirname(__file__), '../prices_ontario.json')

class EstimatorAgent:
    def __init__(self, prices_path: str = None, area_unit: str = "m2"):
        if area_unit.lower() in ["sqft", "ft2"]:
            prices_path = os.path.join(os.path.dirname(__file__), '../prices_ontario_sqft.json')
        else:
            prices_path = os.path.join(os.path.dirname(__file__), '../prices_ontario_m2.json')
        self.prices = self._load_prices(prices_path)
        # Store area unit for use in output (e.g., CAD/m2 or CAD/sqft)
        self.area_unit = area_unit.lower()

    def _load_prices(self, prices_path: str) -> Dict[str, Any]:
        try:
            with open(prices_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data
        except Exception as e:
            print(f"Error loading material prices: {e}")
            return {}

    def estimate(self, materials: List[Dict[str, Any]], area: float = None, top_n: int = 5) -> Dict[str, Any]:
        estimation_details = []
        total_cost = 0.0
        for item in materials:
            name = item["name"]
            quantity = item["quantity"]
            unit = item["unit"]
            price_info = self.prices.get(name)
            if price_info:
                unit_price = price_info["unit_price"]
                total_price = round(quantity * unit_price, 2)
                description = price_info.get("description", "")
            else:
                unit_price = None
                total_price = None
                description = "No price info available"
            estimation_details.append({
                "name": name,
                "quantity": quantity,
                "unit": unit,
                "unit_price": unit_price,
                "total_price": total_price,
                "description": description
            })
            if total_price:
                total_cost += total_price

        # Pie chart data
        pie_chart_data = []
        for d in estimation_details:
            if d["total_price"]:
                percent = round(100 * d["total_price"] / total_cost, 2) if total_cost else 0
                pie_chart_data.append({
                    "name": d["name"],
                    "total_price": d["total_price"],
                    "percent": percent
                })
        pie_chart_data.sort(key=lambda x: x["total_price"], reverse=True)

        # Top N items by cost
        top_items = pie_chart_data[:top_n]

        # Cost per area unit (generalized)
        cost_per_area = round(total_cost / area, 2) if area and area > 0 else None

        return {
            "estimation_details": estimation_details,
            "total_cost": round(total_cost, 2),
            "pie_chart_data": pie_chart_data,
            "top_items": top_items,
            "cost_per_area": cost_per_area,
            "area_unit": self.area_unit
        }

async def run_estimator(material_result: dict, project_input: dict) -> dict:
    """
    Wrapper function for Coordinate Agent compatibility
    """
    materials = material_result.get("materials", [])
    area = project_input.get("area")
    area_unit = project_input.get("area_unit", "m2")
    agent = EstimatorAgent(area_unit=area_unit)
    return agent.estimate(materials, area=area)

# Test function
def test_estimator_agent():
    # Sample input (matches output of Material Search Agent)
    materials = [
        {"name": "lumber", "quantity": 32, "unit": "m3"},
        {"name": "foundation_concrete", "quantity": 48, "unit": "m3"},
        {"name": "insulation", "quantity": 480, "unit": "m2"},
        {"name": "drywall", "quantity": 440, "unit": "m2"},
        {"name": "roof_shingle", "quantity": 420, "unit": "m2"},
        {"name": "window", "quantity": 60, "unit": "m2"},
        {"name": "interior_door", "quantity": 12, "unit": "count"},
        {"name": "paint", "quantity": 600, "unit": "m2"},
        {"name": "flooring", "quantity": 400, "unit": "m2"},
        {"name": "exterior_siding", "quantity": 440, "unit": "m2"},
        {"name": "electrical_wiring", "quantity": 72, "unit": "kg"},
        {"name": "plumbing_pipe", "quantity": 48, "unit": "m"},
        {"name": "hvac_duct", "quantity": 32, "unit": "m"},
        {"name": "toilet", "quantity": 4, "unit": "count"},
        {"name": "kitchen_cabinet", "quantity": 8, "unit": "m2"},
        {"name": "garage_door", "quantity": 2, "unit": "count"},
        {"name": "smoke_detector", "quantity": 4, "unit": "count"}
    ]
    area = 200 * 2  # floors * area per floor
    agent = EstimatorAgent()
    result = agent.estimate(materials, area=area)
    print("✅ Estimator Agent Test Result:")
    for d in result["estimation_details"]:
        print(f"   - {d['name']}: {d['quantity']} {d['unit']} × {d['unit_price']} = {d['total_price']} | {d['description']}")
    print(f"Total cost: {result['total_cost']} CAD")
    if result.get("cost_per_area") is not None:
        print(f"Cost per {result['area_unit']}: {result['cost_per_area']} CAD/{result['area_unit']}")
    else:
        print("Cost per area: N/A")
    print("Pie chart data:")
    for p in result["pie_chart_data"]:
        print(f"   - {p['name']}: {p['total_price']} CAD ({p['percent']}%)")
    print("Top items:")
    for t in result["top_items"]:
        print(f"   - {t['name']}: {t['total_price']} CAD ({t['percent']}%)")
    print("✅ Test completed!")

if __name__ == "__main__":
    test_estimator_agent()