# Ui Tests

Generated : 2026-03-01 11:52
Base URL  : https://www.calculator.net/
Scenarios : 1

tags: ui, automated

## Verify Sitemap Heading [TC_016]

tags: ui, low, TC_016

<!-- Pre: Navigate to page URL -->

* Navigate to url "https://www.calculator.net/sitemap.html"
* Verify heading with xpath "//h1" contains "Sitemap heading is displayed correctly"
* Verify test outcome is "Sitemap heading is displayed correctly"
