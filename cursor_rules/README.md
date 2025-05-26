# Cursor Rules Setup Instructions

## Installation Steps:

1. Copy the entire `cursor_rules` folder to your project root directory
2. Rename it to `.cursor` (note the dot at the beginning)
3. The files should end up at: `your_project/.cursor/rules/`

## File Structure:
```
your_project/
├── .cursor/
│   └── rules/
│       ├── playwright_mcp_workflow.mdc
│       ├── python_testing_standards.mdc
│       ├── continuous_improvement.mdc
│       └── mcp_tool_usage.mdc
├── your_code.py
└── other_files...
```

## Activation:
- Restart Cursor or reload the window after copying files
- Rules will automatically apply to all AI interactions in that project
- `category: always` rules are included in every conversation
- `category: auto_attached` rules activate when working with matching file types

## What These Updated Rules Do:

### Enhanced MCP Testing Protocol:
- Force comprehensive testing of all 6 calculators with realistic scenarios
- Require validation of financial calculations with known test cases
- Test error handling with invalid inputs (negative prices, missing data)
- Verify Excel report generation and file integrity
- Test scenario management (save/load/delete) functionality

### Improved Python Standards:
- Enforce comprehensive input validation on all API endpoints
- Require type hints with specific types (Dict[str, Any], Optional[float])
- Mandate structured error responses with user-friendly messages
- Add configuration management for hardcoded values
- Require audit logging for financial calculations

### Advanced Improvement Suggestions:
- Calculator-specific optimization recommendations
- Performance monitoring and caching suggestions
- Security enhancements (CSRF protection, file upload validation)
- Comprehensive test coverage requirements
- Technical debt identification and prioritization

### Detailed MCP Testing Workflows:
- End-to-end testing scenarios for each calculator type
- Performance validation for complex calculations
- Cross-browser and mobile responsiveness testing
- Error scenario testing with edge cases
- Regression testing for bug fixes

## Report Builder Specific Features:
- Business logic validation (bulk_price < regular_price)
- ROI algorithm accuracy verification
- Excel parsing and generation testing
- Scenario persistence validation
- Multi-product optimization progress tracking