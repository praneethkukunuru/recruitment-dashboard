// Dashboard JavaScript functionality

// Utility function to ensure page is at top
function scrollToTop() {
    window.scrollTo({
        top: 0,
        left: 0,
        behavior: 'smooth'
    });
}

// Check for existing processed data on page load
function checkForExistingData() {
    console.log('=== CHECKING FOR EXISTING DATA ===');
    
    // Check for existing data in session (server-side)
    $.ajax({
        url: '/check_existing_data',
        method: 'GET',
        success: function(response) {
            console.log('Existing data check response:', response);
            
            if (response.has_data) {
                console.log('Found existing data, restoring...');
                restoreDashboardFromData(response);
            } else {
                console.log('No existing data found');
            }
        },
        error: function(xhr, status, error) {
            console.error('Error checking existing data:', error);
        }
    });
}

function processFinanceReport() {
    console.log('=== PROCESSING FINANCE REPORT ===');
    $.ajax({
        url: '/process_finance_report',
        type: 'POST',
        contentType: 'application/json',
        success: function(response) {
            console.log('Finance report response:', response);
            if (response.success) {
                console.log('Finance report successful, updating UI...');
                
                // Save to localStorage for persistence
                localStorage.setItem('financeData', JSON.stringify({
                    kpis: response.kpis,
                    charts: response.charts,
                    filename: response.filename,
                    sheet_names: response.sheet_names,
                    processed_data: response.processed_data,
                    specific_values: response.specific_values
                }));
                
                updateFinanceKPIs(response.kpis);
                updateSpecificFinancialValues(response.specific_values);
                renderFinanceCharts(response.charts);
                
                // Hide upload area and show dashboard
                showFinanceDashboardAfterUpload();
                scrollToTop();
            } else {
                console.error('Finance report failed:', response.error);
                alert('Failed to process finance report: ' + response.error);
            }
        },
        error: function(xhr, status, error) {
            console.error('Finance processing error:', xhr.responseText);
            alert('Failed to process finance report. Please try again.');
        }
    });
}

function showFinanceDashboardAfterUpload() {
    console.log('=== SHOWING FINANCE DASHBOARD AFTER UPLOAD ===');
    
    // Hide upload area and show dashboard sections
    console.log('Hiding finance upload section...');
    $('#finance-upload-section').hide();
    
    console.log('Showing finance sections...');
    $('#finance-dashboard .section').show();
    
    // Update Data Explorer with new finance data
    console.log('Updating Data Explorer with finance data...');
    loadDataExplorerData();
    
    console.log('Finance dashboard UI update complete');
}

function updateSpecificFinancialValues(specificValues) {
    console.log('=== UPDATING SPECIFIC FINANCIAL VALUES ===');
    console.log('Specific values:', specificValues);
    
    if (specificValues) {
        // Direct Hire values
        $('#kpi-direct-hire-total-revenue').text(formatCurrency(specificValues.direct_hire?.total_revenue || 0));
        $('#kpi-direct-hire-gross-income').text(formatCurrency(specificValues.direct_hire?.gross_income || 0));
        $('#kpi-direct-hire-net-income').text(formatCurrency(specificValues.direct_hire?.net_income || 0));
        
        // IT Services values
        $('#kpi-it-services-total-revenue').text(formatCurrency(specificValues.it_services?.total_revenue || 0));
        $('#kpi-it-services-gross-income').text(formatCurrency(specificValues.it_services?.gross_income || 0));
        $('#kpi-it-services-net-income').text(formatCurrency(specificValues.it_services?.net_income || 0));
        
        // IT Staffing values
        $('#kpi-it-staffing-total-revenue').text(formatCurrency(specificValues.it_staffing?.total_revenue || 0));
        $('#kpi-it-staffing-gross-income').text(formatCurrency(specificValues.it_staffing?.gross_income || 0));
        $('#kpi-it-staffing-net-income').text(formatCurrency(specificValues.it_staffing?.net_income || 0));
    }
}

function updateFinanceKPIs(kpis) {
    if (kpis) {
        // Update KPI values with comprehensive data
        $('#kpi-total-revenue').text(formatCurrency(kpis.total_revenue?.value || 0));
        $('#kpi-total-expenses').text(formatCurrency(kpis.total_expenses?.value || 0));
        $('#kpi-net-income').text(formatCurrency(kpis.total_net_income?.value || 0));
        $('#kpi-profit-margin').text(formatPercentage(kpis.profit_margin?.value || 0));
        $('#kpi-avg-monthly-revenue').text(formatCurrency(kpis.avg_monthly_revenue?.value || 0));
        $('#kpi-avg-monthly-net-income').text(formatCurrency(kpis.avg_monthly_net_income?.value || 0));
    }
}

function renderFinanceCharts(charts) {
    console.log('=== RENDERING FINANCE CHARTS ===');
    console.log('Charts to render:', Object.keys(charts));
    
    Object.keys(charts).forEach(chartName => {
        let chartId = 'chart-' + chartName.replace(/_/g, '-');
        console.log(`Looking for chart container: ${chartId}`);
        
        const $container = $('#' + chartId);
        console.log(`Found container:`, $container.length);
        
        if ($container.length > 0) {
            try {
                const chartData = charts[chartName];
                console.log(`Chart data for ${chartName}:`, chartData);
                
                // Validate chart data structure
                if (!chartData || !chartData.data || !chartData.data.labels) {
                    console.error(`Invalid chart data structure for ${chartName}:`, chartData);
                    return;
                }
                
                // Clear any existing canvas
                $container.empty();
                
                // Create new canvas element
                const canvas = $('<canvas>').attr('id', chartId + '-canvas')[0];
                $container.append(canvas);
                
                // Create Chart.js chart
                const ctx = canvas.getContext('2d');
                new Chart(ctx, chartData);
                
                console.log(`Successfully rendered chart: ${chartName}`);
            } catch (e) {
                console.error('Failed to render finance chart:', chartName, e);
                console.error('Chart data that failed:', charts[chartName]);
            }
        } else {
            console.warn(`Chart container not found: ${chartId}`);
        }
    });
}

// Formula Customization Functions
let customFormulas = {
    'total_revenue': 'Direct Hire Revenue + Services Revenue + IT Staffing Revenue',
    'total_expenses': 'Direct Hire Expenses + Services Expenses + IT Staffing Expenses',
    'net_income': 'Total Revenue - Total Expenses',
    'profit_margin': '(Net Income / Total Revenue) * 100',
    'avg_monthly_revenue': 'Total Revenue / 8',
    'avg_monthly_net_income': 'Net Income / 8'
};

// Initialize formula customization
function initializeFormulaCustomization() {
    console.log('=== INITIALIZING FORMULA CUSTOMIZATION ===');
    
    // Load saved formulas from session
    loadCustomFormulas();
    
    // Set up event listeners
    setupFormulaEventListeners();
    
    // Update formula previews
    updateFormulaPreviews();
}

// Load custom formulas from session
function loadCustomFormulas() {
    // Try to load from localStorage first
    const savedFormulas = localStorage.getItem('customFinanceFormulas');
    if (savedFormulas) {
        try {
            customFormulas = JSON.parse(savedFormulas);
            console.log('Loaded custom formulas:', customFormulas);
        } catch (e) {
            console.error('Error loading custom formulas:', e);
        }
    }
    
    // Update form inputs with loaded formulas
    Object.keys(customFormulas).forEach(key => {
        const input = document.getElementById(key.replace('_', '-') + '-formula');
        if (input) {
            input.value = customFormulas[key];
        }
    });
}

// Save custom formulas to session
function saveCustomFormulas() {
    console.log('=== SAVING CUSTOM FORMULAS ===');
    
    // Collect formulas from inputs
    const formulas = {
        'total_revenue': document.getElementById('total-revenue-formula').value,
        'total_expenses': document.getElementById('total-expenses-formula').value,
        'net_income': document.getElementById('net-income-formula').value,
        'profit_margin': document.getElementById('profit-margin-formula').value,
        'avg_monthly_revenue': document.getElementById('avg-monthly-revenue-formula').value,
        'avg_monthly_net_income': document.getElementById('avg-monthly-net-income-formula').value
    };
    
    // Save to localStorage
    localStorage.setItem('customFinanceFormulas', JSON.stringify(formulas));
    
    // Update global customFormulas object
    customFormulas = formulas;
    
    console.log('Saved formulas:', formulas);
    
    // Send to server for processing
    $.ajax({
        url: '/save_custom_formulas',
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({ formulas: formulas }),
        success: function(response) {
            console.log('Formulas saved to server:', response);
            showNotification('Formulas saved successfully!', 'success');
            
            // Recalculate KPIs with new formulas
            if (window.financeData) {
                recalculateFinanceKPIs();
            }
        },
        error: function(xhr, status, error) {
            console.error('Error saving formulas:', error);
            showNotification('Error saving formulas. Please try again.', 'error');
        }
    });
}

// Set up event listeners for formula customization
function setupFormulaEventListeners() {
    // Edit formulas button
    $('#edit-formulas-btn').on('click', function() {
        $('#formula-editor').slideDown();
        $('#edit-formulas-btn').hide();
        $('#save-formulas-btn').show();
    });
    
    // Save formulas button
    $('#save-formulas-btn').on('click', function() {
        saveCustomFormulas();
        $('#formula-editor').slideUp();
        $('#edit-formulas-btn').show();
        $('#save-formulas-btn').hide();
    });
    
    // Reset formulas button
    $('#reset-formulas-btn').on('click', function() {
        if (confirm('Are you sure you want to reset all formulas to default values?')) {
            resetFormulasToDefault();
        }
    });
    
    // Update previews on input change
    $('.formula-input').on('input', function() {
        updateFormulaPreviews();
    });
}

// Reset formulas to default values
function resetFormulasToDefault() {
    const defaultFormulas = {
        'total_revenue': 'Direct Hire Revenue + Services Revenue + IT Staffing Revenue',
        'total_expenses': 'Direct Hire Expenses + Services Expenses + IT Staffing Expenses',
        'net_income': 'Total Revenue - Total Expenses',
        'profit_margin': '(Net Income / Total Revenue) * 100',
        'avg_monthly_revenue': 'Total Revenue / 8',
        'avg_monthly_net_income': 'Net Income / 8'
    };
    
    Object.keys(defaultFormulas).forEach(key => {
        const input = document.getElementById(key.replace('_', '-') + '-formula');
        if (input) {
            input.value = defaultFormulas[key];
        }
    });
    
    customFormulas = defaultFormulas;
    updateFormulaPreviews();
    
    // Clear saved formulas
    localStorage.removeItem('customFinanceFormulas');
    
    showNotification('Formulas reset to default values', 'info');
}

// Update formula previews
function updateFormulaPreviews() {
    $('#preview-total-revenue').text(document.getElementById('total-revenue-formula').value);
    $('#preview-net-income').text(document.getElementById('net-income-formula').value);
    $('#preview-profit-margin').text(document.getElementById('profit-margin-formula').value);
}

// Recalculate finance KPIs with custom formulas
function recalculateFinanceKPIs() {
    console.log('=== RECALCULATING FINANCE KPIS WITH CUSTOM FORMULAS ===');
    
    if (!window.financeData) {
        console.log('No finance data available for recalculation');
        return;
    }
    
    // Get the processed data
    const processedData = window.financeData.processed_data || window.financeData;
    
    // Calculate KPIs using custom formulas
    const newKPIs = calculateCustomFinanceKPIs(processedData);
    
    // Update the KPIs display
    updateFinanceKPIs(newKPIs);
    
    console.log('KPIs recalculated with custom formulas:', newKPIs);
}

// Calculate finance KPIs using custom formulas
function calculateCustomFinanceKPIs(processedData) {
    console.log('=== CALCULATING CUSTOM FINANCE KPIS ===');
    
    try {
        // Extract base values from processed data
        const baseValues = extractBaseValues(processedData);
        console.log('Base values extracted:', baseValues);
        
        // Calculate KPIs using custom formulas
        const kpis = {};
        
        // Total Revenue
        kpis['total_revenue'] = {
            'value': evaluateFormula(customFormulas['total_revenue'], baseValues),
            'label': 'Total Revenue',
            'format': 'currency'
        };
        
        // Total Expenses
        kpis['total_expenses'] = {
            'value': evaluateFormula(customFormulas['total_expenses'], baseValues),
            'label': 'Total Expenses',
            'format': 'currency'
        };
        
        // Net Income
        kpis['total_net_income'] = {
            'value': evaluateFormula(customFormulas['net_income'], baseValues),
            'label': 'Total Net Income',
            'format': 'currency'
        };
        
        // Profit Margin
        kpis['profit_margin'] = {
            'value': evaluateFormula(customFormulas['profit_margin'], baseValues),
            'label': 'Profit Margin',
            'format': 'percentage'
        };
        
        // Average Monthly Revenue
        kpis['avg_monthly_revenue'] = {
            'value': evaluateFormula(customFormulas['avg_monthly_revenue'], baseValues),
            'label': 'Avg Monthly Revenue',
            'format': 'currency'
        };
        
        // Average Monthly Net Income
        kpis['avg_monthly_net_income'] = {
            'value': evaluateFormula(customFormulas['avg_monthly_net_income'], baseValues),
            'label': 'Avg Monthly Net Income',
            'format': 'currency'
        };
        
        return kpis;
        
    } catch (error) {
        console.error('Error calculating custom finance KPIs:', error);
        return {};
    }
}

// Extract base values from processed data
function extractBaseValues(processedData) {
    const values = {};
    
    // Extract from business units
    if (processedData.business_units) {
        Object.keys(processedData.business_units).forEach(unit => {
            const unitData = processedData.business_units[unit];
            if (unitData.revenue) {
                values[`${unit} Revenue`] = sumArray(unitData.revenue);
            }
            if (unitData.net_income) {
                values[`${unit} Net Income`] = sumArray(unitData.net_income);
            }
        });
    }
    
    // Extract from monthly data
    if (processedData.monthly_data) {
        Object.keys(processedData.monthly_data).forEach(company => {
            const companyData = processedData.monthly_data[company];
            if (companyData.total_income) {
                values[`${company} Income`] = sumArray(companyData.total_income);
            }
            if (companyData.total_expense) {
                values[`${company} Expenses`] = sumArray(companyData.total_expense);
            }
        });
    }
    
    // Add calculated totals
    values['Total Revenue'] = values['Direct Hire Net income Revenue'] + values['Services Net income Revenue'] + values['IT Staffing Net Income Revenue'] || 0;
    values['Total Expenses'] = values['Techgene PnL new Expenses'] + values['Vensiti PnL new Expenses'] || 0;
    values['Net Income'] = values['Total Revenue'] - values['Total Expenses'];
    values['Month Count'] = 8;
    
    return values;
}

// Evaluate a formula string with given values
function evaluateFormula(formula, values) {
    try {
        // Replace variable names with values
        let expression = formula;
        Object.keys(values).forEach(key => {
            const regex = new RegExp(key.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'g');
            expression = expression.replace(regex, values[key]);
        });
        
        // Evaluate the expression safely
        const result = Function('"use strict"; return (' + expression + ')')();
        return isNaN(result) ? 0 : result;
    } catch (error) {
        console.error('Error evaluating formula:', formula, error);
        return 0;
    }
}

// Helper function to sum array values
function sumArray(arr) {
    return arr.reduce((sum, val) => sum + (val || 0), 0);
}

// Show notification
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = $(`
        <div class="notification notification-${type}">
            <span class="notification-message">${message}</span>
            <button class="notification-close">&times;</button>
        </div>
    `);
    
    // Add to page
    $('body').append(notification);
    
    // Show notification
    notification.fadeIn();
    
    // Auto-hide after 3 seconds
    setTimeout(() => {
        notification.fadeOut(() => notification.remove());
    }, 3000);
    
    // Close button
    notification.find('.notification-close').on('click', () => {
        notification.fadeOut(() => notification.remove());
    });
}

// Data Explorer Functions
let currentDataSource = 'recruitment';
let recruitmentData = null;
let financeData = null;

// Initialize Data Explorer
function initializeDataExplorer() {
    console.log('=== INITIALIZING DATA EXPLORER ===');
    
    // Set up event listeners
    setupDataExplorerEventListeners();
    
    // Update data status indicators
    updateDataStatusIndicators();
    
    // Load initial data
    loadDataExplorerData();
}

// Set up event listeners for Data Explorer
function setupDataExplorerEventListeners() {
    // Search functionality
    $('#recruitment-search').on('input', function() {
        filterRecruitmentData($(this).val());
    });
    
    $('#finance-search').on('input', function() {
        filterFinanceData($(this).val());
    });
}

// Switch data source in Data Explorer
function switchDataSource(source) {
    console.log('=== SWITCHING DATA SOURCE ===', source);
    
    currentDataSource = source;
    
    // Update tab buttons
    $('.data-tab-btn').removeClass('active');
    $(`#tab-${source}`).addClass('active');
    
    // Update content visibility
    $('.data-source-content').removeClass('active').hide();
    $(`#content-${source}`).addClass('active').show();
    
    // Load data for the selected source
    loadDataForSource(source);
}

// Load data for specific source
function loadDataForSource(source) {
    if (source === 'recruitment') {
        loadRecruitmentDataTables();
    } else if (source === 'finance') {
        loadFinanceDataTables();
    }
}

// Update data status indicators
function updateDataStatusIndicators() {
    console.log('=== UPDATING DATA STATUS INDICATORS ===');
    
    // Check recruitment data from localStorage
    const hasRecruitmentData = !!localStorage.getItem('recruitmentData');
    console.log('Has recruitment data in localStorage:', hasRecruitmentData);
    $('#status-recruitment').text(hasRecruitmentData ? 'Data Available' : 'No Data')
                           .toggleClass('has-data', hasRecruitmentData);
    
    // Check finance data from localStorage
    const hasFinanceData = !!localStorage.getItem('financeData');
    console.log('Has finance data in localStorage:', hasFinanceData);
    $('#status-finance').text(hasFinanceData ? 'Data Available' : 'No Data')
                        .toggleClass('has-data', hasFinanceData);
}

// Load Data Explorer data
function loadDataExplorerData() {
    console.log('=== LOADING DATA EXPLORER DATA ===');
    console.log('All localStorage keys:', Object.keys(localStorage));
    
    // Get data directly from localStorage
    const recruitmentDataStr = localStorage.getItem('recruitmentData');
    const financeDataStr = localStorage.getItem('financeData');
    
    console.log('Recruitment data string length:', recruitmentDataStr ? recruitmentDataStr.length : 0);
    console.log('Finance data string length:', financeDataStr ? financeDataStr.length : 0);
    
    if (recruitmentDataStr) {
        try {
            recruitmentData = JSON.parse(recruitmentDataStr);
            window.recruitmentData = recruitmentData; // Also set global variable
            console.log('Found recruitment data in localStorage:', recruitmentData);
            console.log('Recruitment data keys:', Object.keys(recruitmentData));
            console.log('Sheet1 data exists:', !!recruitmentData.sheet1_data);
            console.log('Sheet2 data exists:', !!recruitmentData.sheet2_data);
            if (recruitmentData.sheet1_data) {
                console.log('Sheet1 data keys:', Object.keys(recruitmentData.sheet1_data));
            }
            if (recruitmentData.sheet2_data) {
                console.log('Sheet2 data keys:', Object.keys(recruitmentData.sheet2_data));
            }
        } catch (e) {
            console.error('Error parsing recruitment data from localStorage:', e);
        }
    } else {
        console.log('No recruitment data found in localStorage');
    }
    
    if (financeDataStr) {
        try {
            financeData = JSON.parse(financeDataStr);
            window.financeData = financeData; // Also set global variable
            console.log('Found finance data in localStorage:', financeData);
            console.log('Finance data keys:', Object.keys(financeData));
        } catch (e) {
            console.error('Error parsing finance data from localStorage:', e);
        }
    } else {
        console.log('No finance data found in localStorage');
    }
    
    // Update status indicators
    updateDataStatusIndicators();
    
    // Load initial data for current source
    loadDataForSource(currentDataSource);
}

// Load recruitment data tables
function loadRecruitmentDataTables() {
    console.log('=== LOADING RECRUITMENT DATA TABLES ===');
    console.log('Recruitment data:', recruitmentData);
    
    if (!recruitmentData) {
        console.log('No recruitment data available');
        return;
    }
    
    console.log('Recruitment data keys:', Object.keys(recruitmentData));
    console.log('Sheet1 data:', recruitmentData.sheet1_data);
    console.log('Sheet2 data:', recruitmentData.sheet2_data);
    console.log('Sheet3 data:', recruitmentData.sheet3_data);
    
    // Check if we have the expected data structure
    if (!recruitmentData.sheet1_data || !recruitmentData.sheet2_data) {
        console.log('Recruitment data missing expected sheet structure');
        console.log('Available keys:', Object.keys(recruitmentData));
        return;
    }
    
    // Load employment types data
    loadEmploymentTypesTable();
    
    // Load placement metrics data
    loadPlacementMetricsTable();
}

// Load employment types table
function loadEmploymentTypesTable() {
    const table = $('#recruitment-employment-table tbody');
    table.empty();
    
    if (recruitmentData.sheet1_data && recruitmentData.sheet1_data.tg_data) {
        const months = recruitmentData.sheet1_data.months || ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug'];
        const tgData = recruitmentData.sheet1_data.tg_data;
        
        months.forEach((month, index) => {
            const row = `
                <tr>
                    <td>${month}</td>
                    <td>${tgData['TG W2'] ? tgData['TG W2'][index] || 0 : 0}</td>
                    <td>${tgData['TG C2C'] ? tgData['TG C2C'][index] || 0 : 0}</td>
                    <td>${tgData['TG 1099'] ? tgData['TG 1099'][index] || 0 : 0}</td>
                    <td>${tgData['TG Referral'] ? tgData['TG Referral'][index] || 0 : 0}</td>
                </tr>
            `;
            table.append(row);
        });
    } else {
        table.append('<tr><td colspan="5" style="text-align: center; color: #666;">No employment data available</td></tr>');
    }
}

// Load placement metrics table
function loadPlacementMetricsTable() {
    const table = $('#recruitment-placements-table tbody');
    table.empty();
    
    if (recruitmentData.sheet2_data && recruitmentData.sheet2_data.placement_metrics) {
        const months = recruitmentData.sheet2_data.months || ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug'];
        const metrics = recruitmentData.sheet2_data.placement_metrics;
        
        months.forEach((month, index) => {
            const row = `
                <tr>
                    <td>${month}</td>
                    <td>${metrics['New Placements'] ? metrics['New Placements'][index] || 0 : 0}</td>
                    <td>${metrics['Terminations'] ? metrics['Terminations'][index] || 0 : 0}</td>
                    <td>${metrics['Net Placements'] ? metrics['Net Placements'][index] || 0 : 0}</td>
                    <td>${metrics['Net billables'] ? metrics['Net billables'][index] || 0 : 0}</td>
                </tr>
            `;
            table.append(row);
        });
    } else {
        table.append('<tr><td colspan="5" style="text-align: center; color: #666;">No placement data available</td></tr>');
    }
}

// Load finance data tables
function loadFinanceDataTables() {
    console.log('=== LOADING FINANCE DATA TABLES ===');
    
    if (!financeData) {
        console.log('No finance data available');
        return;
    }
    
    // Load business units summary
    loadBusinessUnitsTable();
    
    // Load P&L data
    loadPnLTable();
}

// Load business units summary table
function loadBusinessUnitsTable() {
    const table = $('#finance-summary-table tbody');
    table.empty();
    
    if (financeData.processed_data && financeData.processed_data.business_units) {
        const businessUnits = financeData.processed_data.business_units;
        const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug'];
        
        Object.keys(businessUnits).forEach(unitName => {
            const unitData = businessUnits[unitName];
            const revenue = unitData.revenue || [];
            
            const row = `
                <tr>
                    <td><strong>${unitName}</strong></td>
                    ${months.map((_, index) => `<td>${revenue[index] ? revenue[index].toLocaleString() : 0}</td>`).join('')}
                </tr>
            `;
            table.append(row);
        });
    } else {
        table.append('<tr><td colspan="9" style="text-align: center; color: #666;">No business units data available</td></tr>');
    }
}

// Load P&L table
function loadPnLTable() {
    const table = $('#finance-pnl-table tbody');
    table.empty();
    
    if (financeData.processed_data && financeData.processed_data.monthly_data) {
        const monthlyData = financeData.processed_data.monthly_data;
        const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug'];
        
        Object.keys(monthlyData).forEach(companyName => {
            const companyData = monthlyData[companyName];
            const income = companyData.total_income || [];
            const expenses = companyData.total_expense || [];
            const netIncome = companyData.net_income || [];
            
            months.forEach((month, index) => {
                const row = `
                    <tr>
                        <td>${companyName}</td>
                        <td>${month}</td>
                        <td>${income[index] ? income[index].toLocaleString() : 0}</td>
                        <td>${expenses[index] ? expenses[index].toLocaleString() : 0}</td>
                        <td>${netIncome[index] ? netIncome[index].toLocaleString() : 0}</td>
                    </tr>
                `;
                table.append(row);
            });
        });
    } else {
        table.append('<tr><td colspan="5" style="text-align: center; color: #666;">No P&L data available</td></tr>');
    }
}

// Filter recruitment data
function filterRecruitmentData(searchTerm) {
    const tables = ['#recruitment-employment-table', '#recruitment-placements-table'];
    
    tables.forEach(tableId => {
        const table = $(tableId);
        const rows = table.find('tbody tr');
        
        rows.each(function() {
            const row = $(this);
            const text = row.text().toLowerCase();
            const matches = text.includes(searchTerm.toLowerCase());
            row.toggle(matches);
        });
    });
}

// Filter finance data
function filterFinanceData(searchTerm) {
    const tables = ['#finance-summary-table', '#finance-pnl-table'];
    
    tables.forEach(tableId => {
        const table = $(tableId);
        const rows = table.find('tbody tr');
        
        rows.each(function() {
            const row = $(this);
            const text = row.text().toLowerCase();
            const matches = text.includes(searchTerm.toLowerCase());
            row.toggle(matches);
        });
    });
}

// Clear recruitment search
function clearRecruitmentSearch() {
    $('#recruitment-search').val('');
    filterRecruitmentData('');
}

// Clear finance search
function clearFinanceSearch() {
    $('#finance-search').val('');
    filterFinanceData('');
}

// Export recruitment data
function exportRecruitmentData() {
    console.log('=== EXPORTING RECRUITMENT DATA ===');
    
    if (!recruitmentData) {
        showNotification('No recruitment data available to export', 'error');
        return;
    }
    
    // Create CSV content
    let csvContent = '';
    
    // Employment data
    csvContent += 'Employment Types Data\n';
    csvContent += 'Month,TG W2,TG C2C,TG 1099,TG Referral\n';
    
    if (recruitmentData.sheet1_data && recruitmentData.sheet1_data.tg_data) {
        const months = recruitmentData.sheet1_data.months || ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug'];
        const tgData = recruitmentData.sheet1_data.tg_data;
        
        months.forEach((month, index) => {
            csvContent += `${month},${tgData['TG W2'] ? tgData['TG W2'][index] || 0 : 0},${tgData['TG C2C'] ? tgData['TG C2C'][index] || 0 : 0},${tgData['TG 1099'] ? tgData['TG 1099'][index] || 0 : 0},${tgData['TG Referral'] ? tgData['TG Referral'][index] || 0 : 0}\n`;
        });
    }
    
    // Placement data
    csvContent += '\nPlacement Metrics Data\n';
    csvContent += 'Month,New Placements,Terminations,Net Placements,Net Billables\n';
    
    if (recruitmentData.sheet2_data && recruitmentData.sheet2_data.placement_metrics) {
        const months = recruitmentData.sheet2_data.months || ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug'];
        const metrics = recruitmentData.sheet2_data.placement_metrics;
        
        months.forEach((month, index) => {
            csvContent += `${month},${metrics['New Placements'] ? metrics['New Placements'][index] || 0 : 0},${metrics['Terminations'] ? metrics['Terminations'][index] || 0 : 0},${metrics['Net Placements'] ? metrics['Net Placements'][index] || 0 : 0},${metrics['Net billables'] ? metrics['Net billables'][index] || 0 : 0}\n`;
        });
    }
    
    // Download CSV
    downloadCSV(csvContent, 'recruitment_data.csv');
    showNotification('Recruitment data exported successfully', 'success');
}

// Export finance data
function exportFinanceData() {
    console.log('=== EXPORTING FINANCE DATA ===');
    
    if (!financeData) {
        showNotification('No finance data available to export', 'error');
        return;
    }
    
    // Create CSV content
    let csvContent = '';
    
    // Business units data
    csvContent += 'Business Units Summary\n';
    csvContent += 'Business Unit,Jan,Feb,Mar,Apr,May,Jun,Jul,Aug\n';
    
    if (financeData.processed_data && financeData.processed_data.business_units) {
        const businessUnits = financeData.processed_data.business_units;
        
        Object.keys(businessUnits).forEach(unitName => {
            const unitData = businessUnits[unitName];
            const revenue = unitData.revenue || [];
            
            csvContent += `${unitName},${revenue.map(val => val || 0).join(',')}\n`;
        });
    }
    
    // P&L data
    csvContent += '\nMonthly P&L Data\n';
    csvContent += 'Company,Month,Total Income,Total Expenses,Net Income\n';
    
    if (financeData.processed_data && financeData.processed_data.monthly_data) {
        const monthlyData = financeData.processed_data.monthly_data;
        const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug'];
        
        Object.keys(monthlyData).forEach(companyName => {
            const companyData = monthlyData[companyName];
            const income = companyData.total_income || [];
            const expenses = companyData.total_expense || [];
            const netIncome = companyData.net_income || [];
            
            months.forEach((month, index) => {
                csvContent += `${companyName},${month},${income[index] || 0},${expenses[index] || 0},${netIncome[index] || 0}\n`;
            });
        });
    }
    
    // Download CSV
    downloadCSV(csvContent, 'finance_data.csv');
    showNotification('Finance data exported successfully', 'success');
}

// Download CSV file
function downloadCSV(content, filename) {
    const blob = new Blob([content], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    
    if (link.download !== undefined) {
        const url = URL.createObjectURL(blob);
        link.setAttribute('href', url);
        link.setAttribute('download', filename);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
}

// Get the currently active dashboard
function getCurrentDashboard() {
    const financeDashboard = document.getElementById('finance-dashboard');
    const recruitmentDashboard = document.getElementById('recruitment-dashboard');
    const dataExplorerDashboard = document.getElementById('data-explorer-dashboard');
    
    // Check if finance dashboard is visible
    if (financeDashboard && financeDashboard.style.display !== 'none' && financeDashboard.style.display !== '') {
        return 'finance';
    }
    
    // Check if recruitment dashboard is visible
    if (recruitmentDashboard && recruitmentDashboard.style.display !== 'none' && recruitmentDashboard.style.display !== '') {
        return 'recruitment';
    }
    
    // Check if data explorer dashboard is visible
    if (dataExplorerDashboard && dataExplorerDashboard.style.display !== 'none' && dataExplorerDashboard.style.display !== '') {
        return 'data-explorer';
    }
    
    // If neither is visible, check which one has data and default to that
    // This handles the case where the page loads and both are hidden initially
    if (window.currentDashboard) {
        return window.currentDashboard;
    }
    
    // Default to finance
    return 'finance';
}

// Restore dashboard from existing data
function restoreDashboardFromData(response) {
    console.log('=== RESTORING DASHBOARD FROM DATA ===');
    console.log('Response:', response);
    
    // Store the response data globally for later use
    window.existingData = response;
    
    // Handle recruitment data - restore regardless of current dashboard
    if (response.has_recruitment_data && response.recruitment_data) {
        console.log('Restoring recruitment data...');
        
        const data = response.recruitment_data;
        
        // Store recruitment data globally
        window.recruitmentData = data;
        
        // Update KPIs
        if (data.kpis) {
            updatePlacementKPIs(data.kpis);
        }
        
        // Render charts
        if (data.charts) {
            renderPlacementCharts(data.charts);
        }
        
        // Mark recruitment dashboard as having data
        window.hasRecruitmentData = true;
        
        // Show the recruitment dashboard if we're on recruitment dashboard
        const currentDashboard = getCurrentDashboard();
        if (currentDashboard === 'recruitment') {
            showDashboardAfterUpload();
        }
    } else if (window.recruitmentData) {
        // If no server data but localStorage has data, restore from localStorage
        console.log('Restoring recruitment data from localStorage...');
        const data = window.recruitmentData;
        
        // Update KPIs
        if (data.kpis) {
            updatePlacementKPIs(data.kpis);
        }
        
        // Render charts
        if (data.charts) {
            renderPlacementCharts(data.charts);
        }
        
        // Mark recruitment dashboard as having data
        window.hasRecruitmentData = true;
        
        // Show the recruitment dashboard if we're on recruitment dashboard
        const currentDashboard = getCurrentDashboard();
        if (currentDashboard === 'recruitment') {
            showDashboardAfterUpload();
        }
    }
    
    // Handle finance data - restore regardless of current dashboard
    if (response.has_finance_data && response.finance_data) {
        console.log('Restoring finance data...');
        
        const data = response.finance_data;
        
        // Store finance data globally
        window.financeData = data;
        
        // Update KPIs
        if (data.kpis) {
            updateFinanceKPIs(data.kpis);
        }
        
        // Update specific financial values
        if (data.specific_values) {
            updateSpecificFinancialValues(data.specific_values);
        }
        
        // Render charts
        if (data.charts) {
            renderFinanceCharts(data.charts);
        }
        
        // Mark finance dashboard as having data
        window.hasFinanceData = true;
        
        // Show the finance dashboard if we're on finance dashboard
        const currentDashboard = getCurrentDashboard();
        if (currentDashboard === 'finance') {
            showFinanceDashboardAfterUpload();
        }
    } else if (window.financeData) {
        // If no server data but localStorage has data, restore from localStorage
        console.log('Restoring finance data from localStorage...');
        const data = window.financeData;
        
        // Update KPIs
        if (data.kpis) {
            updateFinanceKPIs(data.kpis);
        }
        
        // Update specific financial values
        if (data.specific_values) {
            updateSpecificFinancialValues(data.specific_values);
        }
        
        // Render charts
        if (data.charts) {
            renderFinanceCharts(data.charts);
        }
        
        // Mark finance dashboard as having data
        window.hasFinanceData = true;
        
        // Show the finance dashboard if we're on finance dashboard
        const currentDashboard = getCurrentDashboard();
        if (currentDashboard === 'finance') {
            showFinanceDashboardAfterUpload();
        }
    }
    
    // Mark upload areas as having existing data
    markUploadAreasWithExistingData();
    
    // Update Data Explorer with restored data
    console.log('Updating Data Explorer with restored data...');
    loadDataExplorerData();
}


// Mark upload areas to show existing data is available
function initializeSidebarVisibility() {
    console.log('Initializing sidebar visibility...');
    
    // Check which dashboard is currently active
    const currentDashboard = getCurrentDashboard();
    console.log('Current dashboard:', currentDashboard);
    
    const dataSidebar = document.getElementById('data-sidebar');
    const mainContent = document.querySelector('.main-content');
    
    if (currentDashboard === 'recruitment') {
        // Show sidebar for recruitment dashboard
        if (dataSidebar) {
            dataSidebar.style.display = 'block';
            console.log('Sidebar shown for recruitment dashboard');
        }
        if (mainContent) {
            mainContent.classList.add('recruitment-mode');
            mainContent.classList.remove('finance-mode');
        }
    } else if (currentDashboard === 'finance') {
        // Hide sidebar for finance dashboard
        if (dataSidebar) {
            dataSidebar.style.display = 'none';
            console.log('Sidebar hidden for finance dashboard');
        }
        if (mainContent) {
            mainContent.classList.add('finance-mode');
            mainContent.classList.remove('recruitment-mode');
        }
    } else {
        // Default to recruitment dashboard with sidebar
        if (dataSidebar) {
            dataSidebar.style.display = 'block';
            console.log('Sidebar shown by default');
        }
        if (mainContent) {
            mainContent.classList.add('recruitment-mode');
            mainContent.classList.remove('finance-mode');
        }
    }
}

// Mark upload areas to show existing data is available
function markUploadAreasWithExistingData() {
    console.log('=== MARKING UPLOAD AREAS WITH EXISTING DATA ===');
    
    // Mark recruitment sidebar upload area
    const $sidebarRecUpload = $('#sidebar-rec-upload');
    console.log('Recruitment sidebar upload found:', $sidebarRecUpload.length);
    if ($sidebarRecUpload.length > 0) {
        const $sidebarRecText = $sidebarRecUpload.find('.upload-text');
        $sidebarRecText.text('✓ Data available (reload safe)');
        $sidebarRecUpload.addClass('uploaded');
        console.log('Marked recruitment sidebar upload area');
    }
    
    // Mark finance sidebar upload area
    const $sidebarFinanceUpload = $('#sidebar-finance-upload');
    console.log('Finance sidebar upload found:', $sidebarFinanceUpload.length);
    if ($sidebarFinanceUpload.length > 0) {
        const $sidebarFinanceText = $sidebarFinanceUpload.find('.upload-text');
        $sidebarFinanceText.text('✓ Data available (reload safe)');
        $sidebarFinanceUpload.addClass('uploaded');
        console.log('Marked finance sidebar upload area');
    }
    
    console.log('Upload areas marking complete');
}

$(document).ready(function() {
    // Ensure page starts at top
    scrollToTop();
    
    // Initialize sidebar visibility
    initializeSidebarVisibility();
    
    // Check for existing data on page load
    checkForExistingData();
    
    // Initialize formula customization (OLD SYSTEM - DISABLED)
    // initializeFormulaCustomization();
    
    // Initialize data explorer
    initializeDataExplorer();
    
    // File upload handling
    setupFileUploads();
    
    // Setup KPI card click handlers for formula editing
    setupKPICardClickHandlers();
    
    // Column mapping handling
    setupColumnMapping();
    
    // Process data button
    $('#download-report').click(function() {
        processData();
    });
    
    // Monthly data form submission
    $('#monthly-data-form').submit(function(e) {
        e.preventDefault();
        addMonthlyData();
    });
    
    // Setup sidebar file upload
    setupSidebarFileUpload();
    
    // Setup full-screen drag and drop
    setupFullscreenDragDrop();
    
    // Setup chart resizing for consistent appearance
    setupChartResizing();
});

function setupFileUploads() {
    $('.file-upload').each(function() {
        const $upload = $(this);
        const $input = $upload.find('input[type="file"]');
        const $area = $upload.find('.upload-area');
        const fileType = $input.data('type');
        
        // Click to browse
        $area.find('.browse-btn').click(function(e) {
            e.preventDefault();
            e.stopPropagation();
            $input.click();
        });
        
        // Drag and drop
        $upload.on('dragover', function(e) {
            e.preventDefault();
            $upload.addClass('dragover');
        });
        
        $upload.on('dragleave', function(e) {
            e.preventDefault();
            $upload.removeClass('dragover');
        });
        
        $upload.on('drop', function(e) {
            e.preventDefault();
            $upload.removeClass('dragover');
            const files = e.originalEvent.dataTransfer.files;
            if (files.length > 0) {
                handleFileUpload(files[0], fileType);
            }
        });
        
        // File input change
        $input.change(function() {
            console.log('File input changed');
            const file = this.files[0];
            if (file) {
                console.log('File selected:', file.name, 'Size:', file.size, 'Type:', file.type);
                handleFileUpload(file, fileType);
            } else {
                console.log('No file selected');
            }
        });
    });
    
    // Setup main upload zone
    $('.upload-zone').each(function() {
        const $upload = $(this);
        const $input = $upload.find('input[type="file"]');
        const $area = $upload.find('.upload-area-fullscreen');
        const fileType = $input.data('type');
        
        console.log('Setting up main upload zone:', fileType);
        
        // Click to browse
        $area.find('.browse-btn-large').click(function(e) {
            e.preventDefault();
            e.stopPropagation();
            $input.click();
        });
        
        // Drag and drop
        $upload.on('dragover', function(e) {
            e.preventDefault();
            $upload.addClass('dragover');
        });
        
        $upload.on('dragleave', function(e) {
            e.preventDefault();
            $upload.removeClass('dragover');
        });
        
        $upload.on('drop', function(e) {
            e.preventDefault();
            $upload.removeClass('dragover');
            const files = e.originalEvent.dataTransfer.files;
            if (files.length > 0) {
                console.log('File dropped on main upload:', files[0].name);
                handleFileUpload(files[0], fileType);
            }
        });
        
        // File input change
        $input.change(function() {
            console.log('Main upload file input changed');
            const file = this.files[0];
            if (file) {
                console.log('Main upload file selected:', file.name, 'Size:', file.size, 'Type:', file.type);
                handleFileUpload(file, fileType);
            } else {
                console.log('No main upload file selected');
            }
        });
    });
    
    // Setup sidebar file upload areas
    $('.file-upload-sidebar').each(function() {
        const $upload = $(this);
        const $input = $upload.find('input[type="file"]');
        const $area = $upload.find('.upload-area-sidebar');
        const fileType = $input.data('type');
        
        console.log('Setting up sidebar upload:', fileType);
        
        // Click to browse
        $area.find('.browse-btn-small').click(function(e) {
            e.preventDefault();
            e.stopPropagation();
            $input.click();
        });
        
        // Drag and drop
        $upload.on('dragover', function(e) {
            e.preventDefault();
            $upload.addClass('dragover');
        });
        
        $upload.on('dragleave', function(e) {
            e.preventDefault();
            $upload.removeClass('dragover');
        });
        
        $upload.on('drop', function(e) {
            e.preventDefault();
            $upload.removeClass('dragover');
            const files = e.originalEvent.dataTransfer.files;
            if (files.length > 0) {
                console.log('File dropped on sidebar:', files[0].name);
                handleFileUpload(files[0], fileType);
            }
        });
        
        // File input change
        $input.change(function() {
            console.log('Sidebar file input changed');
            const file = this.files[0];
            if (file) {
                console.log('Sidebar file selected:', file.name, 'Size:', file.size, 'Type:', file.type);
                handleFileUpload(file, fileType);
            } else {
                console.log('No sidebar file selected');
            }
        });
    });
}

// Setup KPI card click handlers for formula editing
function setupKPICardClickHandlers() {
    console.log('Setting up KPI card click handlers');
    
    // Add click handlers to all KPI cards with data-kpi attribute
    $('.kpi-card[data-kpi]').click(function() {
        const kpiType = $(this).data('kpi');
        console.log('KPI card clicked:', kpiType);
        openFormulaEditor(kpiType);
    });
}

function handleFileUpload(file, fileType) {
    console.log('Starting file upload:', file.name, 'Type:', fileType);
    
    const formData = new FormData();
    formData.append('file', file);
    formData.append('type', fileType);
    
    // Show loading state
    const $upload = $('#' + fileType + '-upload');
    const $text = $upload.find('.upload-text');
    const originalText = $text.text();
    $text.text('Uploading...');
    
    $.ajax({
        url: '/upload',
        type: 'POST',
        data: formData,
        processData: false,
        contentType: false,
        beforeSend: function() {
            console.log('Sending upload request...');
        },
        success: function(response) {
            console.log('Upload response:', response);
            if (response.success) {
                if (fileType === 'rec' && response.file_type === 'excel_placement_report') {
                    // Handle Excel placement report upload
                    updateUploadArea(fileType, file.name);
                    updateUploadStatus(fileType, response.message);
                    showProcessingStatus();
                    
                    // Store file path in session for processing
                    sessionStorage.setItem(fileType + '_file', response.file_path);
                    
                    // Automatically process the placement report
                    processPlacementReport();
                } else if (fileType === 'finance') {
                    // Handle finance Excel file upload
                    updateUploadArea(fileType, file.name);
                    sessionStorage.setItem(fileType + '_file', response.file_path);
                    
                    // Only process finance report for finance files
                    console.log('Processing finance file only - not recruitment data');
                    processFinanceReport();
                } else {
                    // Handle regular CSV/Excel files
                    showFilePreview(fileType, response.columns, response.preview);
                    updateUploadArea(fileType, file.name);
                    sessionStorage.setItem(fileType + '_file', response.file_path);
                    
                    // For regular recruitment files, automatically process the data
                    if (fileType === 'rec') {
                        processData();
                    }
                }
            } else {
                alert('Upload failed: ' + response.error);
                $text.text(originalText);
            }
        },
        error: function(xhr, status, error) {
            console.error('Upload error:', xhr.responseText);
            alert('Upload failed: ' + (xhr.responseJSON ? xhr.responseJSON.error : 'Please try again.'));
            $text.text(originalText);
        }
    });
}

function showFilePreview(fileType, columns, preview) {
    const mappingId = fileType + '-mapping';
    const previewId = fileType + '-preview';
    
    // Show mapping section
    $('#' + mappingId).show();
    
    // Update preview
    const $preview = $('#' + previewId);
    let previewHtml = '<table style="width: 100%; font-size: 11px;">';
    previewHtml += '<tr><th>Row</th>';
    columns.forEach(col => {
        previewHtml += '<th>' + col + '</th>';
    });
    previewHtml += '</tr>';
    
    preview.forEach((row, index) => {
        previewHtml += '<tr><td>' + (index + 1) + '</td>';
        columns.forEach(col => {
            previewHtml += '<td>' + (row[col] || '') + '</td>';
        });
        previewHtml += '</tr>';
    });
    previewHtml += '</table>';
    
    $preview.html(previewHtml);
    
    // Populate column selectors
    populateColumnSelectors(fileType, columns);
    
    // Hide no-data message if P&L data is uploaded
    if (fileType === 'pl') {
        $('#no-data-message').hide();
    }
    
    // Hide recruitment no-data message if recruitment data is uploaded
    if (fileType === 'rec') {
        $('#no-rec-data-message').hide();
    }
}

function updateUploadArea(fileType, fileName) {
    const $upload = $('#' + fileType + '-upload');
    const $text = $upload.find('.upload-text');
    $text.text('✓ ' + fileName + ' uploaded successfully');
    $upload.addClass('uploaded');
}

function updateUploadStatus(fileType, message) {
    const $status = $('#' + fileType + '-upload-status');
    $status.text(message).css('color', '#28a745');
}

function showProcessingStatus() {
    $('#no-rec-data-message').hide();
}

function processPlacementReport() {
    $.ajax({
        url: '/process_placement_report',
        type: 'POST',
        contentType: 'application/json',
        success: function(response) {
            if (response.success) {
                // Save to localStorage for persistence
                localStorage.setItem('recruitmentData', JSON.stringify({
                    kpis: response.kpis,
                    charts: response.charts,
                    processing_status: response.processing_status,
                    sheet1_data: response.sheet1_data,
                    sheet2_data: response.sheet2_data,
                    sheet3_data: response.sheet3_data
                }));
                
                updatePlacementKPIs(response.kpis);
                renderPlacementCharts(response.charts);
                
                // Hide upload area and show dashboard
                showDashboardAfterUpload();
            } else {
                alert('Failed to process placement report: ' + response.error);
            }
        },
        error: function(xhr, status, error) {
            console.error('Processing error:', xhr.responseText);
            alert('Failed to process placement report. Please try again.');
        }
    });
}

function showDashboardAfterUpload() {
    // Scroll to top when showing dashboard
    scrollToTop();
    
    // Hide the full-screen upload zone
    $('#initial-upload-section').hide();
    
    // Hide the no-data message
    $('#no-rec-data-message').hide();
    
    // Show only recruitment dashboard sections
    $('#recruitment-dashboard .section').show();
    
    // Add a smooth transition effect
    $('.dashboard-view').addClass('dashboard-loaded');
    
    // Show sidebar for recruitment dashboard now that we have data
    const dataSidebar = document.getElementById('data-sidebar');
    const mainContent = document.querySelector('.main-content');
    if (currentDashboard === 'recruitment') {
        dataSidebar.style.display = 'block';
        mainContent.classList.remove('finance-mode');
        mainContent.classList.add('recruitment-mode');
    }
    
    // Update Data Explorer with new recruitment data
    console.log('Updating Data Explorer with recruitment data...');
    loadDataExplorerData();
}

function toggleDataSidebar() {
    const sidebar = document.getElementById('data-sidebar');
    const mainContent = document.querySelector('.main-content');
    
    // On mobile, toggle visibility; on desktop, sidebar is always visible
    if (window.innerWidth <= 768) {
        if (sidebar.style.display === 'none' || sidebar.style.display === '') {
            sidebar.style.display = 'block';
            sidebar.classList.add('sidebar-open');
        } else {
            sidebar.style.display = 'none';
            sidebar.classList.remove('sidebar-open');
        }
    }
    // On desktop, do nothing - sidebar is always visible
}

function exportCurrentData() {
    // Trigger download of current data
    window.location.href = '/api/recruitment/export/dataset';
}

function resetDashboard() {
    if (confirm('Are you sure you want to reset the dashboard? This will clear all data.')) {
        // Clear server-side session data
        $.ajax({
            url: '/clear_session_data',
            type: 'POST',
            success: function() {
                console.log('Session data cleared');
            },
            error: function() {
                console.log('Error clearing session data');
            }
        });
        
        // Hide dashboard and show upload area
        $('#initial-upload-section').show();
        $('.section').hide();
        
        // Clear any stored data
        sessionStorage.removeItem('rec_file');
        
        // Reset the dashboard state
        $('.dashboard-view').removeClass('dashboard-loaded');
        
        // Show sidebar for recruitment dashboard (it should always be visible)
        if (currentDashboard === 'recruitment') {
            const dataSidebar = document.getElementById('data-sidebar');
            const mainContent = document.querySelector('.main-content');
            dataSidebar.style.display = 'block';
            mainContent.classList.add('recruitment-mode');
        }
    }
}


function updatePlacementKPIs(kpis) {
    console.log('=== UPDATING PLACEMENT KPIS ===');
    console.log('KPIs received:', kpis);
    
    if (kpis) {
        // Update KPI values with proper mapping
        $('#kpi-total-placements').text(kpis['Total Placements'] || '—');
        $('#kpi-total-terminations').text(kpis['Total Terminations'] || '—');
        $('#kpi-net-placements').text(kpis['Net Placements (Latest Month)'] || '—');
        $('#kpi-total-billables').text(kpis['Total Current Billables'] || '—');
        $('#kpi-w2-placements').text(kpis['W2 Placements'] || '—');
        $('#kpi-c2c-placements').text(kpis['C2C Placements'] || '—');
    }
}

function renderPlacementCharts(charts) {
    // Ensure we stay at the top when rendering charts
    setTimeout(scrollToTop, 100);
    
    console.log('=== RENDERING PLACEMENT CHARTS ===');
    console.log('Charts to render:', Object.keys(charts));
    
    Object.keys(charts).forEach(chartName => {
        let chartId = 'chart-' + chartName.replace('_', '-');
        
        // Handle special chart mappings
        const chartMapping = {
            'employment_types': 'chart-employment-types',
            'placement_metrics': 'chart-placement-metrics',
            'billables_trend': 'chart-billables-trend',
            'gross_margin': 'chart-gross-margin'
        };
        
        chartId = chartMapping[chartName] || chartId;
        
        console.log(`Looking for chart container: ${chartId}`);
        const $container = $('#' + chartId);
        console.log(`Found container:`, $container.length);
        
        if ($container.length > 0) {
            try {
                const chartData = charts[chartName];
                console.log(`Chart data for ${chartName}:`, chartData);
                
                // Validate chart data structure
                if (!chartData || !chartData.data || !chartData.data.labels) {
                    console.error(`Invalid chart data structure for ${chartName}:`, chartData);
                    return;
                }
                
                // Clear any existing canvas
                $container.empty();
                
                // Create new canvas element
                const canvas = $('<canvas>').attr('id', chartId + '-canvas')[0];
                $container.append(canvas);
                
                // Create Chart.js chart
                const ctx = canvas.getContext('2d');
                new Chart(ctx, chartData);
                
                console.log(`Successfully rendered chart: ${chartName}`);
            } catch (e) {
                console.error('Failed to render chart:', chartName, e);
                console.error('Chart data that failed:', charts[chartName]);
            }
        } else {
            console.warn(`Chart container not found: ${chartId}`);
        }
    });
}

function populateColumnSelectors(fileType, columns) {
    const selectors = getColumnSelectors(fileType);
    
    selectors.forEach(selector => {
        const $select = $('#' + fileType + '-' + selector);
        $select.empty();
        $select.append('<option value="">Select column...</option>');
        
        columns.forEach(col => {
            $select.append('<option value="' + col + '">' + col + '</option>');
        });
    });
}

function getColumnSelectors(fileType) {
    const selectors = {
        'pl': ['date-col', 'revenue-col', 'cogs-col', 'opex-col'],
        'bs': ['date-col', 'assets-col', 'liab-col', 'equity-col'],
        'rec': ['date-col', 'placements-col', 'revenue-col', 'margin-col'],
        'mg': ['date-col', 'amount-col', 'percent-col']
    };
    return selectors[fileType] || [];
}

function setupColumnMapping() {
    // Auto-select columns based on common patterns
    $('.select-field').change(function() {
        const fileType = $(this).attr('id').split('-')[0];
        autoSelectColumns(fileType);
    });
}

function autoSelectColumns(fileType) {
    const $selects = $('#' + fileType + '-mapping select');
    
    $selects.each(function() {
        const $select = $(this);
        const currentValue = $select.val();
        
        if (!currentValue) {
            const options = $select.find('option');
            options.each(function() {
                const optionText = $(this).text().toLowerCase();
                const optionValue = $(this).val();
                
                // Auto-select based on common patterns
                if (optionText.includes('date') || optionText.includes('month') || optionText.includes('period')) {
                    if ($select.attr('id').includes('date')) {
                        $select.val(optionValue);
                    }
                } else if (optionText.includes('revenue') || optionText.includes('sales')) {
                    if ($select.attr('id').includes('revenue')) {
                        $select.val(optionValue);
                    }
                } else if (optionText.includes('cogs') || optionText.includes('cost')) {
                    if ($select.attr('id').includes('cogs')) {
                        $select.val(optionValue);
                    }
                } else if (optionText.includes('expense') || optionText.includes('operat')) {
                    if ($select.attr('id').includes('opex')) {
                        $select.val(optionValue);
                    }
                }
            });
        }
    });
}

function processData() {
    const mappings = collectMappings();
    
    $.ajax({
        url: '/process',
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({ mappings: mappings }),
        success: function(response) {
            updateKPIs(response.kpis);
            renderCharts(response.charts);
        },
        error: function() {
            alert('Failed to process data. Please check your mappings.');
        }
    });
}

function collectMappings() {
    const mappings = {
        pl_map: {},
        bs_map: {},
        rec_map: {},
        mg_map: {}
    };
    
    // Collect P&L mappings
    if ($('#pl-mapping').is(':visible')) {
        mappings.pl_map = {
            date: $('#pl-date-col').val(),
            revenue: getSelectedValues('#pl-revenue-col'),
            cogs: getSelectedValues('#pl-cogs-col'),
            opex: getSelectedValues('#pl-opex-col')
        };
    }
    
    // Collect Balance Sheet mappings
    if ($('#bs-mapping').is(':visible')) {
        mappings.bs_map = {
            date: $('#bs-date-col').val(),
            assets: getSelectedValues('#bs-assets-col'),
            liabilities: getSelectedValues('#bs-liab-col'),
            equity: getSelectedValues('#bs-equity-col')
        };
    }
    
    // Collect Recruitment mappings
    if ($('#rec-mapping').is(':visible')) {
        mappings.rec_map = {
            date: $('#rec-date-col').val(),
            placements: $('#rec-placements-col').val(),
            revenue: $('#rec-revenue-col').val(),
            margin: $('#rec-margin-col').val()
        };
    }
    
    // Collect Margin mappings
    if ($('#mg-mapping').is(':visible')) {
        mappings.mg_map = {
            date: $('#mg-date-col').val(),
            margin_amount: $('#mg-amount-col').val(),
            margin_percent: $('#mg-percent-col').val()
        };
    }
    
    return mappings;
}

function getSelectedValues(selector) {
    const values = [];
    $(selector + ' option:selected').each(function() {
        if ($(this).val()) {
            values.push($(this).val());
        }
    });
    return values;
}

function updateKPIs(kpis) {
    Object.keys(kpis).forEach(key => {
        const kpiId = getKpiId(key);
        if (kpiId) {
            $('#' + kpiId).text(kpis[key]);
        }
    });
}

function getKpiId(kpiName) {
    const mapping = {
        'Revenue (last period)': 'kpi-revenue',
        'Gross Profit (last period)': 'kpi-gross-profit',
        'Net Income (last period)': 'kpi-net-income',
        'Assets − Liabilities (last)': 'kpi-assets-liab'
    };
    return mapping[kpiName];
}

function renderCharts(charts) {
    // Ensure we stay at the top when rendering charts
    setTimeout(scrollToTop, 100);
    
    Object.keys(charts).forEach(chartName => {
        let chartId = 'chart-' + chartName.replace('_', '-');
        
        // Handle special chart mappings for recruitment placement report
        if (chartName === 'employment_types') {
            chartId = 'chart-employment-types';
        } else if (chartName === 'placement_metrics') {
            chartId = 'chart-placement-metrics';
        }
        
        const $container = $('#' + chartId);
        
        if ($container.length > 0) {
            try {
                const chartData = charts[chartName];
                
                // Clear any existing canvas
                $container.empty();
                
                // Create new canvas element
                const canvas = $('<canvas>').attr('id', chartId + '-canvas')[0];
                $container.append(canvas);
                
                // Create Chart.js chart
                const ctx = canvas.getContext('2d');
                new Chart(ctx, chartData);
                
            } catch (e) {
                console.error('Failed to render chart:', chartName, e);
            }
        }
    });
}

function setupFullscreenDragDrop() {
    const fullscreenZone = document.querySelector('.fullscreen-upload-zone');
    const uploadArea = document.querySelector('.upload-area-fullscreen');
    const fileInput = document.querySelector('#rec-upload input[type="file"]');
    
    if (!fullscreenZone || !uploadArea || !fileInput) return;
    
    // Make the entire fullscreen zone draggable
    fullscreenZone.addEventListener('dragover', function(e) {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });
    
    fullscreenZone.addEventListener('dragleave', function(e) {
        e.preventDefault();
        // Only remove dragover if we're leaving the entire fullscreen zone
        if (!fullscreenZone.contains(e.relatedTarget)) {
            uploadArea.classList.remove('dragover');
        }
    });
    
    fullscreenZone.addEventListener('drop', function(e) {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFileUpload(files[0], 'rec');
        }
    });
    
    // Make the browse button work
    const browseBtn = document.querySelector('.browse-btn-large');
    
    if (browseBtn) {
        browseBtn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            fileInput.click();
        });
    }
    
    // File input change
    fileInput.addEventListener('change', function() {
        const file = this.files[0];
        if (file) {
            handleFileUpload(file, 'rec');
        }
    });
}

// Initialize upload area styling
$(document).ready(function() {
    // Add pointer-events: none to upload area contents to prevent interference with drag/drop
    $('.upload-area').css('pointer-events', 'none');
    $('.browse-btn').css('pointer-events', 'auto');
});

// Sidebar functionality
function setupSidebarFileUpload() {
    // Handle old sidebar uploads
    $('.file-upload-sidebar').each(function() {
        const $upload = $(this);
        const $input = $upload.find('input[type="file"]');
        const $area = $upload.find('.upload-area-sidebar');
        
        // Click to browse
        $area.find('.browse-btn-small').click(function(e) {
            e.preventDefault();
            e.stopPropagation();
            $input.click();
        });
        
        // Drag and drop
        $upload.on('dragover', function(e) {
            e.preventDefault();
            $upload.addClass('dragover');
        });
        
        $upload.on('dragleave', function(e) {
            e.preventDefault();
            $upload.removeClass('dragover');
        });
        
        $upload.on('drop', function(e) {
            e.preventDefault();
            $upload.removeClass('dragover');
            const files = e.originalEvent.dataTransfer.files;
            if (files.length > 0) {
                handleSidebarFileUpload(files[0]);
            }
        });
        
        // File input change
        $input.change(function() {
            const file = this.files[0];
            if (file) {
                handleSidebarFileUpload(file);
            }
        });
    });
    
    // Handle new navigation uploads
    $('.file-upload-nav').each(function() {
        const $upload = $(this);
        const $input = $upload.find('input[type="file"]');
        const $area = $upload.find('.upload-area-nav');
        const fileType = $input.attr('data-type');
        
        // Click to browse
        $area.find('.browse-btn-nav').click(function(e) {
            e.preventDefault();
            e.stopPropagation();
            $input.click();
        });
        
        // Drag and drop
        $upload.on('dragover', function(e) {
            e.preventDefault();
            $upload.addClass('dragover');
        });
        
        $upload.on('dragleave', function(e) {
            e.preventDefault();
            $upload.removeClass('dragover');
        });
        
        $upload.on('drop', function(e) {
            e.preventDefault();
            $upload.removeClass('dragover');
            const files = e.originalEvent.dataTransfer.files;
            if (files.length > 0) {
                handleNavFileUpload(files[0], fileType);
            }
        });
        
        // File input change
        $input.change(function() {
            const file = this.files[0];
            if (file) {
                handleNavFileUpload(file, fileType);
            }
        });
    });
}

function handleNavFileUpload(file, fileType) {
    console.log('=== NAVIGATION FILE UPLOAD ===');
    console.log('File:', file.name);
    console.log('Type:', fileType);
    
    const formData = new FormData();
    formData.append('file', file);
    formData.append('type', fileType);
    
    $.ajax({
        url: '/upload',
        type: 'POST',
        data: formData,
        processData: false,
        contentType: false,
        success: function(response) {
            console.log('Navigation upload success:', response);
            
            // Switch to appropriate dashboard based on file type
            if (fileType === 'finance') {
                switchDashboard('finance');
                // Process finance report
                setTimeout(() => {
                    processFinanceReport();
                }, 500);
            } else if (fileType === 'rec') {
                switchDashboard('recruitment');
                // Process recruitment report
                setTimeout(() => {
                    processPlacementReport();
                }, 500);
            }
            
            // Close sidebar after upload
            toggleSidebar();
        },
        error: function(xhr, status, error) {
            console.error('Navigation upload error:', xhr.responseText);
            alert('Upload failed: ' + (xhr.responseJSON?.error || error));
        }
    });
}

function handleSidebarFileUpload(file) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('type', 'rec');
    
    // Show loading state
    const $upload = $('#sidebar-rec-upload');
    const $text = $upload.find('.upload-text');
    const originalText = $text.text();
    $text.text('Uploading...');
    
    $.ajax({
        url: '/upload',
        type: 'POST',
        data: formData,
        processData: false,
        contentType: false,
        success: function(response) {
            if (response.success) {
                $text.text('✓ File uploaded successfully');
                $upload.addClass('uploaded');
                
                // Process the new file
                processPlacementReport();
            } else {
                alert('Upload failed: ' + response.error);
                $text.text(originalText);
            }
        },
        error: function(xhr, status, error) {
            console.error('Upload error:', xhr.responseText);
            alert('Upload failed: ' + (xhr.responseJSON ? xhr.responseJSON.error : 'Please try again.'));
            $text.text(originalText);
        }
    });
}

function addMonthlyData() {
    const formData = {
        month: $('#new-month').val(),
        tg_w2: parseInt($('#tg-w2').val()) || 0,
        tg_c2c: parseInt($('#tg-c2c').val()) || 0,
        tg_1099: parseInt($('#tg-1099').val()) || 0,
        tg_referral: parseInt($('#tg-referral').val()) || 0,
        vnst_w2: parseInt($('#vnst-w2').val()) || 0,
        vnst_sc: parseInt($('#vnst-sc').val()) || 0,
        new_placements: parseInt($('#new-placements').val()) || 0,
        terminations: parseInt($('#terminations').val()) || 0
    };
    
    if (!formData.month) {
        alert('Please select a month');
        return;
    }
    
    $.ajax({
        url: '/api/recruitment/add_month',
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify(formData),
        success: function(response) {
            if (response.success) {
                alert('Monthly data added successfully!');
                
                // Clear form
                $('#monthly-data-form')[0].reset();
                
                // Refresh the dashboard
                processPlacementReport();
            } else {
                alert('Failed to add monthly data: ' + response.error);
            }
        },
        error: function(xhr, status, error) {
            console.error('Add monthly data error:', xhr.responseText);
            alert('Failed to add monthly data. Please try again.');
        }
    });
}

function setupChartResizing() {
    // Handle window resize to maintain chart consistency with Chart.js
    let resizeTimeout;
    $(window).on('resize', function() {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(function() {
            // Chart.js automatically handles responsive resizing
            // No manual intervention needed
            Chart.helpers.each(Chart.instances, function(instance) {
                instance.resize();
            });
        }, 250); // Debounce resize events
    });
}

function formatCurrency(value) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(value);
}

function formatPercentage(value) {
    return new Intl.NumberFormat('en-US', {
        style: 'percent',
        minimumFractionDigits: 1,
        maximumFractionDigits: 1
    }).format(value / 100);
}
// New Drag-and-Drop Formula Editor Functions
let currentEditingKPI = null;
let availableVariables = [];
let formulaCanvas = null;
let formulaText = ''; // Track the formula as text

function openFormulaEditor(kpiKey) {
    console.log('Opening formula editor for:', kpiKey);
    currentEditingKPI = kpiKey;
    
    // Show modal
    $('#formula-editor-modal').show();
    
    // Set title
    $('#formula-editor-title').text(`Edit ${kpiKey.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())} Formula`);
    
    // Load available variables
    loadAvailableVariables();
    
    // Load current formula
    loadCurrentFormula(kpiKey);
    
    // Setup hybrid input (text + drag & drop)
    setupHybridFormulaInput();
}

function closeFormulaEditor() {
    $('#formula-editor-modal').hide();
    currentEditingKPI = null;
    formulaCanvas = null;
}

function loadAvailableVariables() {
    console.log('Loading available variables...');
    
    // Try to get finance data from localStorage first
    const financeDataStr = localStorage.getItem('financeData');
    let financeData = null;
    
    if (financeDataStr) {
        try {
            financeData = JSON.parse(financeDataStr);
            console.log('Loaded finance data from localStorage:', financeData);
        } catch (e) {
            console.error('Error parsing finance data:', e);
        }
    }
    
    // Fallback to window.financeData
    if (!financeData && window.financeData) {
        financeData = window.financeData;
        console.log('Using window.financeData:', financeData);
    }
    
    if (!financeData || !financeData.processed_data) {
        console.log('No finance data available for variables');
        availableVariables = [];
        populateVariablesGrid();
        return;
    }
    
    const variables = [];
    const processedData = financeData.processed_data;
    
    console.log('Processing data for variables:', processedData);
    
    // Extract business unit variables
    if (processedData.business_units) {
        Object.keys(processedData.business_units).forEach(unitName => {
            const unitData = processedData.business_units[unitName];
            
            if (unitData.revenue && unitData.revenue.length > 0) {
                const totalRevenue = unitData.revenue.reduce((sum, val) => sum + val, 0);
                variables.push({
                    name: `${unitName} Revenue`,
                    value: totalRevenue,
                    type: 'revenue'
                });
            }
            if (unitData.gross_income && unitData.gross_income.length > 0) {
                const totalGrossIncome = unitData.gross_income.reduce((sum, val) => sum + val, 0);
                variables.push({
                    name: `${unitName} Gross Income`,
                    value: totalGrossIncome,
                    type: 'income'
                });
            }
            if (unitData.net_income && unitData.net_income.length > 0) {
                const totalNetIncome = unitData.net_income.reduce((sum, val) => sum + val, 0);
                variables.push({
                    name: `${unitName} Net Income`,
                    value: totalNetIncome,
                    type: 'income'
                });
            }
        });
    }
    
    // Extract P&L variables
    if (processedData.monthly_data) {
        Object.keys(processedData.monthly_data).forEach(companyName => {
            const companyData = processedData.monthly_data[companyName];
            
            if (companyData.total_income && companyData.total_income.length > 0) {
                const totalIncome = companyData.total_income.reduce((sum, val) => sum + val, 0);
                variables.push({
                    name: `${companyName} Total Income`,
                    value: totalIncome,
                    type: 'income'
                });
            }
            if (companyData.total_expense && companyData.total_expense.length > 0) {
                const totalExpenses = companyData.total_expense.reduce((sum, val) => sum + val, 0);
                variables.push({
                    name: `${companyName} Total Expenses`,
                    value: totalExpenses,
                    type: 'expense'
                });
            }
        });
    }
    
    availableVariables = variables;
    console.log('Available variables:', variables);
    
    // Populate variables grid
    populateVariablesGrid();
}

function populateVariablesGrid() {
    const grid = $('#variables-grid');
    grid.empty();
    
    availableVariables.forEach(variable => {
        const variableElement = $(`
            <div class="variable-item" draggable="true" data-variable="${variable.name}" data-value="${variable.value}">
                <div class="variable-name">${variable.name}</div>
                <div class="variable-value">$${formatNumber(variable.value)}</div>
            </div>
        `);
        
        grid.append(variableElement);
    });
}

function loadCurrentFormula(kpiKey) {
    console.log('Loading current formula for:', kpiKey);
    
    // Get current formula from localStorage
    const customFormulas = JSON.parse(localStorage.getItem('customFormulas') || '{}');
    const currentFormula = customFormulas[kpiKey] || getDefaultFormula(kpiKey);
    
    console.log('Current formula:', currentFormula);
    
    // Set the formula text in the input
    formulaText = currentFormula;
    const input = $('#formula-canvas .formula-input');
    input.text(currentFormula);
    
    updateFormulaPreview();
}

function getDefaultFormula(kpiKey) {
    const defaultFormulas = {
        'total_revenue': 'Direct Hire Revenue + Services Revenue + IT Staffing Revenue',
        'total_expenses': 'Direct Hire Expenses + Services Expenses + IT Staffing Expenses',
        'total_net_income': 'Total Revenue - Total Expenses',
        'profit_margin': '(Total Net Income / Total Revenue) * 100',
        'avg_monthly_revenue': 'Total Revenue / 8',
        'avg_monthly_net_income': 'Total Net Income / 8'
    };
    
    return defaultFormulas[kpiKey] || '';
}

function parseFormulaToCanvas(formula) {
    const canvas = $('#formula-canvas');
    canvas.empty();
    
    if (!formula) {
        canvas.append('<div class="formula-placeholder">Drag variables here to build your formula</div>');
        return;
    }
    
    // Simple parsing - split by operators and create elements
    const parts = formula.split(/([+\-*/()])/);
    
    parts.forEach(part => {
        if (part.trim()) {
            if (['+', '-', '*', '/', '(', ')'].includes(part)) {
                // Operator
                canvas.append(`<span class="formula-operator">${part}</span>`);
            } else {
                // Variable
                const variable = availableVariables.find(v => v.name === part.trim());
                if (variable) {
                    canvas.append(`<span class="formula-item" data-variable="${variable.name}">${variable.name}</span>`);
                } else {
                    canvas.append(`<span class="formula-item">${part}</span>`);
                }
            }
        }
    });
    
    updateFormulaPreview();
}

function setupHybridFormulaInput() {
    const canvas = $('#formula-canvas');
    
    // Create a contenteditable div for text input
    canvas.html('<div class="formula-input" contenteditable="true" spellcheck="false">Type your formula here or drag variables...</div>');
    
    const input = canvas.find('.formula-input');
    
    // Handle text input with autocomplete
    input.on('input', function() {
        formulaText = $(this).text();
        updateFormulaPreview();
        handleAutocomplete();
    });
    
    // Handle key events
    input.on('keydown', function(e) {
        // Handle backspace, delete, arrow keys
        if (e.key === 'Backspace' || e.key === 'Delete') {
            setTimeout(() => {
                formulaText = $(this).text();
                updateFormulaPreview();
            }, 10);
        }
        
        // Handle Enter key
        if (e.key === 'Enter') {
            e.preventDefault();
            insertOperator('+');
        }
    });
    
    // Handle paste
    input.on('paste', function(e) {
        e.preventDefault();
        const text = (e.originalEvent.clipboardData || window.clipboardData).getData('text');
        document.execCommand('insertText', false, text);
        formulaText = $(this).text();
        updateFormulaPreview();
    });
    
    // Make canvas a drop target for variables
    canvas.on('dragover', function(e) {
        e.preventDefault();
        $(this).addClass('drag-over');
    });
    
    canvas.on('dragleave', function() {
        $(this).removeClass('drag-over');
    });
    
    canvas.on('drop', function(e) {
        e.preventDefault();
        $(this).removeClass('drag-over');
        
        const variableName = e.originalEvent.dataTransfer.getData('text/plain');
        insertVariableAtCursor(variableName);
    });
    
    // Make variables draggable
    $('.variable-item').on('dragstart', function(e) {
        e.originalEvent.dataTransfer.setData('text/plain', $(this).data('variable'));
        $(this).addClass('dragging');
    });
    
    $('.variable-item').on('dragend', function() {
        $(this).removeClass('dragging');
    });
}

function insertVariableAtCursor(variableName) {
    const input = $('#formula-canvas .formula-input');
    const selection = window.getSelection();
    
    if (selection.rangeCount > 0) {
        const range = selection.getRangeAt(0);
        range.deleteContents();
        range.insertNode(document.createTextNode(variableName));
        range.collapse(false);
        selection.removeAllRanges();
        selection.addRange(range);
    } else {
        // If no selection, append to end
        input.append(variableName);
    }
    
    formulaText = input.text();
    updateFormulaPreview();
}

function insertOperator(operator) {
    const input = $('#formula-canvas .formula-input');
    const selection = window.getSelection();
    
    if (selection.rangeCount > 0) {
        const range = selection.getRangeAt(0);
        range.deleteContents();
        range.insertNode(document.createTextNode(operator));
        range.collapse(false);
        selection.removeAllRanges();
        selection.addRange(range);
    } else {
        input.append(operator);
    }
    
    formulaText = input.text();
    updateFormulaPreview();
}

function handleAutocomplete() {
    // Simple autocomplete - highlight known variables
    const input = $('#formula-canvas .formula-input');
    const text = input.text();
    
    // Reset styling
    input.find('span').contents().unwrap();
    
    // Highlight variables
    availableVariables.forEach(variable => {
        const regex = new RegExp(`\\b${variable.name}\\b`, 'g');
        if (text.match(regex)) {
            // This is a simplified approach - in a real implementation,
            // you'd want to preserve cursor position and selection
            input.html(text.replace(regex, `<span class="variable-highlight">${variable.name}</span>`));
        }
    });
}

function addVariableToCanvas(variableName) {
    const canvas = $('#formula-canvas');
    const placeholder = canvas.find('.formula-placeholder');
    
    if (placeholder.length > 0) {
        placeholder.remove();
    }
    
    const variable = availableVariables.find(v => v.name === variableName);
    if (variable) {
        canvas.append(`<span class="formula-item" data-variable="${variable.name}">${variable.name}</span>`);
        updateFormulaPreview();
    }
}

function updateFormulaPreview() {
    const canvas = $('#formula-canvas');
    const formulaText = canvas.text().trim();
    
    $('#formula-preview').text('= ' + formulaText);
    
    // Calculate result
    try {
        const result = evaluateFormula(formulaText, availableVariables);
        $('#formula-result').text('$' + formatNumber(result));
    } catch (error) {
        console.error('Error calculating formula result:', error);
        $('#formula-result').text('Error');
    }
}

function evaluateFormula(formulaText, variables) {
    let evaluatedFormula = formulaText;
    
    // Replace variable names with values
    variables.forEach(variable => {
        const regex = new RegExp(variable.name.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'g');
        evaluatedFormula = evaluatedFormula.replace(regex, variable.value);
    });
    
    // Evaluate the mathematical expression
    return eval(evaluatedFormula);
}

function resetFormula() {
    console.log('Resetting formula to default');
    
    if (currentEditingKPI) {
        const defaultFormula = getDefaultFormula(currentEditingKPI);
        parseFormulaToCanvas(defaultFormula);
    }
}

function saveFormula() {
    console.log('Saving formula for:', currentEditingKPI);
    
    if (!currentEditingKPI) {
        console.error('No KPI selected for saving');
        return;
    }
    
    // Get current formula from canvas
    const canvas = $('#formula-canvas');
    const formulaText = canvas.text().trim();
    
    console.log('Saving formula:', formulaText);
    
    // Save to localStorage
    const customFormulas = JSON.parse(localStorage.getItem('customFormulas') || '{}');
    customFormulas[currentEditingKPI] = formulaText;
    localStorage.setItem('customFormulas', JSON.stringify(customFormulas));
    
    // Update KPI display
    updateKPIFormulaDisplay(currentEditingKPI, formulaText);
    
    // Recalculate KPIs
    recalculateFinanceKPIs();
    
    // Close modal
    closeFormulaEditor();
    
    showNotification('Formula saved successfully!', 'success');
}

function updateKPIFormulaDisplay(kpiKey, formula) {
    const formulaElement = $(`#formula-${kpiKey.replace(/_/g, '-')}`);
    if (formulaElement.length > 0) {
        formulaElement.text(formula || 'Click to edit');
    }
}

function formatNumber(num) {
    return new Intl.NumberFormat('en-US', {
        minimumFractionDigits: 0,
        maximumFractionDigits: 2
    }).format(num);
}


// Operator and Formula Management Functions
function addOperator(operator) {
    console.log('Adding operator:', operator);
    insertOperator(operator);
}

function deleteLastItem() {
    console.log('Deleting last item');
    
    const input = $('#formula-canvas .formula-input');
    const text = input.text();
    
    if (text.length > 0) {
        input.text(text.slice(0, -1));
        formulaText = input.text();
        updateFormulaPreview();
    }
}

function clearFormula() {
    console.log('Clearing formula');
    
    const input = $('#formula-canvas .formula-input');
    input.text('');
    formulaText = '';
    updateFormulaPreview();
}

// Make Financial Summary cards clickable
function makeKPICardsClickable() {
    // Add click handlers to KPI cards
    $('.kpi-card').each(function() {
        const card = $(this);
        const kpiKey = card.data('kpi');
        
        if (kpiKey) {
            card.addClass('clickable-kpi');
            card.on('click', function() {
                console.log('Clicked KPI card:', kpiKey);
                openFormulaEditor(kpiKey);
            });
        }
    });
}

// Update the existing addVariableToCanvas function to handle operators better
function addVariableToCanvas(variableName) {
    const canvas = $('#formula-canvas');
    const placeholder = canvas.find('.formula-placeholder');
    
    if (placeholder.length > 0) {
        placeholder.remove();
    }
    
    const variable = availableVariables.find(v => v.name === variableName);
    if (variable) {
        canvas.append(`<span class="formula-item" data-variable="${variable.name}">${variable.name}</span>`);
        updateFormulaPreview();
    }
}

// Enhanced formula preview with better parsing
function updateFormulaPreview() {
    const text = formulaText || $('#formula-canvas .formula-input').text();
    
    $('#formula-preview').text('= ' + text);
    
    // Calculate result
    try {
        const result = evaluateFormula(text, availableVariables);
        $('#formula-result').text('$' + formatNumber(result));
    } catch (error) {
        console.error('Error calculating formula result:', error);
        $('#formula-result').text('Error');
    }
}

// Enhanced formula parsing for canvas
function parseFormulaToCanvas(formula) {
    const canvas = $('#formula-canvas');
    canvas.empty();
    
    if (!formula) {
        canvas.append('<div class="formula-placeholder">Drag variables here to build your formula</div>');
        return;
    }
    
    // Better parsing - handle spaces and multiple operators
    const parts = formula.split(/(\s*[+\-*/()]\s*)/);
    
    parts.forEach(part => {
        const trimmedPart = part.trim();
        if (trimmedPart) {
            if (['+', '-', '*', '/', '(', ')'].includes(trimmedPart)) {
                // Operator
                canvas.append(`<span class="formula-operator" data-operator="${trimmedPart}">${trimmedPart}</span>`);
            } else {
                // Variable
                const variable = availableVariables.find(v => v.name === trimmedPart);
                if (variable) {
                    canvas.append(`<span class="formula-item" data-variable="${variable.name}">${variable.name}</span>`);
                } else {
                    canvas.append(`<span class="formula-item">${trimmedPart}</span>`);
                }
            }
        }
    });
    
    updateFormulaPreview();
}

// Enhanced save formula function
function saveFormula() {
    console.log('Saving formula for:', currentEditingKPI);
    
    if (!currentEditingKPI) {
        console.error('No KPI selected for saving');
        return;
    }
    
    // Get current formula from text input
    const text = formulaText || $('#formula-canvas .formula-input').text();
    
    console.log('Saving formula:', text);
    
    // Save to localStorage
    const customFormulas = JSON.parse(localStorage.getItem('customFormulas') || '{}');
    customFormulas[currentEditingKPI] = text;
    localStorage.setItem('customFormulas', JSON.stringify(customFormulas));
    
    // Update KPI display
    updateKPIFormulaDisplay(currentEditingKPI, formulaText);
    
    // Recalculate KPIs
    recalculateFinanceKPIs();
    
    // Close modal
    closeFormulaEditor();
    
    showNotification('Formula saved successfully!', 'success');
}

// Initialize clickable KPI cards when page loads
$(document).ready(function() {
    // Make KPI cards clickable after a short delay to ensure they're rendered
    setTimeout(makeKPICardsClickable, 1000);
});
