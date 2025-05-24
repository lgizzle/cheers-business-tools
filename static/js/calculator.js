/**
 * Multi-Product Buying Calculator - Core Calculation Functions
 *
 * Pure functions that implement the core business logic for the
 * Multi-Product Buying Calculator.
 */

/**
 * Compute ROI metrics for a single product line item
 *
 * @param {Object} options - Product and calculation parameters
 * @param {number} options.annualCases - Annual cases sold
 * @param {number} options.bottlesPerCase - Bottles per case
 * @param {number} options.priceSmall - Price per bottle in small deal (P₁)
 * @param {number} options.priceBulk - Price per bottle in bulk deal (P₂)
 * @param {number} options.bulkCases - Number of cases in bulk deal (Q₂)
 * @param {number} options.smallDealBottles - Number of bottles in small deal (q₁)
 * @param {number} options.onHandCases - Number of cases on hand
 * @param {number} options.paymentTermsDays - Payment terms in days
 * @param {number} options.minDaysStock - Minimum days of stock required
 * @returns {Object} ROI metrics including avgInvestment, savings, roi, annualizedRoi
 */
function computeLineItemROI(options) {
  // Destructure parameters
  const {
    annualCases, bottlesPerCase,
    priceSmall, priceBulk,
    bulkCases, smallDealBottles,
    onHandCases, paymentTermsDays,
    minDaysStock
  } = options;

  // Edge case: No velocity
  if (annualCases <= 0) {
    return {
      avgInvestment: 0,
      savings: 0,
      roi: 0,
      annualizedRoi: 0,
      error: "Zero velocity"
    };
  }

  // Convert quantities to bottles
  const annualBottles = annualCases * bottlesPerCase;
  const onHandBottles = onHandCases * bottlesPerCase;
  const bulkBottles = bulkCases * bottlesPerCase;

  // Calculate daily depletion rate (bottles per day)
  const dailyBottles = annualBottles / 365;

  // Calculate depletion periods
  const daysToDepleteBulk = bulkBottles / dailyBottles;

  // Edge case: Not enough stock
  const minRequiredBottles = dailyBottles * minDaysStock;
  if (onHandBottles + bulkBottles < minRequiredBottles) {
    return {
      avgInvestment: 0,
      savings: 0,
      roi: 0,
      annualizedRoi: 0,
      error: "Insufficient stock to meet minimum days requirement"
    };
  }

  // Calculate investment amounts
  const bulkInvestment = bulkBottles * priceBulk;
  const smallInvestment = smallDealBottles * priceSmall;

  // Calculate peak and average investment difference
  const peakInvestment = bulkInvestment - smallInvestment;

  // Average investment over time (assumes linear depletion)
  const avgInvestment = peakInvestment * 0.5;

  // Calculate savings
  const savingsPerBottle = priceSmall - priceBulk;
  const savings = savingsPerBottle * bulkBottles;

  // Calculate ROI
  const roi = avgInvestment > 0 ? savings / avgInvestment : 0;

  // Annualize ROI
  const annualizedRoi = roi * (365 / daysToDepleteBulk);

  return {
    avgInvestment,
    peakInvestment,
    savings,
    roi,
    annualizedRoi,
    daysToDepleteBulk
  };
}

/**
 * Allocate deal cases proportionally based on annual sales
 *
 * @param {Array} products - Array of product objects
 * @param {number} dealSizeCases - Total number of cases in the deal
 * @returns {Array} Updated products with bulkCases assigned
 */
function allocateProportional(products, dealSizeCases) {
  // Calculate total annual cases
  const totalAnnual = products.reduce((sum, p) => sum + p.annualCases, 0);

  if (totalAnnual <= 0) {
    throw new Error("Total annual cases must be greater than zero");
  }

  // Calculate raw case allocation and initial floor allocation
  let allocatedProducts = products.map(product => {
    const rawCases = dealSizeCases * (product.annualCases / totalAnnual);
    const bulkCases = Math.floor(rawCases);

    return {
      ...product,
      rawCases,
      bulkCases,
      remainder: rawCases - bulkCases // Fractional part
    };
  });

  // Calculate leftover cases
  let allocatedCases = allocatedProducts.reduce((sum, p) => sum + p.bulkCases, 0);
  let leftover = dealSizeCases - allocatedCases;

  // Sort by remainder in descending order for leftover distribution
  allocatedProducts.sort((a, b) => b.remainder - a.remainder);

  // Distribute leftover cases
  for (let i = 0; i < leftover && i < allocatedProducts.length; i++) {
    allocatedProducts[i].bulkCases += 1;
  }

  // Clean up temporary properties
  allocatedProducts = allocatedProducts.map(p => {
    const { rawCases, remainder, ...rest } = p;
    return rest;
  });

  return allocatedProducts;
}

/**
 * Run optimization iterations to improve ROI through case swaps
 *
 * @param {Array} products - Array of product objects with initial bulkCases
 * @param {Object} params - Calculation parameters
 * @param {number|string} params.iterations - Number of iterations or 'auto'
 * @param {number} params.minDaysStock - Minimum days of stock required
 * @param {number} params.paymentTermsDays - Payment terms in days
 * @returns {Object} Updated products and iteration history
 */
function runIterations(products, params) {
  const { iterations, minDaysStock, paymentTermsDays } = params;
  const history = [];
  let iterationCount = 0;
  const maxIterations = iterations === 'auto' ? 100 : parseInt(iterations);
  let improved = true;

  // Deep copy products to avoid modifying the original
  let currentProducts = JSON.parse(JSON.stringify(products));

  // Initial portfolio ROI calculation
  let portfolioROI = calculatePortfolioROI(currentProducts, params);
  history.push({
    iteration: 0,
    totalROI: portfolioROI,
    products: JSON.parse(JSON.stringify(currentProducts))
  });

  // Run iterations
  while (improved && iterationCount < maxIterations) {
    improved = false;
    iterationCount++;

    // Find lowest and highest ROI products
    let lowestROIProduct = null;
    let highestROIProduct = null;
    let lowestROI = Infinity;
    let highestROI = -Infinity;

    // Calculate ROI for each product
    const productsWithROI = currentProducts.map(product => {
      const roi = computeLineItemROI({
        annualCases: product.annualCases,
        bottlesPerCase: product.bottlesPerCase,
        priceSmall: product.priceSmall,
        priceBulk: product.priceBulk,
        bulkCases: product.bulkCases,
        smallDealBottles: calculateSmallDealBottles(product, params),
        onHandCases: product.onHandCases,
        paymentTermsDays,
        minDaysStock
      }).annualizedRoi;

      if (roi < lowestROI && product.bulkCases > 0) {
        lowestROI = roi;
        lowestROIProduct = product;
      }

      if (roi > highestROI && product.bulkCases < product.annualCases) {
        highestROI = roi;
        highestROIProduct = product;
      }

      return { ...product, roi };
    });

    // Try a swap if we found candidates
    if (lowestROIProduct && highestROIProduct) {
      // Create a test copy
      const testProducts = JSON.parse(JSON.stringify(currentProducts));

      // Find indexes of the products
      const lowIndex = testProducts.findIndex(p => p.id === lowestROIProduct.id);
      const highIndex = testProducts.findIndex(p => p.id === highestROIProduct.id);

      // Perform the swap
      testProducts[lowIndex].bulkCases -= 1;
      testProducts[highIndex].bulkCases += 1;

      // Check minimum days stock requirements
      const lowStockValid = checkMinDaysStock(testProducts[lowIndex], minDaysStock);
      const highStockValid = checkMinDaysStock(testProducts[highIndex], minDaysStock);

      if (lowStockValid && highStockValid) {
        // Calculate new portfolio ROI
        const newPortfolioROI = calculatePortfolioROI(testProducts, params);

        // Accept the swap if it improves the portfolio ROI
        if (newPortfolioROI > portfolioROI) {
          currentProducts = testProducts;
          portfolioROI = newPortfolioROI;
          improved = true;

          // Record this iteration
          history.push({
            iteration: iterationCount,
            totalROI: portfolioROI,
            swapped: {
              from: lowestROIProduct.name,
              to: highestROIProduct.name
            },
            products: JSON.parse(JSON.stringify(currentProducts))
          });
        }
      }
    }

    // Break if no improvement and we're in auto mode
    if (!improved && iterations === 'auto') {
      break;
    }
  }

  return {
    products: currentProducts,
    history,
    totalIterations: iterationCount,
    finalROI: portfolioROI
  };
}

/**
 * Helper function to calculate small deal bottles based on product and parameters
 *
 * @param {Object} product - Product object
 * @param {Object} params - Calculation parameters
 * @returns {number} Number of bottles in small deal
 */
function calculateSmallDealBottles(product, params) {
  const smallDealCases = Math.min(product.bulkCases, params.smallDealMinimum);
  return smallDealCases * product.bottlesPerCase;
}

/**
 * Helper function to check if a product meets minimum days stock requirement
 *
 * @param {Object} product - Product object
 * @param {number} minDaysStock - Minimum days of stock required
 * @returns {boolean} True if minimum days stock requirement is met
 */
function checkMinDaysStock(product, minDaysStock) {
  if (!minDaysStock) return true;

  const dailyCases = product.annualCases / 365;
  const totalCases = product.onHandCases + product.bulkCases;
  const daysOfStock = dailyCases > 0 ? totalCases / dailyCases : Infinity;

  return daysOfStock >= minDaysStock;
}

/**
 * Calculate overall portfolio ROI
 *
 * @param {Array} products - Array of product objects
 * @param {Object} params - Calculation parameters
 * @returns {number} Portfolio ROI
 */
function calculatePortfolioROI(products, params) {
  let totalInvestment = 0;
  let totalSavings = 0;

  products.forEach(product => {
    const result = computeLineItemROI({
      annualCases: product.annualCases,
      bottlesPerCase: product.bottlesPerCase,
      priceSmall: product.priceSmall,
      priceBulk: product.priceBulk,
      bulkCases: product.bulkCases,
      smallDealBottles: calculateSmallDealBottles(product, params),
      onHandCases: product.onHandCases,
      paymentTermsDays: params.paymentTermsDays,
      minDaysStock: params.minDaysStock
    });

    if (!result.error) {
      totalInvestment += result.avgInvestment;
      totalSavings += result.savings;
    }
  });

  return totalInvestment > 0 ? totalSavings / totalInvestment : 0;
}

// Export functions for use in other modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    computeLineItemROI,
    allocateProportional,
    runIterations,
    calculatePortfolioROI
  };
}
