# Ui Tests

Generated : 2026-02-28 19:12
Base URL  : https://www.calculator.net/
Scenarios : 1

tags: ui, automated

## Verify Loan Calculator Heading [TC_019]

tags: low, TC_019

<!-- Pre: Navigate to page URL -->

* Navigate to url "https://www.calculator.net/loan-calculator.html"
* Verify element with xpath "//h1" is visible
* Verify test outcome is "Loan calculator heading displayed correctly"
