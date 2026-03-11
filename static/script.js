// script.js - Frontend JavaScript with Step Tracking and Abort

let currentExecutionId = null;

// Set default quote start date to yesterday
document.addEventListener('DOMContentLoaded', function() {
    const yesterday = new Date();
    yesterday.setDate(yesterday.getDate() - 1);
    const dateStr = yesterday.toISOString().split('T')[0];
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
    
    // Check if session ID is provided
    if (!data.session_id || data.session_id.trim() === '') {
        errors.push('Session ID is required');
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

function showResults(results) {
    const resultsSection = document.getElementById('resultsSection');
    const resultsDiv = document.getElementById('results');
    
    let resultsHTML = '';
    const instanceUrl = document.getElementById('instance_url').value;
    
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
