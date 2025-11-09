from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Dict, Any
from sqlalchemy.orm import Session
import uvicorn
from fastapi.responses import StreamingResponse
import io
import os
from datetime import datetime

# Import our modules
from database_config import test_connection, get_db
from agents_structure import test_agent_structure
from models import UserCreate, UserResponse, UserLogin, ProjectCreate, ProjectResponse, ApiResponse
from database_operations import create_user, authenticate_user, create_project, get_project_by_id, get_user_projects, ensure_project_type_constraint, delete_project, ensure_project_extra_columns_and_migrate, update_project, ensure_reports_table, create_report, get_project_reports, get_report_by_id, delete_report, update_report, get_user_reports
from sqlalchemy import text
from auth import create_access_token, get_current_user
from agents.material_search_agent import MaterialSearchAgent
from agents.estimator_agent import EstimatorAgent
from agents.advisor_agent import AdvisorAgent
from agents.report_generator_agent import ReportGeneratorAgent
from agents.coordinate_agent import run_coordinate_agent

# Create FastAPI app
app = FastAPI(
    title="Construction Estimation API",
    description="API for construction cost estimation using intelligent agents",
    version="1.0.0"
)

# Ensure DB constraints are up to date (especially projects.type)
try:
    ensure_project_type_constraint()
except Exception as e:
    print(f"⚠️ Startup constraint update failed: {e}")

# Ensure new explicit columns exist and migrate data from extra_info
try:
    ensure_project_extra_columns_and_migrate()
except Exception as e:
    print(f"⚠️ Startup extra columns migration failed: {e}")

# Ensure reports table exists at startup
try:
    ensure_reports_table()
except Exception as e:
    print(f"⚠️ Startup reports table ensure failed: {e}")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Serve index.html at root
from fastapi.responses import FileResponse

@app.get("/index.html")
async def serve_index():
    return FileResponse("index.html")

@app.get("/dashboard.html")
async def serve_dashboard():
    return FileResponse("static/dashboard.html")

@app.get("/dashboard")
async def serve_dashboard_alt():
    return FileResponse("static/dashboard.html")

# Pydantic models for API
class HealthCheck(BaseModel):
    status: str
    message: str
    details: Dict[str, Any]

# API endpoints
@app.get("/", response_model=HealthCheck)
async def root():
    """Root endpoint"""
    return HealthCheck(
        status="healthy",
        message="Construction Estimation API is running",
        details={
            "version": "1.0.0",
            "database": "PostgreSQL",
            "agents": "6 agents configured"
        }
    )

@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint"""
    # Test database connection
    db_status = test_connection()
    
    # Test agent structure
    try:
        test_agent_structure()
        agents_status = True
    except Exception as e:
        agents_status = False
    
    if db_status and agents_status:
        return HealthCheck(
            status="healthy",
            message="All systems operational",
            details={
                "database": "connected",
                "agents": "configured",
                "api": "running"
            }
        )
    else:
        raise HTTPException(
            status_code=500,
            detail="System health check failed"
        )

@app.get("/api/version")
async def get_version():
    """Get API version"""
    return {"version": "1.0.0", "name": "Construction Estimation API"}

# User endpoints
@app.post("/api/users/register", response_model=ApiResponse)
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    result = create_user(db, user)
    return ApiResponse(
        success=result["success"],
        message=result["message"],
        data={"user_id": result.get("user_id")} if result["success"] else None
    )

@app.post("/api/users/login", response_model=ApiResponse)
async def login_user(user_credentials: UserLogin, db: Session = Depends(get_db)):
    """Login user"""
    result = authenticate_user(db, user_credentials.username, user_credentials.password)
    if result["success"]:
        user_data = result["user"].copy()
        user_data.pop("password", None)
        # Generate JWT token
        token = create_access_token({"sub": user_data["username"]})
        return ApiResponse(
            success=True,
            message="Login successful",
            data={"user": user_data, "access_token": token, "token_type": "bearer"}
        )
    else:
        return ApiResponse(
            success=False,
            message=result["message"]
        )

# Auth verification endpoint
@app.get("/api/verify-token", response_model=ApiResponse)
async def verify_token(current_user: dict = Depends(get_current_user)):
    """Verify token and return user info"""
    return ApiResponse(
        success=True,
        message="Token is valid",
        data={"user": current_user}
    )

# Project endpoints
@app.post("/api/projects", response_model=ApiResponse)
async def create_new_project(
    project_data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new project (authenticated)"""
    try:
        # Extract data from frontend format
        extra_info = {
            "area_unit": project_data.get("area_unit", "m2"),
            "building_type": project_data.get("building_type"),
            "building_height": project_data.get("building_height"),
            "foundation_type": project_data.get("foundation_type"),
            "roof_type": project_data.get("roof_type"),
            "quality_level": project_data.get("quality_level"),
            "finishing_type": project_data.get("finishing_type"),
            "features": project_data.get("features", []),
            "description": project_data.get("description")
        }
        
        # Create ProjectCreate object with explicit fields populated
        project = ProjectCreate(
            title=project_data.get("name", "Untitled Project"),
            type=project_data.get("type", "residential"),
            area=float(project_data.get("area", 0)),
            structure_type=project_data.get("structure_type") or project_data.get("building_type") or "wood_frame_house",
            location=project_data.get("location", ""),
            floors=int(project_data.get("floors", 1)),
            rooms=int(project_data.get("rooms", 1)),
            bathrooms=int(project_data.get("bathrooms", 1)),
            # explicit fields mirrored from extra_info
            area_unit=project_data.get("area_unit", "m2"),
            building_type=project_data.get("building_type"),
            building_height=(float(project_data.get("building_height")) if project_data.get("building_height") not in [None, "", "null"] else None),
            foundation_type=project_data.get("foundation_type"),
            roof_type=project_data.get("roof_type"),
            quality_level=project_data.get("quality_level"),
            finishing_type=project_data.get("finishing_type"),
            features=project_data.get("features", []),
            description=project_data.get("description"),
            extra_info=extra_info
        )
        
        user_id = current_user["id"]
        result = create_project(db, project, user_id)
        return ApiResponse(
            success=result["success"],
            message=result["message"],
            data={"project_id": result.get("project_id")} if result["success"] else None
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            message=f"Error creating project: {str(e)}"
        )

@app.put("/api/projects/{project_id}", response_model=ApiResponse)
async def update_existing_project(
    project_id: int,
    project_data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update an existing project (authenticated)"""
    try:
        # Extract data from frontend format
        extra_info = {
            "area_unit": project_data.get("area_unit", "m2"),
            "building_type": project_data.get("building_type"),
            "building_height": project_data.get("building_height"),
            "foundation_type": project_data.get("foundation_type"),
            "roof_type": project_data.get("roof_type"),
            "quality_level": project_data.get("quality_level"),
            "finishing_type": project_data.get("finishing_type"),
            "features": project_data.get("features", []),
            "description": project_data.get("description")
        }

        # Build ProjectCreate object
        project = ProjectCreate(
            title=project_data.get("name", "Untitled Project"),
            type=project_data.get("type", "residential"),
            area=float(project_data.get("area", 0)),
            structure_type=project_data.get("structure_type") or project_data.get("building_type") or "wood_frame_house",
            location=project_data.get("location", ""),
            standard=project_data.get("standard"),
            floors=int(project_data.get("floors", 1)),
            rooms=int(project_data.get("rooms", 1)),
            bathrooms=int(project_data.get("bathrooms", 1)),
            area_unit=project_data.get("area_unit", "m2"),
            building_type=project_data.get("building_type"),
            building_height=(float(project_data.get("building_height")) if project_data.get("building_height") not in [None, "", "null"] else None),
            foundation_type=project_data.get("foundation_type"),
            roof_type=project_data.get("roof_type"),
            quality_level=project_data.get("quality_level"),
            finishing_type=project_data.get("finishing_type"),
            features=project_data.get("features", []),
            description=project_data.get("description"),
            extra_info=extra_info
        )

        user_id = current_user["id"]
        result = update_project(db, project_id, user_id, project)
        return ApiResponse(
            success=result.get("success", False),
            message=result.get("message", ""),
            data={"project_id": result.get("project_id")} if result.get("success") else None
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            message=f"Error updating project: {str(e)}"
        )

@app.get("/api/projects", response_model=ApiResponse)
async def get_user_projects_endpoint(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all projects for the current user"""
    try:
        result = get_user_projects(db, current_user["id"])  # type: ignore
        if result.get("success"):
            return ApiResponse(
                success=True,
                message="Projects retrieved successfully",
                data={"projects": result.get("projects", [])}
            )
        else:
            return ApiResponse(
                success=False,
                message=result.get("message", "Failed to retrieve projects")
            )
    except Exception as e:
        return ApiResponse(
            success=False,
            message=f"Error retrieving projects: {str(e)}"
        )

@app.delete("/api/projects/{project_id}", response_model=ApiResponse)
async def delete_project_endpoint(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete a project owned by current user"""
    try:
        result = delete_project(db, project_id, current_user["id"])  # type: ignore
        return ApiResponse(
            success=result.get("success", False),
            message=result.get("message", "")
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            message=f"Error deleting project: {str(e)}"
        )

@app.post("/api/projects/{project_id}/estimate", response_model=ApiResponse)
async def get_project_estimation(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get cost estimation for a project using AI agents"""
    try:
        # Get project data from database
        project_result = get_project_by_id(db, project_id, current_user["id"])
        
        if not project_result.get("success"):
            return ApiResponse(
                success=False,
                message=project_result.get("message", "Project not found")
            )
        
        project = project_result["project"]
        
        # Convert database project to agent format (prefer explicit columns, fallback to extra_info)
        # Normalize area_unit from explicit column or extra_info keys
        extra = project.get("extra_info", {}) if isinstance(project.get("extra_info", {}), dict) else {}
        area_unit = project.get("area_unit") or extra.get("area_unit") or extra.get("areaUnit") or extra.get("unit") or "m2"
        project_data = {
            "project_id": project_id,
            "project_type": project.get("type", "residential"),
            "building_type": project.get("building_type") or project.get("structure_type") or "wood_frame_house",
            "area": float(project.get("area", 150)),
            "area_unit": area_unit,
            "building_height": project.get("building_height") or extra.get("building_height"),
            "floors": int(project.get("floors", 2)),
            "rooms": int(project.get("rooms", 4)),
            "bathrooms": int(project.get("bathrooms", 2)),
            "location": project.get("location", "Ontario"),
            "description": project.get("description") or project.get("title", "Project"),
            "features": project.get("features") or extra.get("features", [])
        }
        
        # Use coordinate agent to get comprehensive estimation
        result = await run_coordinate_agent(project_data)
        
        if result.get("success"):
            data = result.get("data", {})
            # Normalize payload for dashboard modal using simple ratios for labor/equipment/other
            estimation_block = data.get("estimation", {}) if isinstance(data, dict) else {}
            material_total = float(estimation_block.get("total_cost") or 0)
            labor_cost = round(material_total * 0.35, 2)
            equipment_cost = round(material_total * 0.10, 2)
            other_costs = round(material_total * 0.05, 2)
            total_cost = round(material_total + labor_cost + equipment_cost + other_costs, 2)
            normalized = {
                "project_id": project_id,
                "material_cost": material_total,
                "labor_cost": labor_cost,
                "equipment_cost": equipment_cost,
                "other_costs": other_costs,
                "total_cost": total_cost
            }
            return ApiResponse(
                success=True,
                message="Estimation calculated successfully using AI agents",
                data=normalized
            )
        else:
            # Fallback to placeholder data if agents fail
            estimation = {
                "project_id": project_id,
                "material_cost": 50000000,
                "labor_cost": 30000000,
                "equipment_cost": 15000000,
                "other_costs": 5000000,
                "total_cost": 100000000,
                "note": "Fallback estimation - agents unavailable"
            }
            return ApiResponse(
                success=True,
                message="Estimation calculated (fallback mode)",
                data=estimation
            )
    except Exception as e:
        return ApiResponse(
            success=False,
            message=f"Error calculating estimation: {str(e)}"
        )

@app.get("/api/projects/{project_id}/report")
async def get_project_report(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Generate and download project report using AI agents"""
    try:
        # Read project from DB for the current user
        project_result = get_project_by_id(db, project_id, current_user["id"])  # type: ignore
        if not project_result.get("success"):
            raise HTTPException(status_code=404, detail=project_result.get("message", "Project not found"))
        project = project_result["project"]

        # Build agent input from explicit columns (fallback to extra_info)
        # Normalize area_unit and other fields from explicit columns or extra_info keys
        extra = project.get("extra_info", {}) if isinstance(project.get("extra_info", {}), dict) else {}
        area_unit = project.get("area_unit") or extra.get("area_unit") or extra.get("areaUnit") or extra.get("unit") or "m2"
        project_data = {
            "project_id": project_id,
            "title": project.get("title") or project.get("name"),
            "project_type": project.get("type", "residential"),
            "building_type": project.get("building_type") or project.get("structure_type"),
            "area": float(project.get("area", 0)),
            "area_unit": area_unit,
            "floors": int(project.get("floors", 1)),
            "rooms": int(project.get("rooms", 1)),
            "bathrooms": int(project.get("bathrooms", 1)),
            "location": project.get("location") or extra.get("location"),
            "building_height": project.get("building_height") or extra.get("building_height"),
            "foundation_type": project.get("foundation_type") or extra.get("foundation_type"),
            "roof_type": project.get("roof_type") or extra.get("roof_type"),
            "quality_level": project.get("quality_level") or extra.get("quality_level"),
            "finishing_type": project.get("finishing_type") or extra.get("finishing_type"),
            "features": project.get("features") or extra.get("features", []),
            "description": project.get("description") or extra.get("description"),
            "currency": project.get("currency") or extra.get("currency", "USD"),
            "report_format": "pdf"
        }

        # Run coordinate agent to produce final PDF
        result = await run_coordinate_agent(project_data)
        if result.get("success") and result.get("pdf_content"):
            pdf_content = result.get("pdf_content")
            return StreamingResponse(
                io.BytesIO(pdf_content),
                media_type="application/pdf",
                headers={"Content-Disposition": f"attachment; filename=project-report-{project_id}.pdf"}
            )
        else:
            # Fallback: minimal PDF-like content (WeasyPrint may not be available)
            fallback_bytes = ("Project Report (Fallback)\n" + str(project_data)).encode("utf-8")
            return StreamingResponse(
                io.BytesIO(fallback_bytes),
                media_type="application/pdf",
                headers={"Content-Disposition": f"attachment; filename=project-report-{project_id}.pdf"}
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating report: {str(e)}")

@app.post("/api/agents/material-search")
async def material_search(input_data: dict):
    """Material Search Agent endpoint"""
    agent = MaterialSearchAgent()
    result = agent.calculate_materials(input_data)
    return result

@app.post("/api/agents/estimate")
async def estimate_project(materials: dict):
    """Estimator Agent endpoint"""
    agent = EstimatorAgent()
    # انتظار داریم ورودی به صورت {"materials": [...]} باشد
    result = agent.estimate(materials.get("materials", []))
    return result

@app.post("/api/agents/advice")
async def advisor_agent_endpoint(input_data: dict):
    """Advisor Agent endpoint"""
    estimation = input_data.get("estimation")
    quality_level = input_data.get("quality_level", "standard")
    agent = AdvisorAgent()
    result = agent.analyze(estimation, quality_level)
    return result

@app.post("/api/agents/report")
async def generate_report(input_data: dict):
    """Report Generator Agent endpoint"""
    project_info = input_data.get("project_info", {})
    material_search_output = input_data.get("material_search_output", {})
    estimation_output = input_data.get("estimation_output", {})
    advisor_output = input_data.get("advisor_output", {})
    report_format = input_data.get("report_format", "json")
    agent = ReportGeneratorAgent()
    result = agent.generate_report(
        project_info,
        material_search_output,
        estimation_output,
        advisor_output,
        report_format=report_format
    )
    if report_format == "pdf":
        return StreamingResponse(
            io.BytesIO(result),
            media_type="application/pdf",
            headers={
                "Content-Disposition": "attachment; filename=report.pdf"
            }
        )
    return result

@app.post("/api/agents/coordinate")
async def coordinate_agent_endpoint(input_data: dict):
    """Coordinate Agent endpoint: اجرای کل فرآیند و بازگرداندن گزارش نهایی"""
    result = await run_coordinate_agent(input_data)
    if input_data.get("report_format", "json") == "pdf":
        return StreamingResponse(
            io.BytesIO(result),
            media_type="application/pdf",
            headers={
                "Content-Disposition": "attachment; filename=report.pdf"
            }
        )
    return result

@app.post("/api/projects/{project_id}/reports", response_model=ApiResponse)
async def save_project_report(
    project_id: int,
    payload: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Save a report for a project owned by the current user."""
    try:
        # Ensure project exists and belongs to current user
        project_result = get_project_by_id(db, project_id, current_user["id"])  # type: ignore
        if not project_result.get("success"):
            return ApiResponse(success=False, message=project_result.get("message", "Project not found"))
        project = project_result["project"]

        # Normalize currency and area_unit
        extra = project.get("extra_info", {}) if isinstance(project.get("extra_info", {}), dict) else {}
        currency = project.get("currency") or extra.get("currency") or "USD"
        area_unit = project.get("area_unit") or extra.get("area_unit") or extra.get("areaUnit") or "m2"

        # Build report dict for DB layer
        estimation_json = payload.get("estimation_json") or {}
        total_cost = float(estimation_json.get("total_cost") or 0)
        # Ensure non-null file_path (placeholder when no physical PDF is stored)
        timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        safe_title = (payload.get("title") or project.get("title") or "report").lower().replace(" ", "-")
        file_path_placeholder = f"inline://reports/{project_id}/{safe_title}-{timestamp}.pdf"
        report = {
            "project_id": project_id,
            "title": payload.get("title") or project.get("title") or project.get("name") or "Project Report",
            "notes": payload.get("notes"),
            "format": payload.get("format", "pdf"),
            "file_path": file_path_placeholder,
            "created_by": current_user["id"],
            "currency": currency,
            "area": project.get("area"),
            "area_unit": area_unit,
            "total_cost": total_cost,
            "inputs_json": payload.get("inputs_json"),
            "materials_json": payload.get("materials_json"),
            "estimation_json": payload.get("estimation_json"),
            "advice_json": payload.get("advice_json"),
        }

        result = create_report(db, report)
        if result.get("success"):
            return ApiResponse(success=True, message="Report saved", data={"report_id": result.get("report_id")})
        else:
            return ApiResponse(success=False, message=result.get("message", "Failed to save report"))
    except Exception as e:
        return ApiResponse(success=False, message=f"Error saving report: {str(e)}")


# List all reports of current user
@app.get("/api/reports", response_model=ApiResponse)
async def list_user_reports(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    try:
        result = get_user_reports(db, current_user["id"])  # type: ignore
        if result.get("success"):
            return ApiResponse(
                success=True,
                message="Reports retrieved successfully",
                data={"reports": result.get("reports", [])}
            )
        else:
            return ApiResponse(success=False, message=result.get("message", "Failed to retrieve reports"))
    except Exception as e:
        return ApiResponse(success=False, message=f"Error retrieving reports: {str(e)}")

# Get single report details by id (current user only)
@app.get("/api/reports/{report_id}", response_model=ApiResponse)
async def get_single_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    try:
        result = get_report_by_id(db, report_id, int(current_user["id"]))
        if not result.get("success"):
            return ApiResponse(success=False, message=result.get("message", "Report not found"))
        report = result.get("report")
        if not report or int(report.get("created_by")) != int(current_user["id"]):  # type: ignore
            return ApiResponse(success=False, message="Unauthorized to view this report")
        return ApiResponse(success=True, message="Report retrieved", data={"report": report})
    except Exception as e:
        return ApiResponse(success=False, message=f"Error retrieving report: {str(e)}")

# Delete a report by id (current user only)
@app.delete("/api/reports/{report_id}", response_model=ApiResponse)
async def delete_single_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    try:
        # Ensure ownership
        result = get_report_by_id(db, report_id, int(current_user["id"]))
        if not result.get("success"):
            return ApiResponse(success=False, message=result.get("message", "Report not found"))
        report = result.get("report")
        if not report or int(report.get("created_by")) != int(current_user["id"]):  # type: ignore
            return ApiResponse(success=False, message="Unauthorized to delete this report")
        del_res = delete_report(db, report_id, int(current_user["id"]))
        if del_res.get("success"):
            return ApiResponse(success=True, message="Report deleted")
        else:
            return ApiResponse(success=False, message=del_res.get("message", "Failed to delete report"))
    except Exception as e:
        return ApiResponse(success=False, message=f"Error deleting report: {str(e)}")

if __name__ == "__main__":
    print("🚀 Starting Construction Estimation API...")
    print("📋 Available endpoints:")
    print("   - GET / : Root endpoint")
    print("   - GET /health : Health check")
    print("   - GET /api/version : API version")
    print("   - GET /docs : API documentation (Swagger)")
    print("   - GET /redoc : API documentation (ReDoc)")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )