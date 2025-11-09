#!/usr/bin/env python3
"""
Material Search Agent for Construction Estimation Project
Reads material coefficients from a JSON file (materials_ontario.json)
"""

from typing import Dict, Any, List
import json
import os

MATERIALS_JSON_PATH = os.path.join(os.path.dirname(__file__), '../materials_ontario.json')

class MaterialSearchAgent:
    def __init__(self, json_path: str = None, area_unit: str = "m2"):
        if area_unit.lower() in ["sqft", "ft2"]:
            json_path = os.path.join(os.path.dirname(__file__), '../materials_ontario_sqft.json')
        else:
            json_path = os.path.join(os.path.dirname(__file__), '../materials_ontario_m2.json')
        self.coefficients = self._load_coefficients(json_path)

    def _load_coefficients(self, json_path: str) -> Dict[str, Any]:
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data
        except Exception as e:
            print(f"Error loading material coefficients: {e}")
            return {}

    def calculate_materials(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        building_type = input_data.get("building_type", "wood_frame_house")
        area = input_data.get("area", 0)
        area_unit = input_data.get("area_unit", "m2")  # default: m2
        # حذف تبدیل واحد؛ همه چیز با واحد ورودی انجام می‌شود
        coeffs = self.coefficients.get(building_type, {})
        if not coeffs:
            return {
                "materials": [],
                "suggestions": [
                    f"No coefficients found for {building_type}. Please update the database."
                ]
            }
        materials = []
        for material, info in coeffs.items():
            if info["unit"] in ["m3", "m2", "sqft"]:
                quantity = info["coefficient"] * area
            elif info["unit"] == "count":
                quantity = int(info["coefficient"] * area)
            else:
                quantity = info["coefficient"] * area
            materials.append({
                "name": material,
                "quantity": round(quantity, 2),
                "unit": info["unit"],
                "description": info.get("description", "")
            })

        suggestions = [
            "For better insulation, consider using R-24 batts in exterior walls."
        ]

        return {
            "materials": materials,
            "suggestions": suggestions
        }

async def run_material_search(input_data: dict) -> dict:
    area_unit = input_data.get("area_unit", "m2")
    agent = MaterialSearchAgent(area_unit=area_unit)
    return agent.calculate_materials(input_data)

# Test function
def test_material_search_agent():
    agent = MaterialSearchAgent()
    input_data = {
        "building_type": "wood_frame_house",
        "area": 200,
        "floors": 2,
        "rooms": 4,
        "bathrooms": 2
    }
    result = agent.calculate_materials(input_data)
    print("✅ Material Search Agent Test Result:")
    for m in result["materials"]:
        print(f"   - {m['name']}: {m['quantity']} {m['unit']} | {m['description']}")
    print("Suggestions:")
    for s in result["suggestions"]:
        print(f"   - {s}")
    print("✅ Test completed!")

if __name__ == "__main__":
    test_material_search_agent()