#!/usr/bin/env python3
"""
Pydantic models for API endpoints
"""

from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List
from enum import Enum

# Enums
class UserRole(str, Enum):
    CONTRACTOR = "contractor"
    CLIENT = "client"
    ENGINEER = "engineer"
    ARCHITECT = "architect"

class ProjectType(str, Enum):
    RESIDENTIAL = "residential"
    COMMERCIAL = "commercial"
    OFFICE = "office"
    INDUSTRIAL = "industrial"
    EDUCATIONAL = "educational"
    INFRASTRUCTURE = "infrastructure"

class StandardType(str, Enum):
    EUROCODE = "Eurocode"
    ACI = "ACI"
    BS = "BS"
    OTHER = "other"

# User models
class UserBase(BaseModel):
    first_name: str
    last_name: str
    phone: Optional[str] = None
    username: str
    role: UserRole
    membership_type: str = "basic"
    budget: Optional[float] = None
    email: EmailStr

class UserCreate(UserBase):
    password: str
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters')
        return v

class UserResponse(UserBase):
    id: int
    created_at: str
    
    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    username: str
    password: str

# Project models
class ProjectBase(BaseModel):
    title: str
    type: ProjectType
    area: float
    structure_type: Optional[str] = None
    location: Optional[str] = None
    standard: Optional[StandardType] = None
    floors: int = 1
    rooms: int = 1
    bathrooms: int = 1
    extra_info: Optional[dict] = None
    # Added fields to cover all 17 form items
    area_unit: Optional[str] = "m2"
    building_type: Optional[str] = None
    building_height: Optional[float] = None
    foundation_type: Optional[str] = None
    roof_type: Optional[str] = None
    quality_level: Optional[str] = None
    finishing_type: Optional[str] = None
    features: Optional[List[str]] = None
    description: Optional[str] = None

class ProjectCreate(ProjectBase):
    pass

class ProjectResponse(ProjectBase):
    id: int
    user_id: int
    design_file: Optional[str] = None
    selected_template_id: Optional[int] = None
    created_at: str
    
    class Config:
        from_attributes = True

# Response models
class ApiResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

# Test function
def test_models():
    """Test model creation"""
    try:
        # Test user creation
        user_data = {
            "first_name": "John",
            "last_name": "Doe",
            "username": "johndoe",
            "role": UserRole.CONTRACTOR,
            "email": "john@example.com",
            "password": "password123"
        }
        user = UserCreate(**user_data)
        print("✅ User model test passed")
        
        # Test project creation
        project_data = {
            "title": "Test Project",
            "type": ProjectType.RESIDENTIAL,
            "area": 150.5,
            "floors": 2,
            "rooms": 3,
            "bathrooms": 2
        }
        project = ProjectCreate(**project_data)
        print("✅ Project model test passed")
        
        print("✅ All models working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Model test failed: {e}")
        return False

if __name__ == "__main__":
    test_models()