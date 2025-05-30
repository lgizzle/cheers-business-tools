/**
 * Multi-Product Buying Calculator Application
 * Simplified version with core functionality only
 */

// Execute when DOM is fully loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded - initializing calculator app');

    // Helper function to format numbers with comma separators
    function formatCurrency(amount) {
        return '$' + amount.toLocaleString('en-US', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
    }

    // Simple state management
    let products = [];
    let selectedScenarioName = null;
    let defaultProductAdded = false;

    // GLOBAL optimization history to prevent clearing
    let globalOptimizationHistory = [];

    // Direct DOM element references
    const addProductBtn = document.getElementById('addProductRow');
    const productsTableBody = document.getElementById('productsTableBody');
    const calculateBtn = document.getElementById('calculateBtn');
    const loadScenarioBtn = document.getElementById('loadScenarioBtn');
    const compactToggle = document.getElementById('compactViewToggle');
    const productsInputTable = document.getElementById('productsInputTable');
    const resultsTableSection = document.getElementById('resultsTableSection');

    // Set up compact view toggle
    if (compactToggle && productsInputTable) {
        // Restore saved preference
        const savedCompactView = localStorage.getItem('compactViewPreference') === 'true';
        compactToggle.checked = savedCompactView;
        if (savedCompactView) {
            productsInputTable.classList.add('compact');
        }

        // Add event listener for toggle
        compactToggle.addEventListener('change', function() {
            const isCompact = this.checked;
            productsInputTable.classList.toggle('compact', isCompact);
            localStorage.setItem('compactViewPreference', isCompact);

            console.log('Compact view toggled:', isCompact);
        });
    }

    // Set up event listeners
    if (addProductBtn) {
        console.log('Add Product button found:', addProductBtn);
        addProductBtn.addEventListener('click', handleAddProduct);
    } else {
        console.error('Add Product button not found!');
    }

    if (calculateBtn) {
        calculateBtn.addEventListener('click', handleCalculate);
    }

    // Auto Allocation button event listener
    const autoAllocationBtn = document.getElementById('autoAllocationBtn');
    if (autoAllocationBtn) {
        autoAllocationBtn.addEventListener('click', handleAutoAllocation);
    }

    // Export to Excel button event listener
    const exportBtn = document.getElementById('exportBtn');
    if (exportBtn) {
        exportBtn.addEventListener('click', handleExportToExcel);
    }

    // Deal size validation - monitor changes to deal size
    const dealSizeInput = document.getElementById('dealSizeCases');
    if (dealSizeInput) {
        dealSizeInput.addEventListener('input', validateBulkCasesTotals);

        // ✅ ADD: Also trigger validation on page load if deal size already has a value
        if (dealSizeInput.value) {
            setTimeout(() => validateBulkCasesTotals(), 200);
        }
    }

    // Event delegation to monitor manual changes to bulk case inputs
    // Clear optimization history when user manually modifies allocations
    if (productsTableBody) {
        productsTableBody.addEventListener('input', function(event) {
            if (event.target.classList.contains('product-bulk-cases')) {
                // Validate bulk cases totals when any bulk case input changes
                validateBulkCasesTotals();

                // Only clear history if we actually have optimization history
                if (globalOptimizationHistory.length > 0) {
                    console.log('Manual bulk case change detected - clearing optimization history');
                    globalOptimizationHistory = [];
                    updateOptimizationHistory([]);

                    // Remove the clear history button since history is now empty
                    const clearHistoryBtn = document.querySelector('.clear-history-btn');
                    if (clearHistoryBtn) {
                        clearHistoryBtn.remove();
                    }
                }
            }
        });
    }

    if (loadScenarioBtn) {
        loadScenarioBtn.addEventListener('click', function() {
            // Check if we're currently viewing scenario details
            const scenarioDetailsName = document.getElementById('scenarioDetailName');
            if (scenarioDetailsName && scenarioDetailsName.textContent) {
                // If we have scenario details displayed, use that name
                loadScenarioToCalculator(scenarioDetailsName.textContent);
            } else if (selectedScenarioName) {
                // Fall back to the selected scenario name if available
                loadScenarioToCalculator(selectedScenarioName);
            } else {
                alert('No scenario selected. Please select a scenario first.');
            }
        });
    }

    // Add a product row to the table
    function handleAddProduct() {
        console.log('Add Product button clicked');

        // Create a new row
        const newRow = document.createElement('tr');

        // Set the row HTML for input table only
        newRow.innerHTML = `
            <td><input type="text" class="form-control product-name" value="Test Product" required></td>
            <td><input type="number" class="form-control product-small-price" min="0.01" step="0.01" value="45.99" required></td>
            <td><input type="number" class="form-control product-bulk-price" min="0.01" step="0.01" value="39.99" required></td>
            <td class="detail-column"><input type="number" class="form-control product-cases-on-hand" min="0" value="10" required></td>
            <td class="detail-column"><input type="number" class="form-control product-annual-cases" min="1" value="60" required></td>
            <td class="detail-column"><input type="number" class="form-control product-bottles-per-case" min="1" value="12" required></td>
            <td><input type="number" class="form-control product-bulk-cases" min="0" placeholder="Auto-calculated"></td>
            <td>
                <button class="btn btn-sm btn-danger remove-product">
                    <i class="fas fa-trash"></i>
                </button>
            </td>
        `;

        // Add remove functionality
        const removeBtn = newRow.querySelector('.remove-product');
        if (removeBtn) {
            removeBtn.addEventListener('click', function() {
                if (productsTableBody.contains(newRow)) {
                    productsTableBody.removeChild(newRow);
                    // Trigger validation after removing product
                    validateBulkCasesTotals();
                }
            });
        }

        // Add the row to the input table
        if (productsTableBody) {
            console.log('Adding row to products input table');
            productsTableBody.appendChild(newRow);

            // Trigger validation after adding product (in case there are existing bulk case values)
            validateBulkCasesTotals();
        } else {
            console.error('Products table body not found!');
        }
    }

    // Handle calculate button click
    function handleCalculate() {
        console.log('Calculate button clicked');
        // Collect product data
        const rows = productsTableBody.querySelectorAll('tr:not(#productRowTemplate):not(#totalRow)');
        products = [];

        rows.forEach((row, index) => {
            const product = {
                product_name: row.querySelector('.product-name').value,
                current_price: parseFloat(row.querySelector('.product-small-price').value),
                bulk_price: parseFloat(row.querySelector('.product-bulk-price').value),
                on_hand: parseInt(row.querySelector('.product-cases-on-hand').value),
                annual_cases: parseInt(row.querySelector('.product-annual-cases').value) || 1,
                bottles_per_case: parseInt(row.querySelector('.product-bottles-per-case').value),
                bulk_quantity: parseInt(row.querySelector('.product-bulk-cases').value) || 0
            };
            products.push(product);
        });

        console.log('Collected products (calculation payload):', products);

        // Basic validation
        if (products.length === 0) {
            alert('Please add at least one product');
            return;
        }

                        // New: Check for annual cases > 0
        for (const product of products) {
            if (product.annual_cases <= 0) {
                alert('Annual cases must be greater than zero for all products.');
                return;
            }
        }

        // Get parameters
        const smallDealCases = parseInt(document.getElementById('smallDealCases').value);
        const dealSizeCases = parseInt(document.getElementById('dealSizeCases').value);
        const minDaysStock = parseInt(document.getElementById('minDaysStock').value);
        const paymentTermsDays = parseInt(document.getElementById('paymentTermsDays').value);
        const iterations = document.getElementById('iterations').value;
        const params = {
            // Backend validation keys
            small_deal_minimum: smallDealCases,
            bulk_deal_minimum: dealSizeCases,
            payment_terms: paymentTermsDays,
            min_days_stock: minDaysStock,
            // Calculation logic keys
            smallDealCases: smallDealCases,
            dealSizeCases: dealSizeCases,
            minDaysStock: minDaysStock,
            paymentTermsDays: paymentTermsDays,
            iterations: iterations
        };

        console.log('Calculation parameters:', params);

        // Make API call to calculate
        fetch('/api/calculate-multi-product-deal', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                parameters: params,
                products: products
            })
        })
        .then(response => response.json())
        .then(data => {
            console.log('Calculation results:', data);
            if (data.success) {
                updateResults(data.results);
            } else {
                alert('Error calculating results: ' + (data.error || 'Unknown error'));
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error calculating results: ' + error.message);
        });
    }

    // Update the UI with calculation results
    function updateResults(results) {
        // Store results globally for use in other functions
        window.lastResults = results;

        // Show the results table section
        if (resultsTableSection) {
            resultsTableSection.style.display = 'block';
        }

        // Clear and populate results table
        const resultsTableBody = document.getElementById('resultsTableBody');
        const resultsTotalRow = document.getElementById('resultsTotalRow');

        if (resultsTableBody) {
            // Clear existing results (except totals row)
            const existingRows = resultsTableBody.querySelectorAll('tr:not(#resultsTotalRow)');
            existingRows.forEach(row => row.remove());
        }

        // Update each product's bulk cases in input table AND populate results table
        let totalSmallDealCases = 0;
        let totalBulkCases = 0;
        let totalCasesAfterPurchase = 0;

        results.products.forEach((product, index) => {
            const inputRows = productsTableBody.querySelectorAll('tr:not(#productRowTemplate)');
            if (index < inputRows.length) {
                const inputRow = inputRows[index];

                // Update bulk cases in input table
                const bulkCasesInput = inputRow.querySelector('.product-bulk-cases');
                if (bulkCasesInput) {
                    bulkCasesInput.value = product.bulk_quantity || 0;
                }

                // Get values for results table
                const productName = inputRow.querySelector('.product-name').value;
                const onHandCases = parseInt(inputRow.querySelector('.product-cases-on-hand').value) || 0;
                const bulkCases = product.bulk_quantity || 0;
                const casesAfterPurchase = onHandCases + bulkCases;

                // Add to totals
                if (product.metrics) {
                    totalSmallDealCases += Math.round(product.metrics.smallDealCases || 0);
                }
                totalBulkCases += bulkCases;
                totalCasesAfterPurchase += casesAfterPurchase;

                // Create results table row
                if (resultsTableBody && resultsTotalRow) {
                    const resultsRow = document.createElement('tr');
                    resultsRow.innerHTML = `
                        <td>${productName}</td>
                        <td>${product.metrics ? Math.round(product.metrics.smallDealCases) : '-'}</td>
                        <td>${bulkCases}</td>
                        <td>${casesAfterPurchase}</td>
                        <td class="${product.metrics && product.metrics.roi >= 0 ? 'positive-roi' : 'negative-roi'}">${product.metrics ? (product.metrics.roi * 100).toFixed(2) + '%' : '-'}</td>
                        <td>${product.metrics ? product.metrics.annualROIMultiplier.toFixed(2) : '-'}</td>
                        <td class="${product.metrics && product.metrics.roi >= 0 ? 'positive-roi' : 'negative-roi'}">${product.metrics ? (product.metrics.roi * product.metrics.annualROIMultiplier * 100).toFixed(2) + '%' : '-'}</td>
                    `;

                    // Insert before the totals row
                    resultsTableBody.insertBefore(resultsRow, resultsTotalRow);
                }
            }
        });

        // Update totals in results table
        if (resultsTotalRow) {
            document.getElementById('totalSmallDealCases').textContent = totalSmallDealCases;
            document.getElementById('totalBulkCases').textContent = totalBulkCases;
            document.getElementById('totalCasesAfterPurchase').textContent = totalCasesAfterPurchase;

            // Use BACKEND portfolio calculations
            const portfolioROICell = document.getElementById('portfolioROI');
            const portfolioTurnsCell = document.getElementById('portfolioTurns');
            const portfolioAnnROICell = document.getElementById('portfolioAnnROI');

            if (portfolioROICell) {
                portfolioROICell.textContent = `${(results.portfolioROI * 100).toFixed(2)}%`;
                portfolioROICell.className = results.portfolioROI >= 0 ? 'positive-roi' : 'negative-roi';
            }
            if (portfolioTurnsCell) {
                portfolioTurnsCell.textContent = (results.portfolioROIMultiplier || 0).toFixed(2);
            }
            if (portfolioAnnROICell) {
                const backendAnnROI = results.portfolioROI * results.portfolioROIMultiplier * 100;
                portfolioAnnROICell.textContent = `${backendAnnROI.toFixed(2)}%`;
                portfolioAnnROICell.className = results.portfolioROI >= 0 ? 'positive-roi' : 'negative-roi';
            }
        }

        console.log('Results updated - Totals:', {
            totalSmallDealCases,
            totalBulkCases,
            totalCasesAfterPurchase,
            portfolioROI: results.portfolioROI
        });

        // Show results section (summary and detailed results)
        const resultsSection = document.getElementById('resultsSection');
        if (resultsSection) {
            resultsSection.style.display = 'block';

            // Update summary results
            document.getElementById('peakInvestment').textContent = formatCurrency(results.totalInvestment * 2);
            document.getElementById('averageInvestment').textContent = formatCurrency(results.totalInvestment);
            document.getElementById('totalSavings').textContent = formatCurrency(results.totalSavings);
            document.getElementById('roi').textContent = (results.portfolioROI * 100).toFixed(2) + '%';

            const backendAnnualizedROI = results.portfolioROI * results.portfolioROIMultiplier * 100;
            document.getElementById('annualizedRoi').textContent = backendAnnualizedROI.toFixed(2) + '%';
            document.getElementById('iterationCount').textContent = '0';

            const portfolioEffectiveTurnsElement = document.getElementById('portfolioEffectiveTurns');
            if (portfolioEffectiveTurnsElement) {
                portfolioEffectiveTurnsElement.textContent = (results.portfolioROIMultiplier || 0).toFixed(2);
            }

            // Enable optimize button
            document.getElementById('iterateBtn').disabled = false;
            document.getElementById('exportBtn').disabled = false;
        }
    }

    // Handle scenario tab switch
    document.getElementById('scenarios-tab').addEventListener('click', function() {
        console.log('Switching to Scenarios tab');
        loadScenarioList();
    });

    // ✅ ADD: Validation when switching to calculator tab
    const calculatorTab = document.getElementById('calculator-tab');
    if (calculatorTab) {
        calculatorTab.addEventListener('click', function() {
            // Trigger validation when switching to calculator tab
            setTimeout(() => validateBulkCasesTotals(), 100);
        });
    }

    // Load scenario list
    function loadScenarioList() {
        console.log('Loading scenario list');
        const scenariosList = document.getElementById('scenariosList');

        if (!scenariosList) {
            console.error('Scenarios list element not found!');
            return;
        }

        // Get scenarios from API
        fetch('/api/list-multi-product-scenarios')
            .then(response => response.json())
            .then(data => {
                console.log('Scenarios data:', data);

                if (data.success && data.scenarios && data.scenarios.length > 0) {
                    scenariosList.innerHTML = '';

                    data.scenarios.forEach(scenario => {
                        const item = document.createElement('div');
                        item.className = 'list-group-item d-flex justify-content-between align-items-center';

                        item.innerHTML = `
                            <button type="button" class="btn btn-outline-primary scenario-item text-start" data-name="${scenario}" style="width:60%;">
                                ${scenario}
                            </button>
                            <div class="btn-group" role="group" style="width:38%;">
                                <button type="button" class="btn btn-sm btn-success load-scenario" data-name="${scenario}">
                                    <i class="fas fa-upload"></i> Load
                                </button>
                                <button type="button" class="btn btn-sm btn-danger delete-scenario" data-name="${scenario}">
                                    <i class="fas fa-trash"></i> Delete
                                </button>
                            </div>
                        `;

                        scenariosList.appendChild(item);
                    });

                    // Add event listeners to buttons
                    document.querySelectorAll('.scenario-item').forEach(btn => {
                        btn.addEventListener('click', function() {
                            // Remove the selected class from all scenario items
                            document.querySelectorAll('.scenario-item').forEach(item => {
                                item.classList.remove('btn-danger');
                                item.classList.add('btn-outline-primary');
                            });

                            // Add the selected class to the clicked item
                            this.classList.remove('btn-outline-primary');
                            this.classList.add('btn-danger');

                            // Store the selected scenario name
                            selectedScenarioName = this.getAttribute('data-name');

                            // Load the scenario details
                            loadScenarioDetails(selectedScenarioName);
                        });
                    });

                    document.querySelectorAll('.load-scenario').forEach(btn => {
                        btn.addEventListener('click', function() {
                            const scenarioName = this.getAttribute('data-name');
                            loadScenarioToCalculator(scenarioName);

                            // Update the selected scenario
                            selectedScenarioName = scenarioName;

                            // Update the UI to show which scenario is selected
                            document.querySelectorAll('.scenario-item').forEach(item => {
                                if (item.getAttribute('data-name') === scenarioName) {
                                    item.classList.remove('btn-outline-primary');
                                    item.classList.add('btn-danger');
                                } else {
                                    item.classList.remove('btn-danger');
                                    item.classList.add('btn-outline-primary');
                                }
                            });
                        });
                    });

                    document.querySelectorAll('.delete-scenario').forEach(btn => {
                        btn.addEventListener('click', function() {
                            if (confirm('Are you sure you want to delete this scenario?')) {
                                deleteScenario(this.getAttribute('data-name'));
                            }
                        });
                    });
                } else {
                    scenariosList.innerHTML = '<div class="list-group-item text-muted">No saved scenarios</div>';
                }
            })
            .catch(error => {
                console.error('Error loading scenarios:', error);
                scenariosList.innerHTML = '<div class="list-group-item text-danger">Error loading scenarios: ' + error.message + '</div>';
            });
    }

    // Load scenario details
    function loadScenarioDetails(name) {
        console.log('Loading scenario details:', name);

        fetch(`/api/get-multi-product-scenario/${encodeURIComponent(name)}`)
            .then(response => response.json())
            .then(data => {
                console.log('Scenario details:', data);

                if (data.success && data.scenario) {
                    const scenario = data.scenario;

                    // Update the selected scenario name
                    selectedScenarioName = scenario.name;

                    // Show scenario details panel
                    const scenarioDetails = document.getElementById('scenarioDetails');
                    if (scenarioDetails) {
                        scenarioDetails.style.display = 'block';
                        scenarioDetails.classList.add('scenario-details-panel');

                        // Update details
                        document.getElementById('scenarioDetailName').textContent = scenario.name;
                        document.getElementById('scenarioDetailDealSize').textContent = `${scenario.parameters.dealSizeCases} cases`;
                        document.getElementById('scenarioDetailMinDaysStock').textContent = `${scenario.parameters.minDaysStock} days`;
                        document.getElementById('scenarioDetailPaymentTerms').textContent = `${scenario.parameters.paymentTermsDays} days`;

                        // Update products table
                        const detailsBody = document.getElementById('scenarioDetailsBody');
                        if (detailsBody) {
                            detailsBody.innerHTML = '';

                            // Initialize totals
                            let totalCasesOnHand = 0;
                            let totalAnnualCases = 0;
                            let totalSmallDealCases = 0;
                            let totalBulkCases = 0;
                            let totalCasesAfterPurchase = 0;

                            scenario.products.forEach(product => {
                                // Skip products with invalid data (null/undefined critical fields)
                                if (!product.product_name || product.current_price == null || product.bulk_price == null ||
                                    product.cases_on_hand == null || product.cases_per_year == null || product.bottles_per_case == null) {
                                    console.warn('Skipping invalid product:', product);
                                    return;
                                }

                                // Calculate small deal cases based on parameters and bulkCases
                                let smallDealCases = '-';
                                let totalCases = '-';

                                // If we have the necessary data, calculate smallDealCases
                                if (product.bulk_quantity && scenario.parameters) {
                                    const dailyCases = product.cases_per_year / 365;
                                    const daysQty = Math.ceil(dailyCases * scenario.parameters.min_days_stock);
                                    const propQty = Math.ceil(product.bulk_quantity * (scenario.parameters.small_deal_minimum || 30) / scenario.parameters.dealSizeCases);
                                    smallDealCases = Math.max(propQty, daysQty);

                                    // Calculate total cases after purchase
                                    totalCases = product.cases_on_hand + product.bulk_quantity;

                                    // Add to totals if numeric values
                                    totalSmallDealCases += parseInt(smallDealCases) || 0;
                                    totalCasesAfterPurchase += parseInt(totalCases) || 0;
                                }

                                // Add to running totals
                                totalCasesOnHand += product.cases_on_hand || 0;
                                totalAnnualCases += product.cases_per_year || 0;
                                totalBulkCases += product.bulk_quantity || 0;

                                const row = document.createElement('tr');
                                row.innerHTML = `
                                    <td>${product.product_name}</td>
                                    <td>$${product.current_price.toFixed(2)}</td>
                                    <td>$${product.bulk_price.toFixed(2)}</td>
                                    <td>${product.cases_on_hand}</td>
                                    <td>${product.cases_per_year}</td>
                                    <td>${product.bottles_per_case}</td>
                                    <td>${smallDealCases}</td>
                                    <td>${product.bulk_quantity || 'N/A'}</td>
                                    <td>${totalCases}</td>
                                `;
                                detailsBody.appendChild(row);
                            });

                            // Add totals row
                            const totalsRow = document.createElement('tr');
                            totalsRow.className = 'table-light total-row';
                            totalsRow.innerHTML = `
                                <td><strong>TOTALS</strong></td>
                                <td class="detail-column"></td>
                                <td></td>
                                <td class="detail-column"><strong>${totalCasesOnHand}</strong></td>
                                <td class="detail-column"><strong>${totalAnnualCases}</strong></td>
                                <td class="detail-column"></td>
                                <td><strong>${totalSmallDealCases}</strong></td>
                                <td><strong>${totalBulkCases}</strong></td>
                                <td><strong>${totalCasesAfterPurchase}</strong></td>
                                <td><strong>-</strong></td>
                                <td><strong>-</strong></td>
                                <td></td>
                            `;
                            detailsBody.appendChild(totalsRow);
                        }

                        // Enable and style the load button in the details panel
                        if (loadScenarioBtn) {
                            loadScenarioBtn.disabled = false;
                            loadScenarioBtn.classList.add('scenario-load-btn');
                        }
                    }
                } else {
                    alert('Error loading scenario details: ' + (data.error || 'Unknown error'));
                }
            })
            .catch(error => {
                console.error('Error loading scenario details:', error);
                alert('Error loading scenario details: ' + error.message);
            });
    }

    // Load scenario to calculator
    function loadScenarioToCalculator(name) {
        console.log('Loading scenario to calculator:', name);

        fetch(`/api/get-multi-product-scenario/${encodeURIComponent(name)}`)
            .then(response => response.json())
            .then(data => {
                console.log('Scenario data for calculator:', data);

                if (data.success && data.scenario) {
                    const scenario = data.scenario;

                    // Update the selected scenario name
                    selectedScenarioName = scenario.name;

                    // Update the UI to show which scenario is selected
                    document.querySelectorAll('.scenario-item').forEach(item => {
                        if (item.getAttribute('data-name') === name) {
                            item.classList.remove('btn-outline-primary');
                            item.classList.add('btn-danger');
                        } else {
                            item.classList.remove('btn-danger');
                            item.classList.add('btn-outline-primary');
                        }
                    });

                    // Remember that we've loaded a scenario
                    defaultProductAdded = true;

                    // Clear existing products - ensure ALL rows are removed
                    while (productsTableBody.firstChild) {
                        productsTableBody.removeChild(productsTableBody.firstChild);
                    }

                    // Hide results sections since they're no longer relevant to the loaded scenario
                    if (resultsTableSection) {
                        resultsTableSection.style.display = 'none';
                    }

                    const resultsSection = document.getElementById('resultsSection');
                    if (resultsSection) {
                        resultsSection.style.display = 'none';
                    }

                    // Clear optimization history
                    globalOptimizationHistory = [];
                    updateOptimizationHistory([]);

                    // Remove the clear history button since history is now empty
                    const clearHistoryBtn = document.querySelector('.clear-history-btn');
                    if (clearHistoryBtn) {
                        clearHistoryBtn.remove();
                    }

                    // Load parameters
                    document.getElementById('smallDealCases').value = scenario.parameters.smallDealCases || 15;
                    document.getElementById('dealSizeCases').value = scenario.parameters.dealSizeCases;
                    document.getElementById('minDaysStock').value = scenario.parameters.minDaysStock;
                    document.getElementById('paymentTermsDays').value = scenario.parameters.paymentTermsDays;
                    document.getElementById('iterations').value = scenario.parameters.iterations || 'auto';
                    document.getElementById('scenarioName').value = scenario.name;

                    // Add products
                    scenario.products.forEach(product => {
                        // Skip products with invalid data (null/undefined critical fields)
                        if (!product.product_name || product.current_price == null || product.bulk_price == null ||
                            product.on_hand == null || product.annual_cases == null || product.bottles_per_case == null) {
                            console.warn('Skipping invalid product during load:', product);
                            return;
                        }

                        const mappedProduct = mapLegacyProductKeys(product);

                        const newRow = document.createElement('tr');

                        newRow.innerHTML = `
                            <td><input type="text" class="form-control product-name" value="${mappedProduct.product_name}" required></td>
                            <td><input type="number" class="form-control product-small-price" min="0.01" step="0.01" value="${mappedProduct.current_price}" required></td>
                            <td><input type="number" class="form-control product-bulk-price" min="0.01" step="0.01" value="${mappedProduct.bulk_price}" required></td>
                            <td class="detail-column"><input type="number" class="form-control product-cases-on-hand" min="0" value="${mappedProduct.cases_on_hand}" required></td>
                            <td class="detail-column"><input type="number" class="form-control product-annual-cases" min="1" value="${mappedProduct.cases_per_year}" required></td>
                            <td class="detail-column"><input type="number" class="form-control product-bottles-per-case" min="1" value="${mappedProduct.bottles_per_case}" required></td>
                            <td><input type="number" class="form-control product-bulk-cases" min="0" value="${mappedProduct.bulk_quantity || ''}" placeholder="Auto-calculated"></td>
                            <td>
                                <button class="btn btn-sm btn-danger remove-product">
                                    <i class="fas fa-trash"></i>
                                </button>
                            </td>
                        `;

                        // Add remove functionality
                        const removeBtn = newRow.querySelector('.remove-product');
                        if (removeBtn) {
                            removeBtn.addEventListener('click', function() {
                                if (productsTableBody.contains(newRow)) {
                                    productsTableBody.removeChild(newRow);
                                }
                            });
                        }

                        productsTableBody.appendChild(newRow);
                    });

                    // Switch to calculator tab
                    document.getElementById('calculator-tab').click();

                    // Remove the success popup - it's unnecessary and causes browser automation issues
                    console.log(`Scenario "${scenario.name}" loaded successfully with ${scenario.products.length} products!`);

                    // ✅ ADD: Validate bulk cases totals after loading scenario
                    setTimeout(() => validateBulkCasesTotals(), 100);

                    // Note: updateTotals() removed since it's no longer needed with the new two-table design
                    // The results table will be populated when calculations are run
                } else {
                    alert('Error loading scenario: ' + (data.error || 'Unknown error'));
                }
            })
            .catch(error => {
                console.error('Error loading scenario:', error);
                alert('Error loading scenario: ' + error.message);
            });
    }

    // Delete scenario
    function deleteScenario(name) {
        console.log('Deleting scenario:', name);

        fetch(`/api/delete-multi-product-scenario/${encodeURIComponent(name)}`, {
            method: 'DELETE'
        })
            .then(response => response.json())
            .then(data => {
                console.log('Delete response:', data);

                if (data.success) {
                    alert('Scenario deleted successfully!');
                    loadScenarioList();

                    // Clear scenario details if the deleted scenario was selected
                    if (selectedScenarioName === name) {
                        const scenarioDetails = document.getElementById('scenarioDetails');
                        if (scenarioDetails) {
                            scenarioDetails.style.display = 'none';
                        }
                        selectedScenarioName = null;
                    }
                } else {
                    alert('Error deleting scenario: ' + (data.error || 'Unknown error'));
                }
            })
            .catch(error => {
                console.error('Error deleting scenario:', error);
                alert('Error deleting scenario: ' + error.message);
            });
    }

    // Save scenario - completely replacing this function to fix double notification issue
    const saveScenarioBtn = document.getElementById('saveScenario');

    // Remove any existing event listeners
    if (saveScenarioBtn) {
        const newSaveButton = saveScenarioBtn.cloneNode(true);
        saveScenarioBtn.parentNode.replaceChild(newSaveButton, saveScenarioBtn);

        // Add the event listener to the new button
        newSaveButton.addEventListener('click', handleSaveScenario);
    }

    // Handle save scenario as a separate function
    function handleSaveScenario() {
        console.log('Save scenario button clicked');

        const scenarioName = document.getElementById('scenarioName').value.trim();

        if (!scenarioName) {
            alert('Please enter a scenario name');
            return;
        }

        // Collect product data
        const rows = productsTableBody.querySelectorAll('tr');
        const productsToSave = [];

        rows.forEach((row, index) => {
            const nameInput = row.querySelector('.product-name');
            if (!nameInput) return; // Skip if not a valid product row

            const product = {
                id: 'product-' + index,
                product_name: nameInput.value,
                current_price: parseFloat(row.querySelector('.product-small-price').value),
                bulk_price: parseFloat(row.querySelector('.product-bulk-price').value),
                on_hand: parseInt(row.querySelector('.product-cases-on-hand').value),
                annual_cases: parseInt(row.querySelector('.product-annual-cases').value) || 1,
                bottles_per_case: parseInt(row.querySelector('.product-bottles-per-case').value),
                bulk_quantity: parseInt(row.querySelector('.product-bulk-cases').value) || 0
            };

            productsToSave.push(product);
        });

        // Get parameters
        const params = {
            smallDealCases: parseInt(document.getElementById('smallDealCases').value),
            dealSizeCases: parseInt(document.getElementById('dealSizeCases').value),
            minDaysStock: parseInt(document.getElementById('minDaysStock').value),
            paymentTermsDays: parseInt(document.getElementById('paymentTermsDays').value),
            iterations: document.getElementById('iterations').value
        };

        console.log('Saving scenario with products:', productsToSave);

        // Save scenario
        fetch('/api/save-multi-product-scenario', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                name: scenarioName,
                parameters: params,
                products: productsToSave
            })
        })
        .then(response => response.json())
        .then(data => {
            console.log('Save response:', data);

            if (data.success) {
                alert('Scenario saved successfully!');

                // Update the selected scenario
                selectedScenarioName = scenarioName;

                // Refresh the scenario list
                if (document.getElementById('scenarios').classList.contains('active')) {
                    loadScenarioList();
                }
            } else {
                alert('Error saving scenario: ' + (data.error || 'Unknown error'));
            }
        })
        .catch(error => {
            console.error('Error saving scenario:', error);
            alert('Error saving scenario: ' + error.message);
        });
    }

    // Add a default product row on startup only if there are no products
    if (!defaultProductAdded && productsTableBody.children.length === 0) {
        handleAddProduct();
        defaultProductAdded = true;
    }

    // ✅ ADD: Check for bulk cases validation on page load
    setTimeout(() => {
        const existingRows = productsTableBody?.querySelectorAll('tr:not(#productRowTemplate)');
        if (existingRows && existingRows.length > 0) {
            validateBulkCasesTotals();
        }
    }, 500);

    // Add a clear products button event handler
    const clearProductsBtn = document.getElementById('clearProducts');
    if (clearProductsBtn) {
        clearProductsBtn.addEventListener('click', function() {
            if (confirm('Are you sure you want to clear all products?')) {
                // Clear the products table
                const rows = productsTableBody.querySelectorAll('tr:not(#productRowTemplate):not(#totalRow)');
                rows.forEach(row => productsTableBody.removeChild(row));

                // Hide results sections since they're no longer relevant
                if (resultsTableSection) {
                    resultsTableSection.style.display = 'none';
                }

                const resultsSection = document.getElementById('resultsSection');
                if (resultsSection) {
                    resultsSection.style.display = 'none';
                }

                // Clear optimization history
                globalOptimizationHistory = [];
                updateOptimizationHistory([]);

                // Remove the clear history button since history is now empty
                const clearHistoryBtn = document.querySelector('.clear-history-btn');
                if (clearHistoryBtn) {
                    clearHistoryBtn.remove();
                }

                // Add a default row
                handleAddProduct();
            }
        });
    }

    // Also update the optimize button handler to calculate and display totals
    const iterateBtn = document.getElementById('iterateBtn');
    if (iterateBtn) {
        iterateBtn.addEventListener('click', function() {
            console.log('Optimize button clicked - starting optimization process');

            // Get all the product data from the UI
            const rows = productsTableBody.querySelectorAll('tr:not(#productRowTemplate)');
            console.log('Found rows for optimization:', rows.length);
            products = [];

            rows.forEach((row, index) => {
                console.log('Processing row', index, row);

                const nameInput = row.querySelector('.product-name');
                const smallPriceInput = row.querySelector('.product-small-price');
                const bulkPriceInput = row.querySelector('.product-bulk-price');
                const onHandInput = row.querySelector('.product-cases-on-hand');
                const annualInput = row.querySelector('.product-annual-cases');
                const bottlesInput = row.querySelector('.product-bottles-per-case');
                const bulkCasesInput = row.querySelector('.product-bulk-cases');

                console.log('Row inputs found:', {
                    name: nameInput ? nameInput.value : 'NOT FOUND',
                    smallPrice: smallPriceInput ? smallPriceInput.value : 'NOT FOUND',
                    bulkPrice: bulkPriceInput ? bulkPriceInput.value : 'NOT FOUND',
                    onHand: onHandInput ? onHandInput.value : 'NOT FOUND',
                    annual: annualInput ? annualInput.value : 'NOT FOUND',
                    bottles: bottlesInput ? bottlesInput.value : 'NOT FOUND',
                    bulkCases: bulkCasesInput ? bulkCasesInput.value : 'NOT FOUND'
                });

                if (nameInput && smallPriceInput && bulkPriceInput) {
                    const product = {
                        id: 'product-' + index,
                        product_name: nameInput.value,
                        current_price: parseFloat(smallPriceInput.value),
                        bulk_price: parseFloat(bulkPriceInput.value),
                        on_hand: parseInt(onHandInput ? onHandInput.value : 10),
                        annual_cases: parseInt(annualInput ? annualInput.value : 60),
                        bottles_per_case: parseInt(bottlesInput ? bottlesInput.value : 12),
                        bulk_quantity: parseInt(bulkCasesInput ? bulkCasesInput.value || 0 : 0) || 0
                    };

                    products.push(product);
                    console.log('Added product:', product);
                } else {
                    console.log('Skipping row due to missing inputs');
                }
            });

            console.log('Total products collected:', products.length);

            // Get parameters
            const smallDealCases = parseInt(document.getElementById('smallDealCases').value);
            const dealSizeCases = parseInt(document.getElementById('dealSizeCases').value);
            const minDaysStock = parseInt(document.getElementById('minDaysStock').value);
            const paymentTermsDays = parseInt(document.getElementById('paymentTermsDays').value);
            const iterations = document.getElementById('iterations').value;
            const params = {
                // Backend validation keys
                small_deal_minimum: smallDealCases,
                bulk_deal_minimum: dealSizeCases,
                payment_terms: paymentTermsDays,
                min_days_stock: minDaysStock,
                // Calculation logic keys
                smallDealCases: smallDealCases,
                dealSizeCases: dealSizeCases,
                minDaysStock: minDaysStock,
                paymentTermsDays: paymentTermsDays,
                iterations: iterations
            };

            console.log('Optimization products:', products);
            console.log('Optimization parameters:', params);

            // Make API call to optimize
            console.log('Making API call to /api/optimize-multi-product-deal');
            fetch('/api/optimize-multi-product-deal', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    parameters: params,
                    products: products
                })
            })
            .then(response => {
                console.log('Optimization API response status:', response.status);
                return response.json();
            })
            .then(data => {
                console.log('Optimization API response data:', data);

                if (data.success) {
                    console.log('Optimization successful, updating results');
                    // Update results and history
                    updateResults(data.results);

                    // APPEND new history instead of replacing
                    if (data.results.history && data.results.history.length > 0) {
                        // Check if this is a new optimization run (starts with iteration 0)
                        const firstIteration = data.results.history[0];
                        if (firstIteration && firstIteration.iteration === 0) {
                            // This is a fresh optimization, add a separator if we have existing history
                            if (globalOptimizationHistory.length > 0) {
                                globalOptimizationHistory.push({
                                    iteration: '---',
                                    totalROI: 0,
                                    swapped: null,
                                    separator: true
                                });
                            }
                        }

                        // Add the new history to our global history
                        globalOptimizationHistory = globalOptimizationHistory.concat(data.results.history);
                    }

                    updateOptimizationHistory(globalOptimizationHistory);
                    document.getElementById('iterationCount').textContent = data.results.totalIterations;
                } else {
                    console.error('Optimization failed:', data.error);
                    alert('Error during optimization: ' + (data.error || 'Unknown error'));
                }
            })
            .catch(error => {
                console.error('Optimization error:', error);
                alert('Error during optimization: ' + error.message);
            });
        });
    } else {
        console.error('iterateBtn not found!');
    }

    // Function to update optimization history
    function updateOptimizationHistory(history) {
        const historyBody = document.getElementById('optimizationHistoryBody');
        if (!historyBody) return;

        // ONLY clear if we're starting fresh (no history)
        if (history.length === 0) {
            historyBody.innerHTML = '';
            return;
        }

        // Clear the table and rebuild with full history
        historyBody.innerHTML = '';
        let prevRoi = 0;
        let runNumber = 1;
        let isVeryFirstOptimization = true; // Track if this is the very first optimization overall

        history.forEach((iteration, index) => {
            const row = document.createElement('tr');

            // Handle separator rows
            if (iteration.separator) {
                row.innerHTML = `
                    <td colspan="4" style="background-color: #e9ecef; text-align: center; font-weight: bold; font-style: italic;">
                        --- Optimization Run ${++runNumber} ---
                    </td>
                `;
                row.style.backgroundColor = '#e9ecef';
                historyBody.appendChild(row);
                prevRoi = 0; // Reset for new run
                isVeryFirstOptimization = false; // After first separator, we're no longer in the first run
                return;
            }

            // Format action message with improved labels
            let action;
            if (iteration.iteration === 0) {
                if (isVeryFirstOptimization) {
                    action = "Initial Allocation";
                } else {
                    // If this is the last row of the run and no further swaps, label as Fully Optimized
                    const isLastOfRun = (
                        index === history.length - 1 ||
                        (history[index + 1] && history[index + 1].separator)
                    );
                    const roi = iteration.totalAnnualizedROI || iteration.totalROI;
                    const roiChange = index > 0 && !history[index-1]?.separator ? roi - prevRoi : 0;

                    if (isLastOfRun && Math.abs(roiChange) < 0.001) {
                        action = "Fully Optimized";
                    } else {
                        action = "Continue from Previous";
                    }
                }
            } else {
                const from = iteration.swapped?.from || '';
                const to = iteration.swapped?.to || '';
                action = `Moved 1 case from ${from} to ${to}`;
            }

            // Calculate ROI change - USE ANNUALIZED ROI instead of regular ROI
            const roi = iteration.totalAnnualizedROI || iteration.totalROI;
            const roiChange = index > 0 && !history[index-1]?.separator ? roi - prevRoi : 0;

            row.innerHTML = `
                <td>${iteration.iteration}</td>
                <td>${action}</td>
                <td>${(roi * 100).toFixed(2)}%</td>
                <td style="color: ${roiChange >= 0 ? '#28a745' : '#dc3545'}; font-weight: ${Math.abs(roiChange) > 0.001 ? 'bold' : 'normal'};">
                    ${roiChange > 0 ? '+' : ''}${(roiChange * 100).toFixed(2)}%
                </td>
            `;

            historyBody.appendChild(row);
            if (!iteration.separator) {
                prevRoi = roi;
            }
        });

        // Add clear history button if we have history
        if (history.length > 0) {
            addClearHistoryButton();
        }
    }

    // Function to add clear history button
    function addClearHistoryButton() {
        const historySection = document.getElementById('optimizationHistoryBody').closest('.card');
        if (!historySection) return;

        // Check if button already exists
        if (historySection.querySelector('.clear-history-btn')) return;

        const cardHeader = historySection.querySelector('.card-header');
        if (cardHeader) {
            const clearBtn = document.createElement('button');
            clearBtn.className = 'btn btn-sm btn-outline-secondary float-end clear-history-btn';
            clearBtn.innerHTML = '<i class="fas fa-trash"></i> Clear History';
            clearBtn.onclick = function() {
                if (confirm('Clear all optimization history?')) {
                    globalOptimizationHistory = [];
                    updateOptimizationHistory([]);
                    this.remove();
                }
            };
            cardHeader.appendChild(clearBtn);
        }
    }

    // Handle auto allocation button click
    function handleAutoAllocation() {
        console.log('Auto Allocation button clicked');

        // Get deal size
        const dealSizeCases = parseInt(document.getElementById('dealSizeCases').value);
        if (!dealSizeCases || dealSizeCases <= 0) {
            alert('Please enter a valid deal size before using auto allocation');
            return;
        }

        // Collect product data and calculate total annual cases
        const rows = productsTableBody.querySelectorAll('tr:not(#productRowTemplate):not(#totalRow)');
        if (rows.length === 0) {
            alert('Please add at least one product before using auto allocation');
            return;
        }

        let totalAnnualCases = 0;
        const productData = [];

        rows.forEach((row, index) => {
            const annualCases = parseInt(row.querySelector('.product-annual-cases').value) || 0;
            totalAnnualCases += annualCases;
            productData.push({
                row: row,
                annual_cases: annualCases
            });
        });

        if (totalAnnualCases === 0) {
            alert('Cannot allocate cases: all products have 0 annual cases');
            return;
        }

        // Distribute cases proportionally
        let allocatedCases = 0;
        const allocations = [];

        productData.forEach((product, index) => {
            let casesToAllocate;
            if (index === productData.length - 1) {
                // Last product gets remaining cases to avoid rounding errors
                casesToAllocate = dealSizeCases - allocatedCases;
            } else {
                // Calculate proportional allocation
                const proportion = product.annual_cases / totalAnnualCases;
                casesToAllocate = Math.round(dealSizeCases * proportion);
                allocatedCases += casesToAllocate;
            }

            allocations.push(casesToAllocate);

            // Update the bulk cases input field
            const bulkCasesInput = product.row.querySelector('.product-bulk-cases');
            if (bulkCasesInput) {
                bulkCasesInput.value = casesToAllocate;
            }
        });

        // CLEAR OPTIMIZATION HISTORY since we're starting with a new baseline
        console.log('Clearing optimization history due to Auto Allocation reset');
        globalOptimizationHistory = [];
        updateOptimizationHistory([]);

        // Remove the clear history button since history is now empty
        const clearHistoryBtn = document.querySelector('.clear-history-btn');
        if (clearHistoryBtn) {
            clearHistoryBtn.remove();
        }

        console.log('Auto allocation complete:', allocations, 'Total allocated:', allocations.reduce((a, b) => a + b, 0));

        // Trigger validation after auto allocation
        validateBulkCasesTotals();
    }

    // Bulk cases validation function
    function validateBulkCasesTotals() {
        const dealSize = parseInt(document.getElementById('dealSizeCases').value) || 0;
        const headerIndicator = document.getElementById('bulkCasesHeaderIndicator');
        const indicatorText = document.getElementById('bulkCasesIndicatorText');
        const calculateButton = document.getElementById('calculateBtn');

        if (dealSize <= 0 || !headerIndicator || !indicatorText) {
            if (headerIndicator) headerIndicator.style.display = 'none';
            return;
        }

        // Calculate total bulk cases
        const bulkCasesInputs = productsTableBody.querySelectorAll('.product-bulk-cases');
        let totalBulkCases = 0;
        let hasAnyValues = false;

        bulkCasesInputs.forEach(input => {
            const value = parseInt(input.value) || 0;
            if (input.value !== '') {
                hasAnyValues = true;
            }
            totalBulkCases += value;

            // Remove previous validation classes
            input.classList.remove('validation-error', 'validation-warning', 'validation-success');
        });

        // ✅ CHANGE: Show indicator even if no bulk case values entered yet (if we have products)
        const hasAnyProducts = bulkCasesInputs.length > 0;
        if (!hasAnyProducts) {
            if (headerIndicator) headerIndicator.style.display = 'none';
            return;
        }

        // Show header indicator
        if (headerIndicator) headerIndicator.style.display = 'block';

        const available = dealSize - totalBulkCases;
        
        // Remove previous validation classes from header indicator
        if (headerIndicator) {
            headerIndicator.classList.remove('valid', 'invalid', 'warning');
        }

        // Apply validation logic and styling
        if (totalBulkCases > dealSize) {
            // ERROR: Exceeds deal size
            if (headerIndicator) headerIndicator.classList.add('invalid');
            indicatorText.textContent = `⚠️ ${totalBulkCases}/${dealSize}`;

            // Highlight inputs in error
            bulkCasesInputs.forEach(input => {
                if (parseInt(input.value) > 0) {
                    input.classList.add('validation-error');
                }
            });

            // Disable calculate button
            if (calculateButton) {
                calculateButton.disabled = true;
                calculateButton.title = 'Cannot calculate: bulk cases exceed deal size';
            }
        } else if (totalBulkCases === dealSize) {
            // SUCCESS: Exact match
            if (headerIndicator) headerIndicator.classList.add('valid');
            indicatorText.textContent = `✅ ${totalBulkCases}/${dealSize}`;

            // Highlight inputs in success
            bulkCasesInputs.forEach(input => {
                if (parseInt(input.value) > 0) {
                    input.classList.add('validation-success');
                }
            });

            // Enable calculate button
            if (calculateButton) {
                calculateButton.disabled = false;
                calculateButton.title = '';
            }
        } else if (totalBulkCases > dealSize * 0.8) {
            // WARNING: Close to limit but acceptable
            if (headerIndicator) headerIndicator.classList.add('warning');
            indicatorText.textContent = `⚡ ${totalBulkCases}/${dealSize}`;

            // Highlight inputs in warning
            bulkCasesInputs.forEach(input => {
                if (parseInt(input.value) > 0) {
                    input.classList.add('validation-warning');
                }
            });

            // Enable calculate button
            if (calculateButton) {
                calculateButton.disabled = false;
                calculateButton.title = '';
            }
        } else {
            // NORMAL: Under limit - but still show the indicator
            if (headerIndicator) headerIndicator.classList.add('valid');

            if (totalBulkCases === 0) {
                indicatorText.textContent = `${totalBulkCases}/${dealSize}`;
            } else {
                indicatorText.textContent = `${totalBulkCases}/${dealSize}`;
            }

            // Enable calculate button
            if (calculateButton) {
                calculateButton.disabled = false;
                calculateButton.title = '';
            }
        }
    }

    // Export to Excel button event listener
    function handleExportToExcel() {
        console.log('Export to Excel button clicked');

        // Collect product data
        const rows = productsTableBody.querySelectorAll('tr:not(#productRowTemplate):not(#totalRow)');
        const productsToExport = [];

        rows.forEach((row, index) => {
            const product = {
                id: 'product-' + index,
                product_name: row.querySelector('.product-name').value,
                current_price: parseFloat(row.querySelector('.product-small-price').value),
                bulk_price: parseFloat(row.querySelector('.product-bulk-price').value),
                on_hand: parseInt(row.querySelector('.product-cases-on-hand').value),
                annual_cases: parseInt(row.querySelector('.product-annual-cases').value) || 1,
                bottles_per_case: parseInt(row.querySelector('.product-bottles-per-case').value),
                bulk_quantity: parseInt(row.querySelector('.product-bulk-cases').value) || 0
            };

            productsToExport.push(product);
        });

        console.log('Products to export:', productsToExport);

        // Get parameters
        const params = {
            dealSizeCases: parseInt(document.getElementById('dealSizeCases').value),
            minDaysStock: parseInt(document.getElementById('minDaysStock').value),
            paymentTermsDays: parseInt(document.getElementById('paymentTermsDays').value),
            iterations: document.getElementById('iterations').value
        };

        console.log('Export parameters:', params);

        // Make API call to export to Excel
        fetch('/api/export-multi-product-deal', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                name: document.getElementById('scenarioName').value || 'Distributor Order',
                parameters: params,
                products: productsToExport
            })
        })
        .then(response => {
            if (response.ok) {
                // Handle the file download
                return response.blob();
            } else {
                throw new Error('Export failed');
            }
        })
        .then(blob => {
            // Create a download link for the Excel file
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;

            // Generate filename
            const scenarioName = document.getElementById('scenarioName').value || 'Distributor_Order';
            const timestamp = new Date().toISOString().slice(0, 19).replace(/[:-]/g, '');
            a.download = `distributor_order_${scenarioName.replace(/\s+/g, '_')}_${timestamp}.xlsx`;

            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);

            console.log('Export to Excel successful - file downloaded');
        })
        .catch(error => {
            console.error('Error exporting to Excel:', error);
            alert('Error exporting to Excel: ' + error.message);
        });
    }

    // In loadScenarioToCalculator and loadScenarioDetails, add this mapping for each product:
    function mapLegacyProductKeys(product) {
        return {
            product_name: product.product_name || product.name || '',
            current_price: product.current_price != null ? product.current_price : product.priceSmall,
            bulk_price: product.bulk_price != null ? product.bulk_price : product.priceBulk,
            cases_on_hand: product.on_hand != null ? product.on_hand : product.onHandCases,
            cases_per_year: product.annual_cases != null ? product.annual_cases : product.annualCases,
            bottles_per_case: product.bottles_per_case != null ? product.bottles_per_case : product.bottlesPerCase,
            bulk_quantity: product.bulk_quantity != null ? product.bulk_quantity : product.bulkCases || 0
        };
    }

    // --- BEGIN: ENHANCED VALIDATION FUNCTIONS ---

    // Clear all bulk cases function
    function clearAllBulkCases() {
        if (confirm('Clear all bulk case allocations?')) {
            const bulkInputs = document.querySelectorAll('.product-bulk-cases');
            bulkInputs.forEach(input => {
                input.value = '';
                input.classList.add('bulk-cases-empty');
            });
            validateBulkCasesTotals();
            validateAndStyleRequiredFields();

            // Clear optimization history since we're starting fresh
            globalOptimizationHistory = [];
            updateOptimizationHistory([]);

            // Remove the clear history button since history is now empty
            const clearHistoryBtn = document.querySelector('.clear-history-btn');
            if (clearHistoryBtn) {
                clearHistoryBtn.remove();
            }
        }
    }

    // Enhanced calculate with validation
    function validateAndCalculate() {
        console.log('validateAndCalculate called');

        // Show validation summary if there are issues
        const validationSummary = document.getElementById('formValidationSummary');
        const errorsList = document.getElementById('validationErrorsList');

        if (!isFormReadyForCalculation()) {
            validationSummary.style.display = 'block';
            errorsList.innerHTML = '<li>Please fill in all required fields (marked with *)</li>';

            // Scroll to validation summary
            validationSummary.scrollIntoView({ behavior: 'smooth', block: 'center' });
            return;
        }

        validationSummary.style.display = 'none';
        handleCalculate(); // Call existing calculate function
    }

    // Check if form is ready for calculation
    function isFormReadyForCalculation() {
        // Check parameters
        const dealSize = parseInt(document.getElementById('dealSizeCases').value);
        const smallDeal = parseInt(document.getElementById('smallDealCases').value);
        const minDays = parseInt(document.getElementById('minDaysStock').value);
        const paymentTerms = parseInt(document.getElementById('paymentTermsDays').value);

        if (!dealSize || dealSize <= 0 || !smallDeal || smallDeal <= 0 ||
            minDays < 0 || paymentTerms < 0) {
            return false;
        }

        // Check products
        const rows = productsTableBody.querySelectorAll('tr:not(#productRowTemplate)');
        if (rows.length === 0) {
            return false;
        }

        // Check each product has required fields
        for (const row of rows) {
            const name = row.querySelector('.product-name')?.value?.trim();
            const smallPrice = parseFloat(row.querySelector('.product-small-price')?.value);
            const bulkPrice = parseFloat(row.querySelector('.product-bulk-price')?.value);
            const onHand = parseInt(row.querySelector('.product-cases-on-hand')?.value);
            const annual = parseInt(row.querySelector('.product-annual-cases')?.value);
            const bottles = parseInt(row.querySelector('.product-bottles-per-case')?.value);

            if (!name || !smallPrice || smallPrice <= 0 || !bulkPrice || bulkPrice <= 0 ||
                onHand < 0 || !annual || annual <= 0 || !bottles || bottles <= 0) {
                return false;
            }
        }

        return true;
    }

    // Validate and style required fields
    function validateAndStyleRequiredFields() {
        // Style parameter fields
        const parameterInputs = [
            'dealSizeCases', 'smallDealCases', 'minDaysStock', 'paymentTermsDays'
        ];

        parameterInputs.forEach(id => {
            const input = document.getElementById(id);
            if (input) {
                const value = parseFloat(input.value);
                if (!value || value <= 0 || (id === 'minDaysStock' && value < 0) ||
                    (id === 'paymentTermsDays' && value < 0)) {
                    input.classList.add('is-invalid');
                } else {
                    input.classList.remove('is-invalid');
                    input.classList.add('is-valid');
                }
            }
        });

        // Style product fields
        const rows = productsTableBody.querySelectorAll('tr:not(#productRowTemplate)');
        rows.forEach(row => {
            const inputs = row.querySelectorAll('input[required]');
            inputs.forEach(input => {
                const value = input.value.trim();
                const numValue = parseFloat(value);

                if (input.classList.contains('product-name')) {
                    if (!value) {
                        input.classList.add('is-invalid');
                    } else {
                        input.classList.remove('is-invalid');
                        input.classList.add('is-valid');
                    }
                } else if (input.classList.contains('product-annual-cases') ||
                          input.classList.contains('product-bottles-per-case')) {
                    if (!value || numValue <= 0) {
                        input.classList.add('is-invalid');
                    } else {
                        input.classList.remove('is-invalid');
                        input.classList.add('is-valid');
                    }
                } else {
                    if (!value || numValue < 0) {
                        input.classList.add('is-invalid');
                    } else {
                        input.classList.remove('is-invalid');
                        input.classList.add('is-valid');
                    }
                }
            });
        });
    }

    // Note: Removed duplicate autoAllocationBtn2 since we now have only one Auto Allocate button

    // Add validation styling on input changes
    document.addEventListener('input', function(event) {
        if (event.target.matches('input[required]')) {
            validateAndStyleRequiredFields();
        }
    });

    // --- END: ENHANCED VALIDATION FUNCTIONS ---
});
