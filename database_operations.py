#!/usr/bin/env python3
"""
Database operations for Construction Estimation Project
"""

import hashlib
import json
from sqlalchemy.orm import Session
from sqlalchemy import text
from database_config import SessionLocal, engine
from models import UserCreate, UserResponse, ProjectCreate, ProjectResponse

def hash_password(password: str) -> str:
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return hash_password(plain_password) == hashed_password

# User operations
def create_user(db: Session, user: UserCreate) -> dict:
    """Create a new user"""
    try:
        # Check if username already exists
        existing_user = db.execute(
            text("SELECT id FROM users WHERE username = :username"),
            {"username": user.username}
        ).fetchone()
        
        if existing_user:
            return {"success": False, "message": "Username already exists"}
        
        # Check if email already exists
        existing_email = db.execute(
            text("SELECT id FROM users WHERE email = :email"),
            {"email": user.email}
        ).fetchone()
        
        if existing_email:
            return {"success": False, "message": "Email already exists"}
        
        # Hash password
        hashed_password = hash_password(user.password)
        
        # Insert new user
        result = db.execute(
            text("""
                INSERT INTO users (first_name, last_name, phone, username, password, 
                                 role, membership_type, budget, email)
                VALUES (:first_name, :last_name, :phone, :username, :password,
                        :role, :membership_type, :budget, :email)
                RETURNING id
            """),
            {
                "first_name": user.first_name,
                "last_name": user.last_name,
                "phone": user.phone,
                "username": user.username,
                "password": hashed_password,
                "role": user.role.value,
                "membership_type": user.membership_type,
                "budget": user.budget,
                "email": user.email
            }
        )
        
        user_id = result.fetchone()[0]
        db.commit()
        
        return {
            "success": True,
            "message": "User created successfully",
            "user_id": user_id
        }
        
    except Exception as e:
        db.rollback()
        return {"success": False, "message": f"Error creating user: {str(e)}"}

def get_user_by_username(db: Session, username: str) -> dict:
    """Get user by username"""
    try:
        result = db.execute(
            text("SELECT * FROM users WHERE username = :username"),
            {"username": username}
        ).fetchone()
        
        if result:
            return {
                "success": True,
                "user": dict(result._mapping)
            }
        else:
            return {"success": False, "message": "User not found"}
            
    except Exception as e:
        return {"success": False, "message": f"Error getting user: {str(e)}"}

def authenticate_user(db: Session, username: str, password: str) -> dict:
    """Authenticate user with username and password"""
    try:
        result = db.execute(
            text("SELECT * FROM users WHERE username = :username"),
            {"username": username}
        ).fetchone()
        
        if not result:
            return {"success": False, "message": "Invalid username or password"}
        
        user_data = dict(result._mapping)
        
        if verify_password(password, user_data['password']):
            return {
                "success": True,
                "user": user_data
            }
        else:
            return {"success": False, "message": "Invalid username or password"}
            
    except Exception as e:
        return {"success": False, "message": f"Error authenticating user: {str(e)}"}

# Project operations
def create_project(db: Session, project: ProjectCreate, user_id: int) -> dict:
    """Create a new project"""
    try:
        result = db.execute(
            text("""
                INSERT INTO projects (
                    user_id, title, type, area, structure_type,
                    location, standard, floors, rooms, bathrooms,
                    area_unit, building_type, building_height, foundation_type,
                    roof_type, quality_level, finishing_type, features,
                    description, extra_info
                )
                VALUES (
                    :user_id, :title, :type, :area, :structure_type,
                    :location, :standard, :floors, :rooms, :bathrooms,
                    :area_unit, :building_type, :building_height, :foundation_type,
                    :roof_type, :quality_level, :finishing_type, CAST(:features_json AS JSONB),
                    :description, :extra_info
                )
                RETURNING id
            """),
            {
                "user_id": user_id,
                "title": project.title,
                "type": project.type.value if hasattr(project.type, "value") else project.type,
                "area": project.area,
                "structure_type": project.structure_type,
                "location": project.location,
                "standard": project.standard.value if project.standard else None,
                "floors": project.floors,
                "rooms": project.rooms,
                "bathrooms": project.bathrooms,
                # explicit fields
                "area_unit": project.area_unit,
                "building_type": project.building_type,
                "building_height": project.building_height,
                "foundation_type": project.foundation_type,
                "roof_type": project.roof_type,
                "quality_level": project.quality_level,
                "finishing_type": project.finishing_type,
                "features_json": json.dumps(project.features) if project.features is not None else None,
                "description": project.description,
                # keep extra_info for backward compatibility
                "extra_info": json.dumps(project.extra_info) if project.extra_info else None
            }
        )
        
        project_id = result.fetchone()[0]
        db.commit()
        
        return {
            "success": True,
            "message": "Project created successfully",
            "project_id": project_id
        }
        
    except Exception as e:
        db.rollback()
        return {"success": False, "message": f"Error creating project: {str(e)}"}

def get_project_by_id(db: Session, project_id: str, user_id: int = None) -> dict:
    """Get project by ID"""
    try:
        query = "SELECT * FROM projects WHERE id = :project_id"
        params = {"project_id": project_id}
        
        if user_id:
            query += " AND user_id = :user_id"
            params["user_id"] = user_id
        
        result = db.execute(text(query), params).fetchone()
        
        if result:
            project_data = dict(result._mapping)
            # Parse extra_info JSON if it exists
            if project_data.get('extra_info'):
                try:
                    project_data['extra_info'] = json.loads(project_data['extra_info'])
                except:
                    project_data['extra_info'] = {}
            
            return {
                "success": True,
                "project": project_data
            }
        else:
            return {"success": False, "message": "Project not found"}
            
    except Exception as e:
        return {"success": False, "message": f"Error getting project: {str(e)}"}

def get_user_projects(db: Session, user_id: int) -> dict:
    """Get all projects for a given user"""
    try:
        results = db.execute(
            text("SELECT * FROM projects WHERE user_id = :user_id ORDER BY created_at DESC"),
            {"user_id": user_id}
        ).fetchall()
        projects = []
        for row in results:
            proj = dict(row._mapping)
            if proj.get('extra_info'):
                try:
                    proj['extra_info'] = json.loads(proj['extra_info'])
                except Exception:
                    proj['extra_info'] = {}
            projects.append(proj)
        return {"success": True, "projects": projects}
    except Exception as e:
        return {"success": False, "message": f"Error retrieving projects: {str(e)}"}


def delete_project(db: Session, project_id: int, user_id: int) -> dict:
    """Delete a project owned by the given user and its dependent data"""
    try:
        # Ensure the project exists and belongs to the user
        result = db.execute(
            text("SELECT id FROM projects WHERE id = :project_id AND user_id = :user_id"),
            {"project_id": project_id, "user_id": user_id}
        ).fetchone()
        if not result:
            return {"success": False, "message": "Project not found or access denied"}

        # Delete dependent records first (robust even if FK doesn't have CASCADE)
        db.execute(
            text("DELETE FROM estimations WHERE project_id = :project_id"),
            {"project_id": project_id}
        )

        # Delete the project itself
        db.execute(
            text("DELETE FROM projects WHERE id = :project_id AND user_id = :user_id"),
            {"project_id": project_id, "user_id": user_id}
        )
        db.commit()
        return {"success": True, "message": "Project deleted successfully"}
    except Exception as e:
        db.rollback()
        return {"success": False, "message": f"Error deleting project: {str(e)}"}


def update_project(db: Session, project_id: int, user_id: int, project: ProjectCreate) -> dict:
    """Update an existing project owned by the given user with new data."""
    try:
        # Ensure the project exists and belongs to the user
        exists = db.execute(
            text("SELECT id FROM projects WHERE id = :project_id AND user_id = :user_id"),
            {"project_id": project_id, "user_id": user_id}
        ).fetchone()
        if not exists:
            return {"success": False, "message": "Project not found or access denied"}

        # Prepare mirrored extra_info payload
        extra_info = {
            "area_unit": project.area_unit,
            "building_type": project.building_type,
            "building_height": project.building_height,
            "foundation_type": project.foundation_type,
            "roof_type": project.roof_type,
            "quality_level": project.quality_level,
            "finishing_type": project.finishing_type,
            "features": project.features or [],
            "description": project.description
        }

        # Perform update using explicit columns
        db.execute(
            text(
                """
                UPDATE projects SET
                    title = :title,
                    type = :type,
                    area = :area,
                    structure_type = :structure_type,
                    location = :location,
                    standard = :standard,
                    floors = :floors,
                    rooms = :rooms,
                    bathrooms = :bathrooms,
                    area_unit = :area_unit,
                    building_type = :building_type,
                    building_height = :building_height,
                    foundation_type = :foundation_type,
                    roof_type = :roof_type,
                    quality_level = :quality_level,
                    finishing_type = :finishing_type,
                    features = CAST(:features_json AS JSONB),
                    description = :description,
                    extra_info = :extra_info
                WHERE id = :project_id AND user_id = :user_id
                """
            ),
            {
                "project_id": project_id,
                "user_id": user_id,
                "title": project.title,
                "type": project.type.value if hasattr(project.type, "value") else project.type,
                "area": project.area,
                "structure_type": project.structure_type,
                "location": project.location,
                "standard": project.standard.value if project.standard else None,
                "floors": project.floors,
                "rooms": project.rooms,
                "bathrooms": project.bathrooms,
                "area_unit": project.area_unit,
                "building_type": project.building_type,
                "building_height": project.building_height,
                "foundation_type": project.foundation_type,
                "roof_type": project.roof_type,
                "quality_level": project.quality_level,
                "finishing_type": project.finishing_type,
                "features_json": json.dumps(project.features) if project.features is not None else None,
                "description": project.description,
                "extra_info": json.dumps(extra_info)
            }
        )

        db.commit()
        return {"success": True, "message": "Project updated successfully", "project_id": project_id}
    except Exception as e:
        db.rollback()
        return {"success": False, "message": f"Error updating project: {str(e)}"}


def ensure_project_type_constraint() -> None:
    """Ensure projects.type check constraint includes 'infrastructure'"""
    try:
        # Use transactional DDL to ensure commit
        with engine.begin() as connection:
            # Drop existing constraint if present
            connection.execute(text("ALTER TABLE projects DROP CONSTRAINT IF EXISTS projects_type_check"))
            # Add updated constraint including 'infrastructure'
            connection.execute(text(
                """
                ALTER TABLE projects ADD CONSTRAINT projects_type_check
                CHECK (type IN ('residential','commercial','office','industrial','educational','infrastructure'))
                """
            ))
        print("✅ Updated projects.type check constraint to include 'infrastructure'")
    except Exception as e:
        print(f"⚠️ Could not update projects.type check constraint: {e}")

# NEW: ensure explicit columns and migrate extra_info
def ensure_project_extra_columns_and_migrate() -> None:
    """Add explicit columns for fields currently in extra_info and migrate existing data."""
    try:
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE projects ADD COLUMN IF NOT EXISTS area_unit VARCHAR(10)"))
            connection.execute(text("ALTER TABLE projects ADD COLUMN IF NOT EXISTS building_type VARCHAR(50)"))
            connection.execute(text("ALTER TABLE projects ADD COLUMN IF NOT EXISTS building_height DECIMAL(10,2)"))
            connection.execute(text("ALTER TABLE projects ADD COLUMN IF NOT EXISTS foundation_type VARCHAR(50)"))
            connection.execute(text("ALTER TABLE projects ADD COLUMN IF NOT EXISTS roof_type VARCHAR(50)"))
            connection.execute(text("ALTER TABLE projects ADD COLUMN IF NOT EXISTS quality_level VARCHAR(50)"))
            connection.execute(text("ALTER TABLE projects ADD COLUMN IF NOT EXISTS finishing_type VARCHAR(50)"))
            connection.execute(text("ALTER TABLE projects ADD COLUMN IF NOT EXISTS features JSONB"))
            connection.execute(text("ALTER TABLE projects ADD COLUMN IF NOT EXISTS description TEXT"))
            
            rows = connection.execute(text("SELECT id, extra_info FROM projects WHERE extra_info IS NOT NULL")).fetchall()
            for row in rows:
                m = dict(row._mapping)
                raw_extra = m.get('extra_info')
                try:
                    extra = raw_extra if isinstance(raw_extra, dict) else json.loads(raw_extra)
                except Exception:
                    extra = None
                if not isinstance(extra, dict):
                    continue
                def first(*args):
                    for a in args:
                        if a is not None and a != '':
                            return a
                    return None
                area_unit = first(extra.get('area_unit'), extra.get('areaUnit'), extra.get('unit'))
                building_type = first(extra.get('building_type'), extra.get('buildingType'), extra.get('structure_type'))
                building_height = first(extra.get('building_height'), extra.get('buildingHeight'), extra.get('height'))
                try:
                    building_height = float(building_height) if building_height is not None else None
                except Exception:
                    building_height = None
                foundation_type = first(extra.get('foundation_type'), extra.get('foundationType'))
                roof_type = first(extra.get('roof_type'), extra.get('roofType'))
                quality_level = first(extra.get('quality_level'), extra.get('qualityLevel'), extra.get('quality'))
                finishing_type = first(extra.get('finishing_type'), extra.get('finishingType'), extra.get('finishing'))
                features = first(extra.get('features'), extra.get('additional_features'))
                if isinstance(features, str):
                    parts = [p.strip() for p in features.split(',') if p.strip()]
                    features = parts if parts else None
                description = extra.get('description')
                connection.execute(text(
                    """
                    UPDATE projects SET
                        area_unit = COALESCE(:area_unit, area_unit),
                        building_type = COALESCE(:building_type, building_type),
                        building_height = COALESCE(:building_height, building_height),
                        foundation_type = COALESCE(:foundation_type, foundation_type),
                        roof_type = COALESCE(:roof_type, roof_type),
                        quality_level = COALESCE(:quality_level, quality_level),
                        finishing_type = COALESCE(:finishing_type, finishing_type),
                        features = COALESCE(CAST(:features_json AS JSONB), features),
                        description = COALESCE(:description, description)
                    WHERE id = :id
                    """
                ), {
                    "id": m['id'],
                    "area_unit": area_unit,
                    "building_type": building_type,
                    "building_height": building_height,
                    "foundation_type": foundation_type,
                    "roof_type": roof_type,
                    "quality_level": quality_level,
                    "finishing_type": finishing_type,
                    "features_json": json.dumps(features) if features is not None else None,
                    "description": description
                })
        print("✅ Ensured extra columns exist and migrated extra_info to columns")
    except Exception as e:
        print(f"⚠️ Could not ensure extra columns or migrate: {e}")


# Reports table ensure and CRUD functions

def ensure_reports_table() -> None:
    """Create the reports table if it does not exist and add required columns."""
    try:
        with engine.begin() as connection:
            connection.execute(text(
                """
                CREATE TABLE IF NOT EXISTS reports (
                    id SERIAL PRIMARY KEY,
                    project_id INTEGER NOT NULL,
                    title VARCHAR(255),
                    notes TEXT,
                    format VARCHAR(20) DEFAULT 'pdf',
                    file_path TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW(),
                    created_by INTEGER NOT NULL,
                    currency VARCHAR(10),
                    area DECIMAL(12,2),
                    area_unit VARCHAR(10),
                    total_cost DECIMAL(18,2),
                    inputs_json JSONB,
                    materials_json JSONB,
                    estimation_json JSONB,
                    advice_json JSONB
                )
                """
            ))
            # Indexes to speed up queries
            connection.execute(text("CREATE INDEX IF NOT EXISTS idx_reports_project ON reports(project_id)"))
            connection.execute(text("CREATE INDEX IF NOT EXISTS idx_reports_creator ON reports(created_by)"))
            # Try to add FK constraint (ignore errors if already exists)
            try:
                connection.execute(text(
                    "ALTER TABLE reports ADD CONSTRAINT reports_project_fk FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE"
                ))
            except Exception:
                pass
        print("✅ Ensured reports table exists")
    except Exception as e:
        print(f"⚠️ Could not ensure reports table: {e}")


def create_report(db: Session, report: dict) -> dict:
    """Create a new report record."""
    try:
        result = db.execute(text(
            """
            INSERT INTO reports (
                project_id, title, notes, format, file_path, created_by, currency,
                area, area_unit, total_cost, inputs_json, materials_json, estimation_json, advice_json
            ) VALUES (
                :project_id, :title, :notes, :format, :file_path, :created_by, :currency,
                :area, :area_unit, :total_cost, CAST(:inputs_json AS JSONB), CAST(:materials_json AS JSONB), CAST(:estimation_json AS JSONB), CAST(:advice_json AS JSONB)
            ) RETURNING id
            """
        ), {
            "project_id": report.get("project_id"),
            "title": report.get("title"),
            "notes": report.get("notes"),
            "format": report.get("format", "pdf"),
            "file_path": report.get("file_path"),
            "created_by": report.get("created_by"),
            "currency": report.get("currency"),
            "area": report.get("area"),
            "area_unit": report.get("area_unit"),
            "total_cost": report.get("total_cost"),
            "inputs_json": json.dumps(report.get("inputs_json")) if report.get("inputs_json") is not None else None,
            "materials_json": json.dumps(report.get("materials_json")) if report.get("materials_json") is not None else None,
            "estimation_json": json.dumps(report.get("estimation_json")) if report.get("estimation_json") is not None else None,
            "advice_json": json.dumps(report.get("advice_json")) if report.get("advice_json") is not None else None,
        })
        report_id = result.fetchone()[0]
        db.commit()
        return {"success": True, "message": "Report saved", "report_id": report_id}
    except Exception as e:
        db.rollback()
        return {"success": False, "message": f"Error creating report: {e}"}


def get_user_reports(db: Session, user_id: int) -> dict:
    """Get all saved reports for the user across projects."""
    try:
        rows = db.execute(text(
            "SELECT * FROM reports WHERE created_by = :user_id ORDER BY created_at DESC"
        ), {"user_id": user_id}).fetchall()
        reports = []
        for row in rows:
            m = dict(row._mapping)
            for k in ["inputs_json", "materials_json", "estimation_json", "advice_json"]:
                if m.get(k):
                    try:
                        m[k] = json.loads(m[k]) if isinstance(m[k], str) else m[k]
                    except Exception:
                        m[k] = None
            reports.append(m)
        return {"success": True, "reports": reports}
    except Exception as e:
        return {"success": False, "message": f"Error retrieving reports: {e}"}


def get_project_reports(db: Session, project_id: int, user_id: int) -> dict:
    """Get all saved reports for a project owned by the user."""
    try:
        rows = db.execute(text(
            "SELECT * FROM reports WHERE project_id = :project_id AND created_by = :user_id ORDER BY created_at DESC"
        ), {"project_id": project_id, "user_id": user_id}).fetchall()
        reports = []
        for row in rows:
            m = dict(row._mapping)
            for k in ["inputs_json", "materials_json", "estimation_json", "advice_json"]:
                if m.get(k):
                    try:
                        m[k] = json.loads(m[k]) if isinstance(m[k], str) else m[k]
                    except Exception:
                        m[k] = None
            reports.append(m)
        return {"success": True, "reports": reports}
    except Exception as e:
        return {"success": False, "message": f"Error retrieving reports: {e}"}


def get_report_by_id(db: Session, report_id: int, user_id: int) -> dict:
    """Get a single report by ID ensuring ownership."""
    try:
        row = db.execute(text(
            "SELECT * FROM reports WHERE id = :id AND created_by = :user_id"
        ), {"id": report_id, "user_id": user_id}).fetchone()
        if not row:
            return {"success": False, "message": "Report not found or access denied"}
        m = dict(row._mapping)
        for k in ["inputs_json", "materials_json", "estimation_json", "advice_json"]:
            if m.get(k):
                try:
                    m[k] = json.loads(m[k]) if isinstance(m[k], str) else m[k]
                except Exception:
                    m[k] = None
        return {"success": True, "report": m}
    except Exception as e:
        return {"success": False, "message": f"Error getting report: {e}"}


def delete_report(db: Session, report_id: int, user_id: int) -> dict:
    """Delete a report owned by the user."""
    try:
        exists = db.execute(text(
            "SELECT id FROM reports WHERE id = :id AND created_by = :user_id"
        ), {"id": report_id, "user_id": user_id}).fetchone()
        if not exists:
            return {"success": False, "message": "Report not found or access denied"}
        db.execute(text("DELETE FROM reports WHERE id = :id"), {"id": report_id})
        db.commit()
        return {"success": True, "message": "Report deleted"}
    except Exception as e:
        db.rollback()
        return {"success": False, "message": f"Error deleting report: {e}"}


def update_report(db: Session, report_id: int, user_id: int, title: str = None, notes: str = None) -> dict:
    """Update a report's title and/or notes for the owner."""
    try:
        exists = db.execute(text(
            "SELECT id FROM reports WHERE id = :id AND created_by = :user_id"
        ), {"id": report_id, "user_id": user_id}).fetchone()
        if not exists:
            return {"success": False, "message": "Report not found or access denied"}
        db.execute(text(
            """
            UPDATE reports SET
                title = COALESCE(:title, title),
                notes = COALESCE(:notes, notes)
            WHERE id = :id
            """
        ), {"id": report_id, "title": title, "notes": notes})
        db.commit()
        return {"success": True, "message": "Report updated"}
    except Exception as e:
        db.rollback()
        return {"success": False, "message": f"Error updating report: {e}"}


def test_database_operations():
    """Test database operations"""
    try:
        db = SessionLocal()
        
        # Test user creation
        test_user = UserCreate(
            first_name="Test",
            last_name="User",
            username="testuser",
            role="contractor",
            email="test@example.com",
            password="password123"
        )
        
        result = create_user(db, test_user)
        print(f"✅ User creation test: {result['success']}")
        
        # Test user authentication
        auth_result = authenticate_user(db, "testuser", "password123")
        print(f"✅ User authentication test: {auth_result['success']}")
        
        # Test project creation
        test_project = ProjectCreate(
            title="Test Project",
            type="residential",
            area=150.5,
            floors=2,
            rooms=3,
            bathrooms=2
        )
        
        if auth_result['success']:
            project_result = create_project(db, test_project, auth_result['user']['id'])
            print(f"✅ Project creation test: {project_result['success']}")
        
        db.close()
        print("✅ All database operations working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Database operations test failed: {e}")
        return False

if __name__ == "__main__":
    test_database_operations()