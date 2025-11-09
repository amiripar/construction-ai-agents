// Dashboard JavaScript

// Global variables
let currentUser = null;
let currentSection = 'overview';
let currentStep = 1;
let projectData = {};
let lastEstimatedProjectId = null;
let projects = [];
let projectsLoaded = false;

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    checkAuth();
    initializeDashboard();
    loadUserProjects();
});

// Check authentication
function checkAuth() {
    const token = sessionStorage.getItem('authToken');
    if (!token) {
        window.location.href = '/index.html';
        return;
    }
    
    // Load user from sessionStorage as fallback
    const storedUser = sessionStorage.getItem('currentUser');
    if (storedUser) {
        currentUser = JSON.parse(storedUser);
        updateUserInfo();
    }
    
    // Verify token with backend
    fetch('/api/verify-token', {
        method: 'GET',
        headers: {
            'Authorization': `Bearer ${token}`
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Token invalid');
        }
        return response.json();
    })
    .then(data => {
        const user = (data && (data.data && data.data.user)) || data.user || null;
        if (user) {
            currentUser = user;
            updateUserInfo();
        }
    })
    .catch(error => {
        console.error('Auth error:', error);
        sessionStorage.removeItem('authToken');
        sessionStorage.removeItem('currentUser');
        window.location.href = '/index.html';
    });
}

// Initialize dashboard functionality
function initializeDashboard() {
    // Menu item click handlers
    document.querySelectorAll('.menu-item').forEach(item => {
        item.addEventListener('click', function() {
            const section = this.dataset.section;
            showSection(section);
        });
    });
    
    // Wire top navigation (Projects, Reports, Profile) to sections
    const topNavLinks = document.querySelectorAll('.nav-link[href^="#"]');
    topNavLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const target = link.getAttribute('href').replace('#', '');
            const allowed = ['overview','projects','new-project','reports','profile'];
            if (allowed.includes(target)) {
                showSection(target);
                // Update URL hash for deep-linking
                window.location.hash = target;
            }
        });
    });
    
    // Form step navigation (guards to avoid null addEventListener)
    const nextBtn = document.getElementById('nextStep');
    if (nextBtn) nextBtn.addEventListener('click', nextStep);
    const prevBtn = document.getElementById('prevStep');
    if (prevBtn) prevBtn.addEventListener('click', prevStep);
    const submitBtn = document.getElementById('submitProject');
    if (submitBtn) submitBtn.addEventListener('click', submitProject);
    
    // Project form submission
    const formEl = document.getElementById('newProjectForm');
    if (formEl) formEl.addEventListener('submit', handleProjectSubmit);
    
    // Logout handler
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) logoutBtn.addEventListener('click', logout);
    
    // Mobile menu toggle
    const menuToggle = document.getElementById('menuToggle');
    if (menuToggle) {
        menuToggle.addEventListener('click', toggleSidebar);
    }
    
    // Enable tab navigation via progress bar steps
    document.querySelectorAll('.progress-step').forEach(stepEl => {
        stepEl.addEventListener('click', function() {
            const targetStep = parseInt(this.dataset.step, 10);
            if (!isNaN(targetStep) && targetStep >= 1 && targetStep <= 3) {
                currentStep = targetStep;
                updateFormStep();
            }
        });
    });

    // Set sensible defaults to reduce validation friction
    try {
        const ptSel = document.getElementById('projectType');
        if (ptSel && !ptSel.value) ptSel.value = 'residential';
        const btSel = document.getElementById('buildingType');
        if (btSel && !btSel.value) btSel.value = 'wood_frame_house';
    } catch (_) {}
    
    // Initialize first section based on URL hash
    const hash = (window.location.hash || '').replace('#','');
    const allowed = ['overview','projects','new-project','reports','profile'];
    const initialSection = allowed.includes(hash) ? hash : 'overview';
    showSection(initialSection);

    // React to manual URL hash changes
    window.addEventListener('hashchange', () => {
        const newHash = (window.location.hash || '').replace('#','');
        if (allowed.includes(newHash)) {
            showSection(newHash);
        }
    });
}

// Show specific section
function showSection(sectionName) {
    try {
        // Update menu active state
        document.querySelectorAll('.menu-item').forEach(item => {
            item.classList.remove('active');
        });
        
        const menuItem = document.querySelector(`[data-section="${sectionName}"]`);
        if (menuItem) {
            menuItem.classList.add('active');
        }
        
        // Update content sections
        document.querySelectorAll('.content-section').forEach(section => {
            section.classList.remove('active');
        });
        
        // Handle section name mapping
        let sectionId = sectionName;
        if (sectionName === 'new-project') {
            sectionId = 'new-project';
        }
        
        const targetSection = document.getElementById(sectionId);
        if (targetSection) {
            targetSection.classList.add('active');
        }
        
        currentSection = sectionName;
        
        // Load section-specific data
        switch(sectionName) {
            case 'overview':
                if (projectsLoaded) {
                    updateStats();
                    loadRecentProjects();
                } else {
                    loadUserProjects();
                }
                break;
            case 'projects':
                loadUserProjects();
                break;
            case 'reports':
                loadReports();
                break;
            case 'profile':
                loadProfile();
                break;
        }
    } catch (error) {
        console.error('Error in showSection:', error);
    }
}

// Project form step navigation
function nextStep() {
    if (validateCurrentStep()) {
        if (currentStep < 3) {
            currentStep++;
            updateFormStep();
        }
    }
}

function prevStep() {
    if (currentStep > 1) {
        currentStep--;
        updateFormStep();
    }
}

function updateFormStep() {
    // Hide all steps
    document.querySelectorAll('.form-step').forEach(step => {
        step.classList.remove('active');
    });
    
    // Show current step
    document.getElementById(`step${currentStep}`).classList.add('active');
    
    // Update progress bar
    document.querySelectorAll('.progress-step').forEach((step, index) => {
        if (index < currentStep) {
            step.classList.add('active');
        } else {
            step.classList.remove('active');
        }
    });
    
    // Update button visibility (with null guards)
    const prevBtn = document.getElementById('prevStep');
    if (prevBtn) prevBtn.style.display = currentStep === 1 ? 'none' : 'inline-block';
    const nextBtn = document.getElementById('nextStep');
    if (nextBtn) nextBtn.style.display = currentStep === 3 ? 'none' : 'inline-block';
    const submitBtn = document.getElementById('submitProject');
    if (submitBtn) submitBtn.style.display = currentStep === 3 ? 'inline-block' : 'none';
}

// Validate current form step
function validateCurrentStep() {
    const stepEl = document.getElementById(`step${currentStep}`);
    if (!stepEl) return true;

    const requiredFields = stepEl.querySelectorAll('input[required], select[required], textarea[required]');
    let isValid = true;
    let firstInvalid = null;

    requiredFields.forEach(field => {
        // Remove previous inline error
        const prevError = field.parentElement.querySelector('.field-error');
        if (prevError) prevError.remove();

        let fieldValid = true;
        const tag = (field.tagName || '').toLowerCase();

        if (tag === 'select') {
            fieldValid = !!field.value;
        } else if (field.type === 'number') {
            const valStr = field.value;
            const val = Number(valStr);
            const hasValue = valStr !== '' && !Number.isNaN(val);
            const minAttr = field.getAttribute('min');
            const min = minAttr != null ? Number(minAttr) : null;
            fieldValid = hasValue && (min == null || val >= min);
        } else {
            fieldValid = !!field.value && !!field.value.trim();
        }

        if (!fieldValid) {
            field.style.borderColor = '#dc3545';
            // Inline error in Farsi
            const err = document.createElement('small');
            err.className = 'field-error';
            err.style.color = '#dc3545';
            err.style.display = 'block';
            err.style.marginTop = '6px';
            err.textContent = 'این فیلد الزامی است';
            field.parentElement.appendChild(err);
            isValid = false;
            if (!firstInvalid) firstInvalid = field;
        } else {
            field.style.borderColor = '#e9ecef';
        }
    });

    if (!isValid) {
        showNotification('لطفاً همه فیلدهای ضروری این مرحله را پر کنید', 'error');
        try {
            firstInvalid && firstInvalid.focus();
            firstInvalid && firstInvalid.scrollIntoView({ behavior: 'smooth', block: 'center' });
        } catch (_) {}
    }

    return isValid;
}

// Handle project form submission
function handleProjectSubmit(e) {
    e.preventDefault();
    
    if (!validateCurrentStep()) {
        return;
    }
    
    // Collect form data
    const formData = new FormData(e.target);
    projectData = {
        name: formData.get('projectName'),
        type: formData.get('projectType'),
        area: parseFloat(formData.get('projectArea')),
        area_unit: formData.get('areaUnit'),
        building_type: formData.get('buildingType'),
        building_height: parseFloat(formData.get('buildingHeight')) || null,
        floors: parseInt(formData.get('floors')),
        rooms: parseInt(formData.get('rooms')) || 1,
        bathrooms: parseInt(formData.get('bathrooms')) || 1,
        location: formData.get('projectLocation'),
        description: formData.get('projectDescription'),
        // Newly added fields for full 17-item coverage
        structure_type: formData.get('structureType') || null,
        foundation_type: formData.get('foundationType') || null,
        roof_type: formData.get('roofType') || null,
        quality_level: formData.get('qualityLevel') || null,
        finishing_type: formData.get('finishingType') || null,
        features: []
    };
    
    // Collect selected features
    document.querySelectorAll('input[name="features"]:checked').forEach(checkbox => {
        projectData.features.push(checkbox.value);
    });
    
    // Submit to backend
    submitProject();
}

// Submit project to backend
function submitProject() {
    const token = sessionStorage.getItem('authToken');
    const editingId = window.editingProjectId;
    const isEdit = !!editingId;
    const endpoint = isEdit ? `/api/projects/${editingId}` : '/api/projects';
    const method = isEdit ? 'PUT' : 'POST';

    fetch(endpoint, {
        method,
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(projectData)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(isEdit ? 'Failed to update project' : 'Failed to create project');
        }
        return response.json();
    })
    .then(data => {
        if (isEdit) {
            showNotification('Project updated successfully', 'success');
            // Re-estimate cost for the updated project
            getCostEstimation(editingId);
            // Clear editing state
            window.editingProjectId = null;
        } else {
            showNotification('Project created successfully', 'success');
            // Get cost estimation (handle ApiResponse wrapper)
            const createdId = data?.data?.project_id ?? data?.project_id;
            if (createdId) {
                getCostEstimation(createdId);
            } else {
                console.warn('Project ID not found in create response:', data);
            }
        }
        
        // Reset form
        const formEl = document.getElementById('newProjectForm');
        if (formEl) formEl.reset();
        currentStep = 1;
        if (typeof updateFormStep === 'function') updateFormStep();
        
        // Refresh projects list
        loadUserProjects();
    })
    .catch(error => {
        console.error(isEdit ? 'Error updating project:' : 'Error creating project:', error);
        showNotification(isEdit ? 'Error updating project' : 'Error creating project', 'error');
    });
}

// Get cost estimation
function getCostEstimation(projectId) {
    const token = sessionStorage.getItem('authToken');
    
    fetch(`/api/projects/${projectId}/estimate`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Failed to get estimation');
        }
        return response.json();
    })
    .then(data => {
        const estimationPayload = data?.data ?? data;
        showEstimationModal(estimationPayload);
    })
    .catch(error => {
        console.error('Error getting estimation:', error);
        showNotification('Error calculating cost estimation', 'error');
    });
}

// Show estimation modal
function showEstimationModal(estimationData) {
    const modal = document.getElementById('estimationModal');
    const modalBody = document.getElementById('estimationResult');

    // Remember project id for report download
    const pid = estimationData?.project_id || estimationData?.projectId || null;
    if (pid) lastEstimatedProjectId = pid;
    window.lastEstimationData = estimationData;
    
    modalBody.innerHTML = `
        <div class="estimation-result">
            <h3>Project Cost Estimation</h3>
            <div class="cost-breakdown">
                <div class="cost-item">
                    <span>Material Cost:</span>
                    <span>${formatCurrency(estimationData.material_cost)}</span>
                </div>
                <div class="cost-item">
                    <span>Labor Cost:</span>
                    <span>${formatCurrency(estimationData.labor_cost)}</span>
                </div>
                <div class="cost-item">
                    <span>Equipment Cost:</span>
                    <span>${formatCurrency(estimationData.equipment_cost)}</span>
                </div>
                <div class="cost-item">
                    <span>Other Costs:</span>
                    <span>${formatCurrency(estimationData.other_costs)}</span>
                </div>
                <div class="cost-item">
                    <span>Total Cost:</span>
                    <span>${formatCurrency(estimationData.total_cost)}</span>
                </div>
            </div>
            <div class="modal-actions">
                <button class="btn btn-success" onclick="saveReport()">Save Report</button>
                <button class="btn btn-secondary" onclick="closeModal('estimationModal')">Close</button>
            </div>
        </div>
    `;
    
    modal.style.display = 'block';
}

// Support HTML button to download last report
function downloadReport(projectId) {
    try {
        const pid = projectId || lastEstimatedProjectId;
        if (!pid) {
            showNotification('Select a project or run an estimate before downloading PDF.', 'warning');
            return;
        }
        const token = sessionStorage.getItem('authToken');
        fetch(`/api/projects/${pid}/report`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        })
        .then(resp => {
            if (!resp.ok) throw new Error(`Failed to download PDF: ${resp.status}`);
            const dispo = resp.headers.get('Content-Disposition') || '';
            const match = dispo.match(/filename=([^;]+)/i);
            const filename = match ? match[1].replace(/\"/g, '') : `project-report-${pid}.pdf`;
            return resp.blob().then(blob => ({ blob, filename }));
        })
        .then(({ blob, filename }) => {
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            a.remove();
            window.URL.revokeObjectURL(url);
            showNotification('PDF download started.', 'success');
        })
        .catch(err => {
            console.error('Error in downloadReport:', err);
            showNotification('Error downloading PDF report.', 'error');
        });
    } catch (e) {
        console.error('Error in downloadReport:', e);
        showNotification('Error downloading report.', 'error');
    }
}

// Generate comprehensive report (modal) combining project view and cost estimation
function generateReport(projectId) {
    try {
        const proj = projects.find(p => String(p.id) === String(projectId));
        if (!proj) {
            showNotification('Ù¾Ø±ÙˆÚ˜Ù‡ ÛŒØ§ÙØª Ù†Ø´Ø¯', 'error');
            return;
        }
        const token = sessionStorage.getItem('authToken');
        fetch(`/api/projects/${projectId}/estimate`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to get estimation');
            }
            return response.json();
        })
        .then(data => {
            const estimationPayload = data?.data ?? data;
            const pid = estimationPayload?.project_id || estimationPayload?.projectId || projectId;
            if (pid) lastEstimatedProjectId = pid;
            // Ensure Save Report has access to the latest data from this flow
            try {
                window.lastEstimationData = estimationPayload || null;
                const features = Array.isArray(proj.features) ? proj.features : (proj.extra_info && Array.isArray(proj.extra_info.features) ? proj.extra_info.features : []);
                const areaUnit = proj.area_unit || (proj.extra_info && proj.extra_info.area_unit) || 'm2';
                window.lastInputsData = {
                    project_type: proj.type,
                    location: proj.location,
                    area: proj.area,
                    area_unit: areaUnit,
                    floors: proj.floors,
                    building_height: proj.building_height || proj.height,
                    basement: proj.basement,
                    has_elevator: proj.has_elevator,
                    parking: proj.parking,
                    green_building: proj.green_building,
                    features: features
                };
            } catch (_) {}
            showReportModal(proj, estimationPayload);
        })
        .catch(error => {
            console.error('Error generating report:', error);
            try { window.lastEstimationData = null; } catch(_) {}
            showNotification('Ø®Ø·Ø§ Ø¯Ø± Ø¯Ø±ÛŒØ§ÙØª Ø¨Ø±Ø¢ÙˆØ±Ø¯ Ù‡Ø²ÛŒÙ†Ù‡. Ú¯Ø²Ø§Ø±Ø´ ØªÙ†Ù‡Ø§ Ø´Ø§Ù…Ù„ Ø§Ø·Ù„Ø§Ø¹Ø§Øª Ù¾Ø±ÙˆÚ˜Ù‡ Ù†Ù…Ø§ÛŒØ´ Ø¯Ø§Ø¯Ù‡ Ù…ÛŒâ€ŒØ´ÙˆØ¯.', 'warning');
            showReportModal(proj, null);
        });
    } catch (e) {
        console.error('Error in generateReport:', e);
        showNotification('Ø®Ø·Ø§ Ø¯Ø± ØªÙˆÙ„ÛŒØ¯ Ú¯Ø²Ø§Ø±Ø´', 'error');
    }
}



// Load user projects
function loadUserProjects() {
    const token = sessionStorage.getItem('authToken');
    
    fetch('/api/projects', {
        method: 'GET',
        headers: {
            'Authorization': `Bearer ${token}`
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Failed to load projects');
        }
        return response.json();
    })
    .then(data => {
        const list = data?.data?.projects ?? data?.projects ?? [];
        projects = Array.isArray(list) ? list : [];
        projectsLoaded = true;
        displayProjects(projects);
        updateStats();
        if (currentSection === 'overview') {
            loadRecentProjects();
        }
    })
    .catch(error => {
        console.error('Error loading projects:', error);
        showNotification('Error loading projects', 'error');
    });
}

// Display projects
function displayProjects(projectsList) {
    const container = document.getElementById('projectsGrid');
    
    if (projectsList.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-folder-open"></i>
                <p>You haven't created any projects yet</p>
                <button class="btn btn-primary" onclick="showSection('new-project')">
                    Create New Project
                </button>
            </div>
        `;
        return;
    }
    
    container.innerHTML = projectsList.map(project => `
        <div class="project-card">
            <div class="project-header">
                <div>
                    <div class="project-title">${project.title || project.name || 'Untitled Project'}</div>
                    <div class="project-type">${getProjectTypeLabel(project.type)}</div>
                </div>
                ${project.status ? `<span class="project-status status-${project.status}">${getStatusLabel(project.status)}</span>` : ''}
            </div>
            <div class="project-details">
                <div class="project-detail">
                    <span>Area:</span>
                    <span>${project.area} ${getAreaUnitLabel(project.area_unit || (project.extra_info && project.extra_info.area_unit) || 'm2')}</span>
                </div>
                <div class="project-detail">
                    <span>Number of Floors:</span>
                    <span>${project.floors}</span>
                </div>
                <div class="project-detail">
                    <span>Location:</span>
                    <span>${project.location}</span>
                </div>
                <div class="project-detail">
                    <span>Created Date:</span>
                    <span>${formatDate(project.created_at)}</span>
                </div>
            </div>
            <div class="project-actions">
                <button class="btn btn-small btn-primary" onclick="viewProject('${project.id}')">
                    View
                </button>
                <button class="btn btn-small btn-primary" onclick="getCostEstimation('${project.id}')">
                    Cost Estimate
                </button>
                <button class="btn btn-small btn-primary" onclick="generateReport('${project.id}')">
                    Report
                </button>

                <button class="btn btn-small btn-primary" onclick="updateProject('${project.id}')">
                    Update
                </button>
                <button class="btn btn-small btn-danger" onclick="confirmDeleteProject('${project.id}')">
                    Delete
                </button>
            </div>
        </div>
    `).join('');
}

// View project in a new read-only page
function viewProject(projectId) {
    try {
        const proj = projects.find(p => String(p.id) === String(projectId));
        if (!proj) {
            showNotification('Project not found', 'error');
            return;
        }
        const modal = document.getElementById('projectViewModal');
        const content = document.getElementById('projectViewContent');
        if (!modal || !content) {
            showNotification('Unable to open project view', 'error');
            return;
        }
        content.innerHTML = `
            <div class="project-view">
                <div class="project-header">
                    <h3>${proj.title || proj.name || 'Untitled Project'}</h3>
                    ${proj.status ? `<span class="project-status status-${proj.status}">${getStatusLabel(proj.status)}</span>` : ''}
                </div>

                <div class="kv-group">
                    <div class="cost-item"><span>Type</span><span>${getProjectTypeLabel(proj.type)}</span></div>
                    <div class="cost-item"><span>Location</span><span>${proj.location || '-'}</span></div>
                    <div class="cost-item"><span>Area</span><span>${proj.area ?? '-'} ${getAreaUnitLabel(proj.area_unit || (proj.extra_info && proj.extra_info.area_unit) || 'm2')}</span></div>
                    <div class="cost-item"><span>Floors</span><span>${proj.floors ?? '-'}</span></div>
                    <div class="cost-item"><span>Rooms</span><span>${proj.rooms ?? '-'}</span></div>
                    <div class="cost-item"><span>Bathrooms</span><span>${proj.bathrooms ?? '-'}</span></div>
                    <div class="cost-item"><span>Building Height</span><span>${(proj.building_height ?? (proj.extra_info && proj.extra_info.building_height)) ?? '-'}</span></div>
                    <div class="cost-item"><span>Estimated Cost</span><span>${proj.estimated_cost !== undefined ? formatCurrency(proj.estimated_cost) : '-'}</span></div>
                    <div class="cost-item"><span>Created</span><span>${formatDate(proj.created_at)}</span></div>
                    <div class="cost-item"><span>Updated</span><span>${proj.updated_at ? formatDate(proj.updated_at) : '-'}</span></div>
                    <div class="cost-item"><span>Project ID</span><span>${proj.id}</span></div>
                </div>

                <h4>Specifications</h4>
                <div class="kv-group">
                    <div class="cost-item"><span>Building Type</span><span>${proj.building_type || proj.structure_type || '-'}</span></div>
                    <div class="cost-item"><span>Structure Type</span><span>${proj.structure_type || '-'}</span></div>
                    <div class="cost-item"><span>Foundation Type</span><span>${proj.foundation_type || '-'}</span></div>
                    <div class="cost-item"><span>Roof Type</span><span>${proj.roof_type || '-'}</span></div>
                    <div class="cost-item"><span>Quality Level</span><span>${proj.quality_level || '-'}</span></div>
                    <div class="cost-item"><span>Finishing Type</span><span>${proj.finishing_type || '-'}</span></div>
                </div>

                <div class="kv-group">
                    <div class="cost-item">
                        <span>Features</span>
                        <span>${(() => { const features = Array.isArray(proj.features) ? proj.features : (proj.extra_info && Array.isArray(proj.extra_info.features) ? proj.extra_info.features : []); return (features && features.length > 0) ? features.map(f => `<span class=\"feature-chip\">${f}</span>`).join(' ') : '-' })()}</span>
                    </div>
                    <div class="cost-item">
                        <span>Description</span>
                        <span>${proj.description || '-'}</span>
                    </div>
                </div>

                ${(() => { const extra = (proj.extra_info && typeof proj.extra_info === 'object') ? proj.extra_info : null; if (!extra) return ''; const extraRows = Object.entries(extra).filter(([k, v]) => v !== undefined && v !== null && k !== 'features' && k !== 'area_unit').map(([k, v]) => `<div class=\"cost-item\"><span>${k}</span><span>${Array.isArray(v) ? v.join(', ') : v}</span></div>`).join(''); return extraRows ? `<h4>Additional Info</h4><div class=\"kv-group\">${extraRows}</div>` : ''; })()}

                <div class="project-actions">
                    <button class="btn btn-primary" onclick="getCostEstimation('${proj.id}')">Cost Estimate</button>
                    <button class="btn btn-secondary" onclick="closeModal('projectViewModal')">Close</button>
                </div>
            </div>
        `;
        modal.style.display = 'block';
    } catch (error) {
        console.error('Error in viewProject:', error);
        showNotification('An error occurred while displaying the project', 'error');
    }
}

// Update project: open form and prefill fields for editing (UI only)
function updateProject(projectId) {
    try {
        const proj = projects.find(p => String(p.id) === String(projectId));
        if (!proj) {
            showNotification('Project not found', 'error');
            return;
        }
        // Navigate to the New Project form section
        if (typeof showSection === 'function') {
            showSection('new-project');
        }
        // Mark editing mode
        window.editingProjectId = projectId;
        // Reset to step 1 and update UI
        if (typeof updateFormStep === 'function') {
            currentStep = 1;
            updateFormStep();
        }
        // Prefill form fields with null-safe guards
        const setValue = (id, val) => {
            const el = document.getElementById(id);
            if (el && val !== undefined && val !== null) {
                el.value = val;
            }
        };
        setValue('projectName', proj.title || proj.name || '');
        setValue('projectType', proj.type || '');
        setValue('projectLocation', proj.location || '');
        const unit = proj.area_unit || (proj.extra_info && proj.extra_info.area_unit) || 'm2';
        setValue('areaUnit', unit);
        if (typeof updateAreaLabel === 'function') { updateAreaLabel(); }
        setValue('projectArea', proj.area || '');
        setValue('buildingType', proj.building_type || proj.structure_type || '');
        setValue('projectDescription', proj.description || '');
        setValue('floors', (proj.floors !== undefined ? proj.floors : 1));
        setValue('rooms', (proj.rooms !== undefined ? proj.rooms : 1));
        setValue('bathrooms', (proj.bathrooms !== undefined ? proj.bathrooms : 1));
        const height = (proj.building_height !== undefined && proj.building_height !== null)
            ? proj.building_height
            : (proj.extra_info && proj.extra_info.building_height);
        setValue('buildingHeight', height || '');
        setValue('foundationType', proj.foundation_type || '');
        setValue('structureType', proj.structure_type || '');
        setValue('roofType', proj.roof_type || '');
        setValue('qualityLevel', proj.quality_level || '');
        setValue('finishingType', proj.finishing_type || '');
        // Features checkboxes
        const features = Array.isArray(proj.features)
            ? proj.features
            : (proj.extra_info && Array.isArray(proj.extra_info.features) ? proj.extra_info.features : []);
        document.querySelectorAll('input[name="features"]').forEach(cb => {
            cb.checked = features.includes(cb.value);
        });
        // Inform user
        showNotification('Project form is prefilled with current data. You can make changes.', 'info');
    } catch (err) {
        console.error('Error in updateProject:', err);
        showNotification('Error preparing edit form', 'error');
    }
}

// Load recent projects for overview
function loadRecentProjects() {
    const recentProjects = projects.slice(0, 5);
    const container = document.getElementById('recentProjectsList');
    
    if (recentProjects.length === 0) {
        container.innerHTML = '<p>No projects found</p>';
        return;
    }
    
    container.innerHTML = recentProjects.map(project => `
        <div class="project-card">
            <div class="project-header">
                <div>
                    <div class="project-title">${project.title || project.name || 'Untitled Project'}</div>
                    <div class="project-type">${getProjectTypeLabel(project.type)}</div>
                </div>
                ${project.status ? `<span class="project-status status-${project.status}">${getStatusLabel(project.status)}</span>` : ''}
            </div>
            <div class="project-actions">
                <button class="btn btn-small btn-primary" onclick="viewProject('${project.id}')">View</button>
                <button class="btn btn-small btn-primary" onclick="getCostEstimation('${project.id}')">Cost Estimate</button>
                <button class="btn btn-small btn-primary" onclick="generateReport('${project.id}')">Report</button>
                <button class="btn btn-small btn-primary" onclick="updateProject('${project.id}')">Update</button>
                <button class="btn btn-small btn-danger" onclick="confirmDeleteProject('${project.id}')">Delete</button>
            </div>
        </div>
    `).join('');
}

// Update dashboard statistics
function updateStats() {
    const totalProjects = projects.length;
    const totalCost = projects.reduce((sum, p) => sum + (p.estimated_cost || 0), 0);
    
    const totalProjectsEl = document.getElementById('totalProjects');
    const totalEstimationEl = document.getElementById('totalEstimation');

    if (totalProjectsEl) totalProjectsEl.textContent = totalProjects;
    if (totalEstimationEl) totalEstimationEl.textContent = formatCurrency(totalCost);
}

// Update user info
function updateUserInfo() {
    if (currentUser) {
        const userWelcome = document.getElementById('userWelcome');
        if (userWelcome) {
            userWelcome.textContent = `Hello ${currentUser.username}`;
        }
        
        // Update profile section if exists
        const profileUsername = document.getElementById('profileUsername');
        if (profileUsername) {
            profileUsername.textContent = currentUser.username;
        }
    }
}

// Load profile data
function loadProfile() {
    if (currentUser) {
        const profileUsername = document.getElementById('profileUsername');
        const profileEmail = document.getElementById('profileEmail');
        
        if (profileUsername) {
            profileUsername.textContent = currentUser.username || 'Username';
        }
        if (profileEmail) {
            profileEmail.textContent = currentUser.email || 'Email not available';
        }
    }
}

// Load reports data
let savedReports = [];
function loadReports() {
    const container = document.getElementById('reportsList');
    if (!container) return;
    const token = sessionStorage.getItem('authToken');

    fetch('/api/reports', {
        headers: { 'Authorization': `Bearer ${token}` }
    })
    .then(res => res.json())
    .then(data => {
        const list = data?.data?.reports ?? data?.reports ?? null;
        if (Array.isArray(list)) {
            savedReports = list;
            try { sessionStorage.setItem('savedReports', JSON.stringify(savedReports)); } catch (_) {}
            renderReportsList(savedReports);
        } else {
            const fromSession = sessionStorage.getItem('savedReports');
            savedReports = fromSession ? JSON.parse(fromSession) : [];
            renderReportsList(savedReports);
        }
    })
    .catch(err => {
        console.warn('loadReports fallback:', err);
        const fromSession = sessionStorage.getItem('savedReports');
        savedReports = fromSession ? JSON.parse(fromSession) : [];
        renderReportsList(savedReports);
    });
}

function renderReportsList(list) {
    const container = document.getElementById('reportsList');
    if (!container) return;
    if (!list || list.length === 0) {
        container.innerHTML = '<p>No reports found</p>';
        return;
    }
    container.innerHTML = list.map(r => `
        <div class="project-card">
            <div class="project-header">
                <div>
                    <div class="project-title">${r.title || 'Untitled Report'}</div>
                    <div class="project-type">Project #${r.project_id}</div>
                </div>
                ${r.created_at ? `<span class="project-status">${formatDate(r.created_at)}</span>` : ''}
            </div>
            <div class="project-details">
                <div class="project-detail"><span>Total Cost:</span><span>${r.total_cost !== undefined ? formatCurrency(r.total_cost) : '-'}</span></div>
                ${r.notes ? `<div class="project-detail"><span>Notes:</span><span>${r.notes}</span></div>` : ''}
            </div>
            <div class="project-actions">
                <button class="btn btn-small" onclick="showSavedReport('${r.id || r.report_id}')">Show Report</button>
                <button class="btn btn-small btn-danger" onclick="deleteReport('${r.id || r.report_id}')">Delete</button>
                <button class="btn btn-small btn-primary" onclick="downloadReport('${r.project_id}')">Download PDF</button>
            </div>
        </div>
    `).join('');
}

function confirmDeleteProject(projectId) {
    const confirmed = window.confirm('Are you sure you want to delete this project?');
    if (!confirmed) return;

    const token = sessionStorage.getItem('authToken');
    fetch(`/api/projects/${projectId}`, {
        method: 'DELETE',
        headers: {
            'Authorization': `Bearer ${token}`
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Ù¾Ø±ÙˆÚ˜Ù‡ Ø¨Ø§ Ù…ÙˆÙÙ‚ÛŒØª Ø­Ø°Ù Ø´Ø¯', 'success');
            loadUserProjects();
            if (currentSection === 'overview') {
                loadRecentProjects();
            }
        } else {
            showNotification(data.message || 'Ø®Ø·Ø§ Ø¯Ø± Ø­Ø°Ù Ù¾Ø±ÙˆÚ˜Ù‡', 'error');
        }
    })
    .catch(err => {
        console.error('Delete error:', err);
        showNotification('Ø®Ø·Ø§ Ø¯Ø± Ø­Ø°Ù Ù¾Ø±ÙˆÚ˜Ù‡', 'error');
    });
}

// Utility functions
function getProjectTypeLabel(type) {
    const labels = {
        'residential': 'Residential',
        'commercial': 'Commercial',
        'industrial': 'Industrial',
        'infrastructure': 'Infrastructure'
    };
    return labels[type] || type;
}

function getStatusLabel(status) {
    const labels = {
        'draft': 'Draft',
        'active': 'Active',
        'completed': 'Completed',
        'cancelled': 'Cancelled'
    };
    return labels[status] || status;
}

function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 0
    }).format(amount);
}

function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString();
}

// Update area label based on selected unit
function updateAreaLabel() {
    const areaUnit = document.getElementById('areaUnit').value;
    const areaLabel = document.getElementById('areaLabel');
    const heightLabel = document.querySelector('label[for="buildingHeight"]');
    
    if (areaUnit === 'sqft') {
        areaLabel.textContent = 'Area (square feet):';
        if (heightLabel) {
            heightLabel.textContent = 'Building Height (feet):';
        }
    } else {
        areaLabel.textContent = 'Area (square meters):';
        if (heightLabel) {
            heightLabel.textContent = 'Building Height (meters):';
        }
    }
}

// Modal functions
function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}

// Notification system
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <span>${message}</span>
        <button onclick="this.parentElement.remove()">&times;</button>
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 5000);
}

// Logout function
function logout() {
    sessionStorage.removeItem('authToken');
    sessionStorage.removeItem('currentUser');
    window.location.href = '/index.html';
}

// Toggle sidebar for mobile
function toggleSidebar() {
    document.querySelector('.sidebar').classList.toggle('active');
}

// Close sidebar when clicking outside
document.addEventListener('click', function(e) {
    const sidebar = document.querySelector('.sidebar');
    const menuToggle = document.getElementById('menuToggle');
    
    if (window.innerWidth <= 1024 && 
        !sidebar.contains(e.target) && 
        !menuToggle.contains(e.target)) {
        sidebar.classList.remove('active');
    }
});

// Handle window resize
window.addEventListener('resize', function() {
    if (window.innerWidth > 1024) {
        document.querySelector('.sidebar').classList.remove('active');
    }
});


function getAreaUnitLabel(unit) {
    const u = String(unit || '').toLowerCase();
    const labels = {
        'm2': 'square meters',
        'mÂ²': 'square meters',
        'sqm': 'square meters',
        'square_meters': 'square meters',
        'sqft': 'square feet',
        'ft2': 'square feet',
        'ftÂ²': 'square feet',
        'square_feet': 'square feet'
    };
    return labels[u] || unit || 'square meters';
}


function showReportModal(project, estimationData) {
    try {
        const modal = document.getElementById('reportModal');
        const content = document.getElementById('reportContent');
        if (!modal || !content) {
            showNotification('Report modal not found', 'error');
            return;
        }

        const areaUnit = (project.area_unit || (project.extra_info && project.extra_info.area_unit) || 'm2');
        const features = Array.isArray(project.features)
            ? project.features
            : (project.extra_info && Array.isArray(project.extra_info.features) ? project.extra_info.features : []);

        const overviewHtml = `
            <div class="project-header">
                <h3>${project.title || project.name || 'Untitled Project'}</h3>
                ${project.status ? `<span class="project-status status-${project.status}">${getStatusLabel(project.status)}</span>` : ''}
            </div>
            <div class="kv-group">
                <div class="cost-item"><span>Type</span><span>${getProjectTypeLabel(project.type)}</span></div>
                <div class="cost-item"><span>Location</span><span>${project.location || '-'}</span></div>
                <div class="cost-item"><span>Area</span><span>${project.area ?? '-'} ${getAreaUnitLabel(areaUnit)}</span></div>
                <div class="cost-item"><span>Floors</span><span>${project.floors ?? '-'}</span></div>
                ${project.building_height ? `<div class="cost-item"><span>Height</span><span>${project.building_height}</span></div>` : ''}
                ${project.basement !== undefined ? `<div class="cost-item"><span>Basement</span><span>${project.basement ? 'Yes' : 'No'}</span></div>` : ''}
                ${project.has_elevator !== undefined ? `<div class="cost-item"><span>Elevator</span><span>${project.has_elevator ? 'Yes' : 'No'}</span></div>` : ''}
                ${project.parking !== undefined ? `<div class="cost-item"><span>Parking</span><span>${project.parking ? 'Yes' : 'No'}</span></div>` : ''}
                ${project.green_building !== undefined ? `<div class="cost-item"><span>Green Building</span><span>${project.green_building ? 'Yes' : 'No'}</span></div>` : ''}
                ${project.created_at ? `<div class="cost-item"><span>Created</span><span>${formatDate(project.created_at)}</span></div>` : ''}
            </div>
            ${features && features.length ? `
            <div class="feature-chip-group">
                ${features.map(f => `<span class="feature-chip">${f}</span>`).join('')}
            </div>` : ''}
        `;

        const estimationHtml = estimationData ? `
            <div class="estimation-result">
                <h3>Project Cost Estimation</h3>
                <div class="cost-breakdown">
                    <div class="cost-item"><span>Material Cost</span><span>${formatCurrency(estimationData.material_cost)}</span></div>
                    <div class="cost-item"><span>Labor Cost</span><span>${formatCurrency(estimationData.labor_cost)}</span></div>
                    <div class="cost-item"><span>Equipment Cost</span><span>${formatCurrency(estimationData.equipment_cost)}</span></div>
                    <div class="cost-item"><span>Other Costs</span><span>${formatCurrency(estimationData.other_costs)}</span></div>
                    <div class="cost-item total"><span>Total Cost</span><span>${formatCurrency(estimationData.total_cost)}</span></div>
                </div>
            </div>
        ` : `
            <div class="estimation-result">
                <h3>Cost Estimation</h3>
                <p>No estimation data available for this project.</p>
                <div class="modal-actions">
                    <button class="btn btn-primary" onclick="getCostEstimation('${project.id}')">Run Cost Estimate</button>
                </div>
            </div>
        `;

        content.innerHTML = `
            <div class="project-report">
                <div class="report-columns">
                    <div class="report-left">
                        ${overviewHtml}
                    </div>
                    <div class="report-right">
                        ${estimationHtml}
                    </div>
                </div>
                <div class="modal-actions">
                    <button class="btn btn-success" onclick="saveReport('${project.id}')">Save Report</button>
                    <button class="btn btn-secondary" onclick="closeModal('reportModal')">Close</button>
                </div>
            </div>
        `;

        modal.style.display = 'block';
    } catch (err) {
        console.error('Error in showReportModal:', err);
        showNotification('An error occurred while displaying the report', 'error');
    }
}

function saveReport(projectId) {
    try {
        const pid = projectId || lastEstimatedProjectId;
        if (!pid) {
            showNotification('No project selected to save report', 'error');
            return;
        }
        const token = sessionStorage.getItem('authToken');
        // Require non-empty report title; retry if empty; cancel aborts
        let title = null;
        while (true) {
            const input = window.prompt('Enter a report title:');
            if (input === null) return; // user cancelled
            const t = String(input).trim();
            if (t.length > 0) { title = t; break; }
            alert('Report title cannot be empty.');
        }
        const notes = null; // no second prompt; keep flow simple
        const estimationData = window.lastEstimationData || null;
        const adviceData = window.lastAdviceData || null;
        const inputsData = window.lastInputsData || null;
        const materialsData = window.lastMaterialsData || null;

        const body = {
            title,
            notes,
            format: 'pdf',
            inputs_json: inputsData,
            materials_json: materialsData,
            estimation_json: estimationData,
            advice_json: adviceData
        };

        fetch(`/api/projects/${pid}/reports`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(body)
        })
        .then(res => res.json())
        .then(data => {
            if (!data.success) throw new Error(data.message || 'Failed to save report');
            showNotification('Report saved successfully', 'success');
            try { closeModal('estimationModal'); } catch (_) {}
            try { closeModal('reportModal'); } catch (_) {}
            try { loadReports(); } catch (_) {}
        })
        .catch(err => {
            console.error('Save report error:', err);
            showNotification(`Save report failed: ${err.message}`, 'error');
        });
    } catch (err) {
        console.error('Save report exception:', err);
        showNotification('Unexpected error saving report', 'error');
    }
}

function showSavedReport(reportId) {
  try {
    if (!reportId) { showNotification('Invalid report id', 'error'); return; }
    const token = sessionStorage.getItem('authToken');

    const modal = document.getElementById('reportModal');
    const container = document.getElementById('reportContent');
    if (!modal || !container) {
      console.warn('reportModal/reportContent not found in DOM');
      return;
    }
    container.innerHTML = '<div class="loading">Loading report...</div>';
    modal.style.display = 'block';

    fetch(`/api/reports/${reportId}`, { headers: { 'Authorization': `Bearer ${token}` } })
      .then(res => res.json())
      .then(data => {
        if (!data.success) throw new Error(data.message || 'Failed to fetch report');
        const r = (data.data && (data.data.report || data.data)) || data.report || data;
        const inputs = r.inputs_json || r.inputs || {};
        const estimation = r.estimation_json || r.estimation || null;

        // Prefer canonical project snapshot from backend to avoid mismatches
        return fetch('/api/projects', { headers: { 'Authorization': `Bearer ${token}` } })
          .then(pr => pr.json())
          .then(pl => {
            const list = pl?.data?.projects ?? pl?.projects ?? [];
            const proj = Array.isArray(list) ? list.find(p => String(p.id) === String(r.project_id)) : null;
            if (proj) {
              showReportModal(proj, estimation);
              return;
            }

            // Fallback: reconstruct minimal project from saved inputs
            const features = Array.isArray(inputs.features) ? inputs.features : [];
            const projectObj = {
              id: r.project_id,
              title: r.title || r.name || `Report #${r.id || r.report_id || reportId}`,
              name: r.title || r.name,
              type: inputs.project_type || inputs.type || r.type || 'residential',
              location: inputs.location || r.location || '-',
              area: (r.area !== undefined ? r.area : inputs.area),
              area_unit: r.area_unit || inputs.area_unit || 'm2',
              floors: inputs.floors,
              height: inputs.building_height || inputs.height,
              basement: inputs.basement,
              has_elevator: (inputs.has_elevator !== undefined ? inputs.has_elevator : inputs.elevator),
              parking: inputs.parking,
              green_building: inputs.green_building,
              created_at: r.created_at,
              features: features,
              extra_info: {
                area_unit: r.area_unit || inputs.area_unit || 'm2',
                features: features
              }
            };
            showReportModal(projectObj, estimation);
          });
      })
      .catch(err => {
        console.error('Show saved report error:', err);
        showNotification(`Failed to load report: ${err.message}`, 'error');
        try { closeModal('reportModal'); } catch (_) {}
      });
  } catch (err) {
    console.error('Show saved report exception:', err);
    showNotification('Unexpected error loading report', 'error');
  }
}
function deleteReport(reportId) {
  try {
    if (!reportId) { showNotification('Invalid report id', 'error'); return; }
    if (!window.confirm('Delete this report permanently?')) return;
    const token = sessionStorage.getItem('authToken');
    fetch(`/api/reports/${reportId}`, {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${token}` }
    })
    .then(res => res.json())
    .then(data => {
      if (!data.success) throw new Error(data.message || 'Failed to delete report');
      showNotification('Report deleted', 'success');
      try { loadReports(); } catch (_) {}
    })
    .catch(err => {
      console.error('Delete report error:', err);
      showNotification(`Delete failed: ${err.message}`, 'error');
    });
  } catch (err) {
    console.error('Delete report exception:', err);
  }
}