# Ui Tests

Generated : 2026-03-01 11:41
Base URL  : https://www.calculator.net/
Scenarios : 1

tags: ui, automated

## Verify heading text [TC_007]

tags: low, TC_007

* Navigate to url "https://www.calculator.net/fitness-and-health-calculator.html"
* Perform assert_text on "//h1"
* Verify test outcome is "Heading text is correct"
