#!/usr/bin/env python3
"""
Report Generator Agent for Construction Estimation Project
Generates reports in JSON, HTML, or PDF format based on agent outputs.
"""

from typing import Dict, Any, Optional
import json
from weasyprint import HTML
import io

class ReportGeneratorAgent:
    def __init__(self):
        pass

    def _fmt_currency(self, value, currency: str = "USD") -> str:
        try:
            num = float(value)
            return f"{num:,.0f} {currency}"
        except Exception:
            return str(value)

    def generate_report(
        self,
        project_info: Dict[str, Any],
        material_search_output: Dict[str, Any],
        estimation_output: Dict[str, Any],
        advisor_output: Dict[str, Any],
        report_format: str = "json"
    ) -> Any:
        """
        Generate a report based on provided agent outputs and format.
        Supported formats: json (default), html, pdf
        """
        if report_format == "json":
            return self._generate_json_report(
                project_info,
                material_search_output,
                estimation_output,
                advisor_output
            )
        elif report_format == "html":
            return self._generate_html_report(
                project_info,
                material_search_output,
                estimation_output,
                advisor_output
            )
        elif report_format == "pdf":
            return self._generate_pdf_report(
                project_info,
                material_search_output,
                estimation_output,
                advisor_output
            )
        else:
            return {"error": f"Unsupported report format: {report_format}"}

    def _generate_json_report(
        self,
        project_info: Dict[str, Any],
        material_search_output: Dict[str, Any],
        estimation_output: Dict[str, Any],
        advisor_output: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Combine all agent outputs into a single JSON report.
        """
        area = project_info.get('area', '')
        area_unit = project_info.get('area_unit', 'm2')
        project_info_extended = dict(project_info)
        project_info_extended["area_display"] = f"{area} {area_unit}"
        report = {
            "project_info": project_info_extended,
            "materials": material_search_output,
            "estimation": estimation_output,
            "advice": advisor_output
        }
        return report

    def _generate_html_report(
        self,
        project_info: Dict[str, Any],
        material_search_output: Dict[str, Any],
        estimation_output: Dict[str, Any],
        advisor_output: Dict[str, Any]
    ) -> str:
        """
        Generate a modern, RTL-friendly HTML report combining all agent outputs.
        """
        currency = project_info.get('currency', 'USD')
        area = project_info.get('area', '')
        area_unit = project_info.get('area_unit', 'm2')
        area_html = f"{area} {area_unit}"
        features = project_info.get('features', []) or []

        # Project overview (all fields)
        overview_rows = []
        def add_row(label, val):
            if val is not None and val != "":
                overview_rows.append(f"<div class='kv'><span class='k'>{label}</span><span class='v'>{val}</span></div>")
        add_row('Project Title', project_info.get('title') or project_info.get('name'))
        add_row('Project Type', project_info.get('project_type') or project_info.get('type'))
        add_row('Building/Structure Type', project_info.get('building_type') or project_info.get('structure_type'))
        add_row('Area', area_html)
        add_row('Floors', project_info.get('floors'))
        add_row('Rooms', project_info.get('rooms'))
        add_row('Bathrooms', project_info.get('bathrooms'))
        add_row('Location', project_info.get('location'))
        add_row('Building Height', project_info.get('building_height'))
        add_row('Foundation Type', project_info.get('foundation_type'))
        add_row('Roof Type', project_info.get('roof_type'))
        add_row('Quality Level', project_info.get('quality_level'))
        add_row('Finishing Type', project_info.get('finishing_type'))
        add_row('Description', project_info.get('description'))

        # Materials table
        materials = material_search_output.get("materials", []) or []
        materials_rows = "".join([
            f"<tr><td>{m.get('name','')}</td><td>{m.get('quantity','')}</td><td>{m.get('unit','')}</td></tr>"
            for m in materials
        ])
        if not materials_rows:
            materials_rows = "<tr><td colspan='3' class='empty'>No material information available</td></tr>"

        # Estimation table and totals
        details = estimation_output.get("estimation_details", []) or []
        total_cost = estimation_output.get("total_cost")
        estimation_rows = "".join([
            f"<tr><td>{d.get('name','')}</td><td>{d.get('quantity','')}</td><td>{d.get('unit','')}</td><td>{self._fmt_currency(d.get('unit_price',0), currency)}</td><td>{self._fmt_currency(d.get('total_price',0), currency)}</td></tr>"
            for d in details
        ])
        if not estimation_rows:
            estimation_rows = "<tr><td colspan='5' class='empty'>No cost estimation details available</td></tr>"
        material_total = sum([d.get('total_price') or 0 for d in details]) if details else (total_cost or 0)
        labor_cost = round(float(material_total) * 0.35, 2)
        equipment_cost = round(float(material_total) * 0.10, 2)
        other_costs = round(float(material_total) * 0.05, 2)
        grand_total = round(float(material_total) + labor_cost + equipment_cost + other_costs, 2)

        # Advisor section
        advice_html = ""
        if advisor_output:
            advice_html = "<div class='card'><h3>Technical Advice and Optimization</h3>"
            for key, suggestions in advisor_output.items():
                if suggestions:
                    title = key.replace('_', ' ').title()
                    advice_html += f"<div class='advice-block'><div class='advice-title'>{title}</div><ul>"
                    for s in suggestions:
                        advice_html += f"<li>{s}</li>"
                    advice_html += "</ul></div>"
            advice_html += "</div>"

        # Features chips
        features_html = ""
        if features:
            chips = "".join([f"<span class='chip'>{f}</span>" for f in features])
            features_html = f"<div class='chip-group'>{chips}</div>"

        # HTML with styles (RTL friendly)
        html = f"""
        <html>
        <head>
            <meta charset='utf-8'>
            <title>Project Report</title>
            <style>
                @page {{ size: A4; margin: 20mm; }}
                body {{ font-family: sans-serif; direction: ltr; text-align: left; color: #1f2937; }}
                h1 {{ font-size: 22px; margin: 0 0 16px; color: #0f172a; }}
                h2 {{ font-size: 18px; margin: 24px 0 12px; color: #111827; }}
                h3 {{ font-size: 16px; margin: 16px 0 8px; color: #111827; }}
                .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }}
                .card {{ border: 1px solid #e5e7eb; border-radius: 8px; padding: 12px; background: #fafafa; }}
                .kv {{ display: flex; justify-content: space-between; padding: 6px 0; border-bottom: 1px dashed #e5e7eb; }}
                .kv .k {{ color: #6b7280; }}
                .kv .v {{ font-weight: 600; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 8px; }}
                th, td {{ border: 1px solid #e5e7eb; padding: 8px; font-size: 12px; }}
                th {{ background: #f3f4f6; color: #374151; }}
                tr:nth-child(even) td {{ background: #fcfcfc; }}
                .empty {{ text-align: center; color: #9ca3af; }}
                .chip-group {{ margin-top: 8px; }}
                .chip {{ display: inline-block; background: #eef2ff; color: #3730a3; padding: 4px 8px; border-radius: 16px; margin: 4px; font-size: 12px; }}
                .summary {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; margin-top: 8px; }}
                .sum-item {{ background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 8px; padding: 10px; text-align: center; }}
                .sum-title {{ color: #6b7280; font-size: 12px; }}
                .sum-value {{ font-weight: 700; font-size: 14px; color: #111827; }}
                footer {{ margin-top: 24px; font-size: 11px; color: #6b7280; border-top: 1px solid #e5e7eb; padding-top: 8px; }}
            </style>
        </head>
        <body>
            <h1>Project Report</h1>

            <div class='grid'>
                <div class='card'>
                    <h2>Project Specifications</h2>
                    {''.join(overview_rows)}
                    {features_html}
                </div>
                <div class='card'>
                    <h2>Cost Summary</h2>
                    <div class='summary'>
                        <div class='sum-item'><div class='sum-title'>Material Cost</div><div class='sum-value'>{self._fmt_currency(material_total, currency)}</div></div>
                        <div class='sum-item'><div class='sum-title'>Labor Cost</div><div class='sum-value'>{self._fmt_currency(labor_cost, currency)}</div></div>
                        <div class='sum-item'><div class='sum-title'>Equipment Cost</div><div class='sum-value'>{self._fmt_currency(equipment_cost, currency)}</div></div>
                        <div class='sum-item'><div class='sum-title'>Other Costs</div><div class='sum-value'>{self._fmt_currency(other_costs, currency)}</div></div>
                    </div>
                    <h3>Grand Total</h3>
                    <div class='sum-item'><div class='sum-title'>Grand Total</div><div class='sum-value'>{self._fmt_currency(grand_total, currency)}</div></div>
                </div>
            </div>

            <div class='card'>
                <h2>Materials List</h2>
                <table>
                    <thead>
                        <tr><th>Name</th><th>Quantity</th><th>Unit</th></tr>
                    </thead>
                    <tbody>
                        {materials_rows}
                    </tbody>
                </table>
            </div>

            <div class='card'>
                <h2>Cost Estimation Details</h2>
                <table>
                    <thead>
                        <tr><th>Item</th><th>Quantity</th><th>Unit</th><th>Unit Price</th><th>Total Price</th></tr>
                    </thead>
                    <tbody>
                        {estimation_rows}
                    </tbody>
                </table>
            </div>

            {advice_html}

            <footer>
                This report is generated based on the project data and AI agents' outputs.
            </footer>
        </body>
        </html>
        """
        return html

    def _generate_pdf_report(
        self,
        project_info: Dict[str, Any],
        material_search_output: Dict[str, Any],
        estimation_output: Dict[str, Any],
        advisor_output: Dict[str, Any]
    ) -> bytes:
        """
        Generate a PDF report by rendering the HTML report and converting it to PDF.
        Returns PDF as bytes.
        """
        html_content = self._generate_html_report(
            project_info,
            material_search_output,
            estimation_output,
            advisor_output
        )
        pdf_io = io.BytesIO()
        HTML(string=html_content).write_pdf(pdf_io)
        pdf_bytes = pdf_io.getvalue()
        pdf_io.close()
        return pdf_bytes

async def run_report_generator(all_results: dict) -> any:
    """
    Wrapper function for Coordinate Agent compatibility
    """
    project_info = all_results.get('project_input', {})
    material_search_output = all_results.get('material_result', {})
    estimation_output = all_results.get('estimator_result', {})
    advisor_output = all_results.get('advisor_result', {})
    report_format = project_info.get('report_format', 'json')
    agent = ReportGeneratorAgent()
    return agent.generate_report(
        project_info,
        material_search_output,
        estimation_output,
        advisor_output,
        report_format=report_format
    )

# Test function
if __name__ == "__main__":
    # Example dummy data for testing
    project_info = {"title": "Sample House", "area": 400, "floors": 2}
    material_search_output = {"materials": [{"name": "lumber", "quantity": 32, "unit": "m3"}]}
    estimation_output = {"total_cost": 100000, "estimation_details": []}
    advisor_output = {"optimization_suggestions": ["Use laminate flooring."]}
    agent = ReportGeneratorAgent()
    report = agent.generate_report(
        project_info,
        material_search_output,
        estimation_output,
        advisor_output,
        report_format="json"
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))