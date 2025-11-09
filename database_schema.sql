-- Construction Cost Estimation Project Database Schema
-- Created: 2024

-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    phone VARCHAR(20),
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('contractor', 'client', 'engineer', 'architect')),
    membership_type VARCHAR(20) DEFAULT 'basic',
    budget DECIMAL(15,2),
    email VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Projects table
CREATE TABLE projects (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    type VARCHAR(30) NOT NULL CHECK (type IN ('residential', 'commercial', 'office', 'industrial', 'educational', 'infrastructure')),
    area DECIMAL(10,2) NOT NULL,
    structure_type VARCHAR(50),
    location VARCHAR(200),
    standard VARCHAR(20) CHECK (standard IN ('Eurocode', 'ACI', 'BS', 'other')),
    design_file VARCHAR(500),
    selected_template_id INTEGER,
    floors INTEGER DEFAULT 1,
    rooms INTEGER DEFAULT 1,
    bathrooms INTEGER DEFAULT 1,
    -- explicit columns formerly in extra_info
    area_unit VARCHAR(10),
    building_type VARCHAR(50),
    building_height DECIMAL(10,2),
    foundation_type VARCHAR(50),
    roof_type VARCHAR(50),
    quality_level VARCHAR(50),
    finishing_type VARCHAR(50),
    features JSONB,
    description TEXT,
    extra_info JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Templates table
CREATE TABLE templates (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    file_path VARCHAR(500),
    standard VARCHAR(20) CHECK (standard IN ('Eurocode', 'ACI', 'BS', 'other')),
    project_type VARCHAR(30) NOT NULL CHECK (project_type IN ('residential', 'commercial', 'office', 'industrial', 'educational')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Estimations table
CREATE TABLE estimations (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    total_cost DECIMAL(15,2) NOT NULL,
    details JSONB,
    charts_data JSONB,
    suggestions JSONB,
    pdf_file VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Vendors table
CREATE TABLE vendors (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    location VARCHAR(200),
    latitude DECIMAL(10,8),
    longitude DECIMAL(11,8),
    contact_info JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Vendor materials table
CREATE TABLE vendor_materials (
    id SERIAL PRIMARY KEY,
    vendor_id INTEGER NOT NULL REFERENCES vendors(id) ON DELETE CASCADE,
    material_name VARCHAR(100) NOT NULL,
    material_type VARCHAR(50) NOT NULL,
    price DECIMAL(10,2),
    unit VARCHAR(20),
    availability BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add foreign key constraint for selected_template_id in projects table
ALTER TABLE projects ADD CONSTRAINT fk_projects_template 
FOREIGN KEY (selected_template_id) REFERENCES templates(id) ON DELETE SET NULL;