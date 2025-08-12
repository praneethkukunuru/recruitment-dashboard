// Dashboard JavaScript functionality

$(document).ready(function() {
    // File upload handling
    setupFileUploads();
    
    // Column mapping handling
    setupColumnMapping();
    
    // Process data button
    $('#download-report').click(function() {
        processData();
    });
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
            const file = this.files[0];
            if (file) {
                handleFileUpload(file, fileType);
            }
        });
    });
}

function handleFileUpload(file, fileType) {
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
            if (response.success) {
                showFilePreview(fileType, response.columns, response.preview);
                updateUploadArea(fileType, file.name);
            } else {
                alert('Upload failed: ' + response.error);
            }
        },
        error: function() {
            alert('Upload failed. Please try again.');
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
}

function updateUploadArea(fileType, fileName) {
    const $upload = $('#' + fileType + '-upload');
    const $text = $upload.find('.upload-text');
    $text.text('File uploaded: ' + fileName);
    $upload.addClass('uploaded');
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
    Object.keys(charts).forEach(chartName => {
        const chartId = 'chart-' + chartName.replace('_', '-');
        const $container = $('#' + chartId);
        
        if ($container.length > 0) {
            try {
                const chartData = JSON.parse(charts[chartName]);
                Plotly.newPlot(chartId, chartData.data, chartData.layout, {
                    responsive: true,
                    displayModeBar: false
                });
            } catch (e) {
                console.error('Failed to render chart:', chartName, e);
            }
        }
    });
}

// Add some CSS for drag and drop states
$('<style>')
    .prop('type', 'text/css')
    .html(`
        .file-upload.dragover {
            border-color: #007bff;
            background-color: #f8f9ff;
        }
        .file-upload.uploaded {
            border-color: #28a745;
            background-color: #f8fff9;
        }
        .file-upload.uploaded .upload-text {
            color: #28a745;
            font-weight: 600;
        }
    `)
    .appendTo('head'); 