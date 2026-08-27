// script.js - Frontend JavaScript with Step Tracking and Abort

let currentExecutionId = null;

// Set default quote start date to today
document.addEventListener('DOMContentLoaded', function() {
    const today = new Date();
    const dateStr = today.toISOString().split('T')[0];
    document.getElementById('quote_start_date').value = dateStr;
});

// Toggle custom instance field when 'other' is selected
document.getElementById('instance_url').addEventListener('change', function() {
    const customInstanceField = document.getElementById('customInstanceField');
    if (this.value === 'other') {
        customInstanceField.style.display = 'block';
    } else {
        customInstanceField.style.display = 'none';
        document.getElementById('custom_instance_name').value = '';
    }
});

// Toggle conditional fields based on checkboxes
document.getElementById('create_account').addEventListener('change', function() {
    const accountFields = document.getElementById('accountFields');
    const existingAccountField = document.getElementById('existingAccountField');
    if (this.checked) {
        // Create new account - show creation fields, hide existing ID field
        accountFields.style.display = 'block';
        existingAccountField.style.display = 'none';
        document.getElementById('account_id').value = '';
        document.getElementById('account_id').disabled = true;
    } else {
        // Use existing account - hide creation fields, show existing ID field
        accountFields.style.display = 'none';
        existingAccountField.style.display = 'block';
        document.getElementById('account_id').disabled = false;
    }
});

document.getElementById('create_opportunity').addEventListener('change', function() {
    const opportunityFields = document.getElementById('opportunityFields');
    const existingOpportunityField = document.getElementById('existingOpportunityField');
    if (this.checked) {
        // Create new opportunity - show creation fields, hide existing ID field
        opportunityFields.style.display = 'block';
        existingOpportunityField.style.display = 'none';
        document.getElementById('opportunity_id').value = '';
        document.getElementById('opportunity_id').disabled = true;
    } else {
        // Use existing opportunity - hide creation fields, show existing ID field
        opportunityFields.style.display = 'none';
        existingOpportunityField.style.display = 'block';
        document.getElementById('opportunity_id').disabled = false;
    }
});

document.getElementById('create_quote').addEventListener('change', function() {
    const quoteFields = document.getElementById('quoteFields');
    const existingQuoteField = document.getElementById('existingQuoteField');
    if (this.checked) {
        // Create new quote - show creation fields, hide existing ID field
        quoteFields.style.display = 'block';
        existingQuoteField.style.display = 'none';
        document.getElementById('quote_id').value = '';
        document.getElementById('quote_id').disabled = true;
    } else {
        // Use existing quote - hide creation fields, show existing ID field
        quoteFields.style.display = 'none';
        existingQuoteField.style.display = 'block';
        document.getElementById('quote_id').disabled = false;
    }
});

document.getElementById('add_products').addEventListener('change', function() {
    const productFields = document.getElementById('productFields');
    productFields.style.display = this.checked ? 'block' : 'none';
});

// Toggle ramp-related fields
document.getElementById('ramp').addEventListener('change', function() {
    const escPercentField = document.getElementById('escPercentField');
    const businessTypeField = document.getElementById('businessTypeField');
    if (this.value === 'Yes') {
        escPercentField.style.display = 'block';
        businessTypeField.style.display = 'block';
    } else {
        escPercentField.style.display = 'none';
        businessTypeField.style.display = 'none';
    }
});

// Toggle custom currency field when 'Other' is selected
document.getElementById('currency').addEventListener('change', function() {
    const customCurrencyField = document.getElementById('customCurrencyField');
    if (this.value === 'Other') {
        customCurrencyField.style.display = 'block';
    } else {
        customCurrencyField.style.display = 'none';
        document.getElementById('custom_currency').value = '';
    }
});

// Abort button handler
document.getElementById('abortBtn').addEventListener('click', async function() {
    if (!currentExecutionId) return;
    
    if (confirm('Are you sure you want to abort the current process?')) {
        try {
            const response = await fetch(`/api/abort/${currentExecutionId}`, {
                method: 'POST'
            });
            const result = await response.json();
            
            if (result.success) {
                document.getElementById('abortBtn').disabled = true;
                document.getElementById('abortBtn').textContent = 'Aborting...';
            }
        } catch (error) {
            console.error('Error aborting:', error);
        }
    }
});

// Form submission
document.getElementById('automationForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const submitBtn = document.getElementById('submitBtn');
    const abortBtn = document.getElementById('abortBtn');
    const overallStatus = document.getElementById('overallStatus');
    const currentStepSection = document.getElementById('currentStepSection');
    const stepsList = document.getElementById('stepsList');
    const logsDiv = document.getElementById('logs');
    const resultsSection = document.getElementById('resultsSection');
    
    // Gather form data first for validation
    const formData = new FormData(this);
    const data = {};
    
    // Convert FormData to object
    for (let [key, value] of formData.entries()) {
        if (value === 'on') {
            data[key] = true;
        } else if (value === '') {
            data[key] = null;
        } else {
            data[key] = value;
        }
    }
    
    // Add unchecked checkboxes as false
    const checkboxes = this.querySelectorAll('input[type="checkbox"]');
    checkboxes.forEach(checkbox => {
        if (!data[checkbox.name]) {
            data[checkbox.name] = false;
        }
    });

    // Inject common session fields (outside the form)
    data.instance_url = document.getElementById('instance_url').value;
    data.custom_instance_name = document.getElementById('custom_instance_name').value;
    data.api_version = document.getElementById('api_version').value;
    
    // === VALIDATION CHECKS ===
    const errors = [];
    
    // Check if instance is selected
    if (!data.instance_url || data.instance_url.trim() === '') {
        errors.push('Instance selection is required');
    }
    
    // Check if 'other' is selected, then custom instance name must be provided
    if (data.instance_url === 'other' && (!data.custom_instance_name || data.custom_instance_name.trim() === '')) {
        errors.push('Custom Instance Name is required when "other" is selected');
    }
    
    // Check if ramp is Yes, then ESC percent and business type must be provided
    if (data.ramp === 'Yes') {
        if (!data.esc_percent || data.esc_percent.trim() === '') {
            errors.push('ESC Percent is required when Ramp is set to Yes');
        }
        if (!data.business_type || data.business_type.trim() === '') {
            errors.push('Business Type is required when Ramp is set to Yes');
        }
    }
    
    if (data.create_opportunity && !data.create_account && (!data.account_id || data.account_id.trim() === '')) {
        errors.push('Account ID is required to create an opportunity');
    }
    
    if (data.create_quote && !data.create_opportunity && (!data.opportunity_id || data.opportunity_id.trim() === '')) {
        errors.push('Opportunity ID is required to create a quote');
    }
    
    // Check if quote creation is not selected, then quote ID is required
    if (!data.create_quote && (data.add_products || data.oara || data.submit_approval || data.validate_quote || data.quote_to_accepted || data.oara_needed) && (!data.quote_id || data.quote_id.trim() === '')) {
        errors.push('Quote ID is required when not creating a new quote');
    }
    
    // Check if add products is selected, then products must be provided
    if (data.add_products && (!data.products || data.products.trim() === '')) {
        errors.push('Products are required when Add Products is selected');
    }
    // Check if add products is selected, then products must be provided
    if (data.oara) {
        if (!data.opportunity_id || data.opportunity_id.trim() === '') {
            errors.push('Opportunity ID is required when OARA is checked');
        }
        if (!data.quote_id || data.quote_id.trim() === '') {
            errors.push('Quote ID is required when OARA is checked');
        }
    }
    
    // Check if add products is selected, then products must be provided
    if (data.add_products && (!data.products || data.products.trim() === '')) {
        errors.push('Products are required when Add Products is selected');
    }
    
    // If there are validation errors, show them and stop
    if (errors.length > 0) {
        alert('Please fix the following errors:\n\n' + errors.join('\n'));
        return;
    }
    
    // Disable submit button, enable abort button
    submitBtn.disabled = true;
    submitBtn.textContent = 'Running...';
    abortBtn.style.display = 'inline-block';
    abortBtn.disabled = false;
    abortBtn.textContent = 'Abort Process';
    
    // Clear previous data
    stepsList.innerHTML = '';
    logsDiv.innerHTML = '';
    resultsSection.style.display = 'none';
    
    // Show overall status as running (will be updated from server)
    overallStatus.textContent = 'Starting...';
    overallStatus.className = 'overall-status running';
    console.log('Form Data Submitted:', data);
    
    try {
        // Start automation
        const response = await fetch('/api/run', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (!result.success) {
            throw new Error(result.error || 'Unknown error occurred');
        }
        
        currentExecutionId = result.execution_id;
        
        // Poll for status
        pollStatus(currentExecutionId);
        
    } catch (error) {
        overallStatus.textContent = 'error';
        overallStatus.className = 'overall-status error';
        currentStepSection.style.display = 'none';
        
        // Show detailed error information
        let errorHTML = `<div class="log-entry error"><strong>Error:</strong> ${escapeHtml(error.message)}</div>`;
        
        // If there's a response with error details, show them
        if (result && result.error_details) {
            errorHTML += `<div class="log-entry error"><strong>Details:</strong><pre>${escapeHtml(result.error_details)}</pre></div>`;
        }
        
        logsDiv.innerHTML = errorHTML;
        submitBtn.disabled = false;
        submitBtn.textContent = 'Run Automation';
        abortBtn.style.display = 'none';
    }
});

async function pollStatus(executionId) {
    const overallStatus = document.getElementById('overallStatus');
    const currentStepSection = document.getElementById('currentStepSection');
    const currentStep = document.getElementById('currentStep');
    const stepsList = document.getElementById('stepsList');
    const logsDiv = document.getElementById('logs');
    const resultsSection = document.getElementById('resultsSection');
    const resultsDiv = document.getElementById('results');
    const submitBtn = document.getElementById('submitBtn');
    const abortBtn = document.getElementById('abortBtn');
    
    const pollInterval = setInterval(async () => {
        try {
            const response = await fetch(`/api/status/${executionId}`);
            const result = await response.json();
            
            if (!result.success) {
                throw new Error('Failed to get status');
            }
            
            const data = result.data;
            
            // Update overall status from server
            if (data.status) {
                overallStatus.textContent = data.status;
                overallStatus.className = 'overall-status ' + data.status;
            }
            
            // Update current step
            if (data.current_step) {
                currentStepSection.style.display = 'block';
                const stepText = currentStep.querySelector('.step-text');
                if (stepText) {
                    stepText.textContent = data.current_step;
                }
            } else {
                currentStepSection.style.display = 'none';
            }
            
            // Update steps list
            if (data.steps && data.steps.length > 0) {
                updateStepsList(data.steps);
            }
            
            // Update logs
            if (data.logs && data.logs.length > 0) {
                updateLogs(data.logs);
            }
            
            // Check status
            if (data.status === 'completed') {
                clearInterval(pollInterval);
                
                currentStepSection.style.display = 'none';
                
                // Show results
                if (data.results) {
                    showResults(data.results);
                }
                
                submitBtn.disabled = false;
                submitBtn.textContent = 'Run Automation';
                abortBtn.style.display = 'none';
                currentExecutionId = null;
                
            } else if (data.status === 'error') {
                clearInterval(pollInterval);
                
                currentStepSection.style.display = 'none';
                
                // Display detailed error information
                if (data.error) {
                    logsDiv.innerHTML += `<div class="log-entry error"><strong>❌ Error:</strong> ${escapeHtml(data.error)}</div>`;
                }
                if (data.error_details) {
                    logsDiv.innerHTML += `<div class="log-entry error"><strong>Stack Trace:</strong><pre style="white-space: pre-wrap; font-family: monospace; font-size: 12px; background: #2d2d2d; padding: 10px; border-radius: 4px; margin-top: 5px;">${escapeHtml(data.error_details)}</pre></div>`;
                }
                
                // Auto-scroll to bottom to show error
                logsDiv.scrollTop = logsDiv.scrollHeight;
                
                submitBtn.disabled = false;
                submitBtn.textContent = 'Run Automation';
                abortBtn.style.display = 'none';
                currentExecutionId = null;
                
            } else if (data.status === 'aborted') {
                clearInterval(pollInterval);
                
                currentStepSection.style.display = 'none';
                
                submitBtn.disabled = false;
                submitBtn.textContent = 'Run Automation';
                abortBtn.style.display = 'none';
                currentExecutionId = null;
            }
            
        } catch (error) {
            clearInterval(pollInterval);
            overallStatus.textContent = 'error';
            overallStatus.className = 'overall-status error';
            currentStepSection.style.display = 'none';
            logsDiv.innerHTML += `<div class="log-entry error"><strong>❌ Polling Error:</strong> ${escapeHtml(error.message)}</div>`;
            logsDiv.innerHTML += `<div class="log-entry error"><pre style="white-space: pre-wrap; font-family: monospace; font-size: 12px;">${escapeHtml(error.stack || 'No stack trace available')}</pre></div>`;
            logsDiv.scrollTop = logsDiv.scrollHeight;
            submitBtn.disabled = false;
            submitBtn.textContent = 'Run Automation';
            abortBtn.style.display = 'none';
            currentExecutionId = null;
        }
    }, 1000); // Poll every 1 second for faster updates
}

function updateStepsList(steps) {
    const stepsList = document.getElementById('stepsList');
    
    stepsList.innerHTML = steps.map(step => {
        let icon = '';
        let statusClass = '';
        
        switch (step.status) {
            case 'pending':
                icon = '○';
                statusClass = 'pending';
                break;
            case 'running':
                icon = '⟳';
                statusClass = 'running';
                break;
            case 'success':
                icon = '✓';
                statusClass = 'success';
                break;
            case 'error':
                icon = '✗';
                statusClass = 'error';
                break;
            case 'skipped':
                icon = '⊘';
                statusClass = 'skipped';
                break;
        }
        
        let detailsHTML = '';
        if (step.duration) {
            detailsHTML = `<span class="step-duration">${step.duration}s</span>`;
        }
        if (step.message) {
            detailsHTML += `<div class="step-message">${escapeHtml(step.message)}</div>`;
        }
        
        return `
            <div class="step-item ${statusClass}">
                <span class="step-icon">${icon}</span>
                <span class="step-name">${escapeHtml(step.name)}</span>
                ${detailsHTML}
            </div>
        `;
    }).join('');
    
    // Auto-scroll to the latest step
    const lastStep = stepsList.lastElementChild;
    if (lastStep) {
        lastStep.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
}

function updateLogs(logs) {
    const logsDiv = document.getElementById('logs');
    
    // Only append new logs (avoid duplicates)
    const currentLogCount = logsDiv.children.length;
    const newLogs = logs.slice(currentLogCount);
    
    newLogs.forEach(log => {
        const logEntry = document.createElement('div');
        logEntry.className = 'log-entry';
        
        // Extract log text from object or string
        let logText = '';
        if (typeof log === 'string') {
            logText = log;
        } else if (log && typeof log === 'object') {
            // Handle structured log objects
            logText = log.message || log.text || log.log || JSON.stringify(log);
        } else {
            logText = String(log);
        }
        
        // Add class based on log content or level
        const logLower = logText.toLowerCase();
        const logLevel = (log && log.level) ? log.level.toLowerCase() : '';
        
        if (logLevel === 'error' || logLower.includes('error') || logLower.includes('failed')) {
            logEntry.classList.add('error');
        } else if (logLevel === 'success' || logLower.includes('success') || logLower.includes('created')) {
            logEntry.classList.add('success');
        } else if (logLevel === 'warning' || logLower.includes('warning')) {
            logEntry.classList.add('warning');
        }
        
        logEntry.textContent = logText;
        logsDiv.appendChild(logEntry);
    });
    
    // Auto-scroll to bottom
    logsDiv.scrollTop = logsDiv.scrollHeight;
}

function getFullInstanceUrl() {
    const selected = document.getElementById('instance_url').value;
    if (!selected) return '';
    if (selected === 'prod') return 'https://trimbledx.my.salesforce.com';
    if (selected === 'other') {
        const custom = document.getElementById('custom_instance_name').value.trim();
        return custom ? `https://trimbledx--${custom}.sandbox.my.salesforce.com` : '';
    }
    return `https://trimbledx--${selected}.sandbox.my.salesforce.com`;
}

function showResults(results) {
    const resultsSection = document.getElementById('resultsSection');
    const resultsDiv = document.getElementById('results');
    
    let resultsHTML = '';
    const instanceUrl = getFullInstanceUrl();
    
    if (results.account_id) {
        resultsHTML += `
            <p><strong>Account ID:</strong> <a href="${instanceUrl}/${results.account_id}" target="_blank">${results.account_id}</a></p>
        `;
    }
    
    if (results.contact_id) {
        resultsHTML += `
            <p><strong>Contact ID:</strong> <a href="${instanceUrl}/${results.contact_id}" target="_blank">${results.contact_id}</a></p>
        `;
    }
    
    if (results.opportunity_id) {
        resultsHTML += `
            <p><strong>Opportunity ID:</strong> <a href="${instanceUrl}/${results.opportunity_id}" target="_blank">${results.opportunity_id}</a></p>
        `;
    }
    
    if (results.quote_id) {
        resultsHTML += `
            <p><strong>Quote ID:</strong> <a href="${instanceUrl}/${results.quote_id}" target="_blank">${results.quote_id}</a></p>
        `;
    }
    
    if (results.oracle_account_number) {
        resultsHTML += `<p><strong>Oracle Account Number:</strong> ${results.oracle_account_number}</p>`;
    }
    
    if (resultsHTML) {
        resultsDiv.innerHTML = resultsHTML;
        resultsSection.style.display = 'block';
    }
}

function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
}

// ============ TAB SWITCHING ============

function switchTab(tabId) {
    // Hide all tab contents
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    // Remove active from all tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    // Show selected tab
    document.getElementById(tabId).classList.add('active');
    // Activate button
    document.querySelector(`[data-tab="${tabId}"]`).classList.add('active');
}

// ============ ORDER PROCESSING ============

let opExecutionId = null;

// Load order processing steps on page load
document.addEventListener('DOMContentLoaded', function() {
    loadOrderProcessingSteps();
    
});

async function loadOrderProcessingSteps() {
    try {
        const response = await fetch('/api/order-processing/steps');
        const result = await response.json();
        
        if (result.success) {
            const container = document.getElementById('opStepsList');
            container.innerHTML = result.steps.map((step, idx) => `
                <div class="op-step-item">
                    <label class="checkbox-label">
                        <input type="checkbox" class="op-step-checkbox" value="${step.id}" checked>
                        <span><strong>Step ${idx + 1}:</strong> ${step.description} <small>(${step.name})</small></span>
                    </label>
                </div>
            `).join('');
        }
    } catch (error) {
        console.error('Failed to load order processing steps:', error);
    }
}

// Select All / Deselect All
document.getElementById('op_select_all').addEventListener('change', function() {
    const checkboxes = document.querySelectorAll('.op-step-checkbox');
    checkboxes.forEach(cb => cb.checked = this.checked);
});

// Abort button for order processing
document.getElementById('opAbortBtn').addEventListener('click', async function() {
    if (!opExecutionId) return;
    
    if (confirm('Are you sure you want to abort order processing?')) {
        try {
            const response = await fetch(`/api/abort/${opExecutionId}`, {
                method: 'POST'
            });
            const result = await response.json();
            if (result.success) {
                this.disabled = true;
                this.textContent = 'Aborting...';
            }
        } catch (error) {
            console.error('Error aborting:', error);
        }
    }
});

// Order Processing form submission
document.getElementById('orderProcessingForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const submitBtn = document.getElementById('opSubmitBtn');
    const abortBtn = document.getElementById('opAbortBtn');
    const overallStatus = document.getElementById('opOverallStatus');
    const currentStepSection = document.getElementById('opCurrentStepSection');
    const stepsProgress = document.getElementById('opStepsProgress');
    const logsDiv = document.getElementById('opLogs');
    
    // Gather data from common session fields
    const instanceUrl = document.getElementById('instance_url').value;
    const customInstanceName = document.getElementById('custom_instance_name').value.trim();
    const apiVersion = document.getElementById('api_version').value.trim();
    const orderId = document.getElementById('op_order_id').value.trim();
    const waitTime = parseFloat(document.getElementById('op_wait_time').value) || 1;
    
    // Get selected steps
    const selectedSteps = Array.from(document.querySelectorAll('.op-step-checkbox:checked'))
        .map(cb => cb.value);
    
    // Validation
    const errors = [];
    if (!instanceUrl) errors.push('Instance selection is required');
    if (instanceUrl === 'other' && !customInstanceName) errors.push('Custom Instance Name is required');
    if (!orderId) errors.push('Order ID is required');
    if (selectedSteps.length === 0) errors.push('At least one batch step must be selected');
    
    if (errors.length > 0) {
        alert('Please fix the following errors:\n\n' + errors.join('\n'));
        return;
    }
    
    // Disable submit, enable abort
    submitBtn.disabled = true;
    submitBtn.textContent = 'Running...';
    abortBtn.style.display = 'inline-block';
    abortBtn.disabled = false;
    abortBtn.textContent = 'Abort Process';
    
    // Clear previous
    stepsProgress.innerHTML = '';
    logsDiv.innerHTML = '';
    overallStatus.textContent = 'Starting...';
    overallStatus.className = 'overall-status running';
    
    try {
        const response = await fetch('/api/order-processing/run', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                instance_url: instanceUrl,
                custom_instance_name: customInstanceName,
                api_version: apiVersion,
                order_id: orderId,
                selected_steps: selectedSteps,
                wait_time: waitTime
            })
        });
        
        const result = await response.json();
        
        if (!result.success) {
            throw new Error(result.error || 'Unknown error');
        }
        
        opExecutionId = result.execution_id;
        pollOrderProcessingStatus(opExecutionId);
        
    } catch (error) {
        overallStatus.textContent = 'Error';
        overallStatus.className = 'overall-status error';
        logsDiv.innerHTML = `<div class="log-entry error"><strong>Error:</strong> ${escapeHtml(error.message)}</div>`;
        submitBtn.disabled = false;
        submitBtn.textContent = 'Run Order Processing';
        abortBtn.style.display = 'none';
    }
});

async function pollOrderProcessingStatus(executionId) {
    const overallStatus = document.getElementById('opOverallStatus');
    const currentStepSection = document.getElementById('opCurrentStepSection');
    const currentStep = document.getElementById('opCurrentStep');
    const stepsProgress = document.getElementById('opStepsProgress');
    const logsDiv = document.getElementById('opLogs');
    const submitBtn = document.getElementById('opSubmitBtn');
    const abortBtn = document.getElementById('opAbortBtn');
    
    const pollInterval = setInterval(async () => {
        try {
            const response = await fetch(`/api/status/${executionId}`);
            const result = await response.json();
            
            if (!result.success) {
                throw new Error('Failed to get status');
            }
            
            const data = result.data;
            
            // Update overall status
            if (data.status) {
                overallStatus.textContent = data.status;
                overallStatus.className = 'overall-status ' + data.status;
            }
            
            // Update current step
            if (data.current_step) {
                currentStepSection.style.display = 'block';
                const stepText = currentStep.querySelector('.step-text');
                if (stepText) stepText.textContent = data.current_step;
            } else {
                currentStepSection.style.display = 'none';
            }
            
            // Update steps progress
            if (data.steps && data.steps.length > 0) {
                updateOpStepsList(data.steps);
            }
            
            // Update logs
            if (data.logs && data.logs.length > 0) {
                updateOpLogs(data.logs);
            }
            
            // Check terminal states
            if (data.status === 'completed' || data.status === 'error' || data.status === 'aborted') {
                clearInterval(pollInterval);
                currentStepSection.style.display = 'none';
                
                if (data.status === 'error' && data.error) {
                    logsDiv.innerHTML += `<div class="log-entry error"><strong>Error:</strong> ${escapeHtml(data.error)}</div>`;
                }
                
                submitBtn.disabled = false;
                submitBtn.textContent = 'Run Order Processing';
                abortBtn.style.display = 'none';
                opExecutionId = null;
            }
        } catch (error) {
            clearInterval(pollInterval);
            overallStatus.textContent = 'Error';
            overallStatus.className = 'overall-status error';
            logsDiv.innerHTML += `<div class="log-entry error"><strong>Polling Error:</strong> ${escapeHtml(error.message)}</div>`;
            submitBtn.disabled = false;
            submitBtn.textContent = 'Run Order Processing';
            abortBtn.style.display = 'none';
            opExecutionId = null;
        }
    }, 1000);
}

function updateOpStepsList(steps) {
    const stepsProgress = document.getElementById('opStepsProgress');
    
    stepsProgress.innerHTML = steps.map(step => {
        let icon = '○';
        let statusClass = 'pending';
        
        switch (step.status) {
            case 'running': icon = '⟳'; statusClass = 'running'; break;
            case 'success': icon = '✓'; statusClass = 'success'; break;
            case 'error': icon = '✗'; statusClass = 'error'; break;
            case 'skipped': icon = '⊘'; statusClass = 'skipped'; break;
        }
        
        let detailsHTML = '';
        if (step.duration) detailsHTML = `<span class="step-duration">${step.duration}s</span>`;
        if (step.message) detailsHTML += `<div class="step-message">${escapeHtml(step.message)}</div>`;
        
        return `
            <div class="step-item ${statusClass}">
                <span class="step-icon">${icon}</span>
                <span class="step-name">${escapeHtml(step.name)}</span>
                ${detailsHTML}
            </div>
        `;
    }).join('');
    
    const lastStep = stepsProgress.lastElementChild;
    if (lastStep) lastStep.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function updateOpLogs(logs) {
    const logsDiv = document.getElementById('opLogs');
    const currentLogCount = logsDiv.children.length;
    const newLogs = logs.slice(currentLogCount);
    
    newLogs.forEach(log => {
        const logEntry = document.createElement('div');
        logEntry.className = 'log-entry';
        
        let logText = typeof log === 'string' ? log : (log.message || JSON.stringify(log));
        const logLower = logText.toLowerCase();
        
        if (logLower.includes('error') || logLower.includes('failed')) {
            logEntry.classList.add('error');
        } else if (logLower.includes('success') || logLower.includes('completed')) {
            logEntry.classList.add('success');
        } else if (logLower.includes('warning')) {
            logEntry.classList.add('warning');
        }
        
        logEntry.textContent = logText;
        logsDiv.appendChild(logEntry);
    });
    
    logsDiv.scrollTop = logsDiv.scrollHeight;
}
