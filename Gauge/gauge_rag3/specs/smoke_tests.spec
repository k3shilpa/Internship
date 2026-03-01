# Smoke Tests — High Priority

Generated : 2026-03-01 11:52
Base URL  : https://www.calculator.net/

tags: smoke, high-priority, automated

## Calculator loads successfully [TC_001]

tags: smoke, high, TC_001

<!-- Pre: Navigate to page URL -->

* Navigate to url "https://www.calculator.net/"
* Verify heading with xpath "//h1" contains "Free Online Calculators"
* Verify test outcome is "Calculator loads successfully"

## Mortgage calculator functionality [TC_002]

tags: smoke, high, TC_002

<!-- Pre: Navigate to page URL -->

* Navigate to url "https://www.calculator.net/"
* Click on link with text "Mortgage Calculator"
* Verify test outcome is "Search results displayed"

## Sign in functionality [TC_003]

tags: smoke, high, TC_003

<!-- Pre: Navigate to page URL -->

* Navigate to url "https://www.calculator.net/"
* Click on link with text "sign in"
* Click on link with text "sign in"
* Verify test outcome is "User logged in successfully"

## Loan calculator functionality [TC_004]

tags: smoke, high, TC_004

<!-- Pre: Navigate to page URL -->

* Navigate to url "https://www.calculator.net/"
* Click on link with text "Loan Calculator"
* Verify test outcome is "Search results displayed"

## Navigate to IP Subnet Calculator page [TC_005]

tags: smoke, high, TC_005

<!-- Pre: Navigate to page URL -->

* Navigate to url "https://www.calculator.net/ip-subnet-calculator.html"
* Verify test outcome is "Page loads successfully"

## Submit valid IP and subnet [TC_006]

tags: high, TC_006

<!-- Pre: Navigate to page URL -->

* Navigate to url "https://www.calculator.net/ip-subnet-calculator.html"
* Enter "192.168.1.1" in input with id "c6ip"
* Enter "255.255.255.0" in input with id "c6subnet"
* Click on button with name "x"
* Verify test outcome is "Result displayed successfully"

## Submit empty IP and subnet [TC_007]

tags: high, TC_007

<!-- Pre: Navigate to page URL -->

* Navigate to url "https://www.calculator.net/ip-subnet-calculator.html"
* Clear field with id "c6ip"
* Clear field with id "c6subnet"
* Verify test outcome is "Error: IP address required and Error: Subnet mask required"

## Time Calculator Page Loads Successfully [TC_009]

tags: smoke, high, TC_009

<!-- Pre: Navigate to page URL -->

* Navigate to url "https://www.calculator.net/time-calculator.html"
* Verify heading with xpath "//h1" contains "Time Calculator"
* Verify test outcome is "Page title is displayed correctly"

## Add Time to a Date [TC_010]

tags: smoke, high, TC_010

<!-- Pre: Navigate to page URL -->

* Navigate to url "https://www.calculator.net/time-calculator.html"
* Enter "2022-01-01" in input with id "tcday1"
* Enter "2" in input with id "tchour1"
* Enter "30" in input with id "tcminute1"
* Click on button with name "x"
* Verify test outcome is "Result is displayed correctly"

## Subtract Time from a Date [TC_011]

tags: smoke, high, TC_011

<!-- Pre: Navigate to page URL -->

* Navigate to url "https://www.calculator.net/time-calculator.html"
* Enter "2022-01-01" in input with id "tcday1"
* Enter "2" in input with id "tchour1"
* Enter "30" in input with id "tcminute1"
* Click on button with name "x"
* Verify test outcome is "Result is displayed correctly"
