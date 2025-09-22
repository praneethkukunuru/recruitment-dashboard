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
    $.ajax({
        url: '/check_existing_data',
        type: 'GET',
        success: function(response) {
            console.log('Check existing data response:', response);
            if (response.has_data) {
                console.log('Found existing data, restoring dashboard...');
                restoreDashboardFromData(response);
            } else {
                console.log('No existing data found');
            }
        },
        error: function(xhr, status, error) {
            console.log('No existing data found or error checking:', error);
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
                updateFinanceKPIs(response.kpis);
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
    
    // Show dashboard sections (no upload areas to hide in finance dashboard)
    console.log('Showing sections...');
    $('.section').show();
    
    console.log('Finance dashboard UI update complete');
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
            }
        } else {
            console.warn(`Chart container not found: ${chartId}`);
        }
    });
}

// Restore dashboard from existing data
function restoreDashboardFromData(response) {
    console.log('=== RESTORING DASHBOARD FROM DATA ===');
    console.log('Response:', response);
    
    // Handle recruitment data
    if (response.has_recruitment_data && response.recruitment_data) {
        console.log('Restoring recruitment data...');
        // Switch to recruitment dashboard
        switchDashboard('recruitment');
        
        const data = response.recruitment_data;
        
        // Update KPIs
        if (data.kpis) {
            updatePlacementKPIs(data.kpis);
        }
        
        // Render charts
        if (data.charts) {
            renderPlacementCharts(data.charts);
        }
        
        // Show the dashboard (hide upload screen)
        showDashboardAfterUpload();
    }
    
    // Handle finance data
    if (response.has_finance_data && response.finance_data) {
        console.log('Restoring finance data...');
        // Switch to finance dashboard
        switchDashboard('finance');
        
        const data = response.finance_data;
        
        // Update KPIs
        if (data.kpis) {
            updateFinanceKPIs(data.kpis);
        }
        
        // Render charts
        if (data.charts) {
            renderFinanceCharts(data.charts);
        }
        
        // Show the dashboard (hide upload screen)
        showFinanceDashboardAfterUpload();
    }
    
    // Mark upload areas as having existing data
    markUploadAreasWithExistingData();
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
    
    // Check for existing data on page load
    checkForExistingData();
    
    // File upload handling
    setupFileUploads();
    
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
                    
                    // Automatically process the finance report
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
    
    // Show the KPI and chart sections
    $('.section').show();
    
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
        
        // Hide sidebar when resetting recruitment dashboard
        if (currentDashboard === 'recruitment') {
            const dataSidebar = document.getElementById('data-sidebar');
            const mainContent = document.querySelector('.main-content');
            dataSidebar.style.display = 'none';
            mainContent.classList.remove('finance-mode', 'recruitment-mode');
        }
    }
}


function updatePlacementKPIs(kpis) {
    const kpiMapping = {
        'Total Current Billables': 'kpi-total-billables',
        'W2 Placements': 'kpi-w2-count',
        'Net Placements (Latest Month)': 'kpi-net-placements',
        'Gross Margin Total': 'kpi-gross-margin'
    };
    
    Object.keys(kpis).forEach(key => {
        const kpiId = kpiMapping[key];
        if (kpiId) {
            $('#' + kpiId).text(kpis[key]);
        }
    });
}

function renderPlacementCharts(charts) {
    // Ensure we stay at the top when rendering charts
    setTimeout(scrollToTop, 100);
    
    Object.keys(charts).forEach(chartName => {
        let chartId = 'chart-' + chartName.replace('_', '-');
        
        // Handle special chart mappings
        const chartMapping = {
            'employment_types': 'chart-employment-types',
            'placement_metrics': 'chart-placement-metrics',
            'billables_trend': 'chart-billables-trend',
            'direct_hire': 'chart-direct-hire',
            'services': 'chart-services',
            'it_staffing': 'chart-it-staffing'
        };
        
        chartId = chartMapping[chartName] || chartId;
        
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