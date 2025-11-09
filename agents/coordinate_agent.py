# Coordinate Agent
# این Agent ورودی پروژه را می‌گیرد، سایر Agentها را به ترتیب فراخوانی می‌کند و فقط خروجی نهایی (گزارش) را بازمی‌گرداند.

from agents.material_search_agent import run_material_search
from agents.estimator_agent import run_estimator
from agents.advisor_agent import run_advisor
from agents.report_generator_agent import run_report_generator


async def run_coordinate_agent(project_input):
    """
    ورودی: project_input (dict)
    خروجی: گزارش نهایی (dict یا HTML یا PDF بسته به تنظیمات)
    """
    try:
        # مرحله ۱: محاسبه مصالح
        material_result = await run_material_search(project_input)

        # مرحله ۲: برآورد هزینه
        estimator_result = await run_estimator(material_result, project_input)

        # مرحله ۳: توصیه فنی
        advisor_result = await run_advisor(estimator_result, project_input)

        # مرحله ۴: تولید گزارش نهایی
        report_result = await run_report_generator({
            'project_input': project_input,
            'material_result': material_result,
            'estimator_result': estimator_result,
            'advisor_result': advisor_result
        })

        return {
            "success": True,
            "data": report_result,
            "pdf_content": report_result if isinstance(report_result, bytes) else None
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "data": None
        }