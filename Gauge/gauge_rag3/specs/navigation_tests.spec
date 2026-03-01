# Navigation Tests

Generated : 2026-03-01 11:52
Base URL  : https://www.calculator.net/
Scenarios : 3

tags: navigation, automated

## Navigate to IP Subnet Calculator page [TC_005]

tags: smoke, high, TC_005

<!-- Pre: Navigate to page URL -->

* Navigate to url "https://www.calculator.net/ip-subnet-calculator.html"
* Verify test outcome is "Page loads successfully"

## Click on sign in link [TC_008]

tags: medium, TC_008

<!-- Pre: Navigate to page URL -->

* Navigate to url "https://www.calculator.net/ip-subnet-calculator.html"
* Click on link with text "sign in"
* Verify test outcome is "Navigated to sign in page"

## Verify Financial Calculators Link [TC_015]

tags: navigation, medium, TC_015

<!-- Pre: Navigate to page URL -->

* Navigate to url "https://www.calculator.net/sitemap.html"
* Verify test outcome is "Navigates to financial calculators page"
