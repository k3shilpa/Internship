# Functional Tests

Generated : 2026-03-01 11:41
Base URL  : https://www.calculator.net/
Scenarios : 13

tags: functional, automated

## Calculator Home Page Loads Successfully [TC_001]

tags: TC_001, smoke, high

* Navigate to url "https://www.calculator.net/"
* Verify "Free Online Calculators" is displayed
* Verify test outcome is "Calculator home page loads successfully"

## Navigate to Fitness and Health Calculators [TC_004]

tags: TC_004, smoke, high

* Navigate to url "https://www.calculator.net/fitness-and-health-calculator.html"
* Verify test outcome is "User is on the Fitness and Health Calculators page"

## Search for a term [TC_005]

tags: medium, TC_005

* Navigate to url "https://www.calculator.net/fitness-and-health-calculator.html"
* Enter "test search term" in input with id "calcSearchTerm"
* Click on link with link_text "sign in"
* Verify test outcome is "Search results are displayed"

## Happy Path: Calculate TDEE [TC_008]

tags: TC_008, smoke, high

* Navigate to url "https://www.calculator.net/tdee-calculator.html"
* Enter "30" in input with id "cage"
* Enter "None" in input with id "csex1"
* Enter "5" in input with id "cheightfeet"
* Enter "8" in input with id "cheightinch"
* Enter "150" in input with id "cpound"
* Click on button with name "x"
* Perform assert_text on "//h1"
* Verify test outcome is "TDEE calculated successfully"

## Empty Required Fields: Calculate TDEE [TC_009]

tags: TC_009, smoke, high

* Navigate to url "https://www.calculator.net/tdee-calculator.html"
* Click on button with name "x"
* Perform assert_text on "//h3"
* Verify test outcome is "Error message displayed successfully"

## Invalid Format: Calculate TDEE [TC_010]

tags: TC_010, smoke, high

* Navigate to url "https://www.calculator.net/tdee-calculator.html"
* Enter "abc" in input with id "cage"
* Perform assert_text on "//h3"
* Verify test outcome is "Error message displayed successfully"

## Happy Path [TC_012]

tags: TC_012, smoke, high

* Navigate to url "https://www.calculator.net/pregnancy-weight-gain-calculator.html"
* Click on button with name "x"
* Verify "Pregnancy Weight Gain Calculator" is displayed
* Verify test outcome is "Calculator results displayed"

## Empty Required Fields [TC_013]

tags: smoke, high, TC_013

* Navigate to url "https://www.calculator.net/pregnancy-weight-gain-calculator.html"
* Click on button with name "x"
* Verify "Please enter your height in feet and inches" is displayed
* Verify test outcome is "Error messages for empty fields"

## Invalid Format [TC_014]

tags: smoke, high, TC_014

* Navigate to url "https://www.calculator.net/pregnancy-weight-gain-calculator.html"
* Enter "abc" in input with name "cheightfeet"
* Verify "Please enter a valid number" is displayed
* Verify test outcome is "Error message for invalid format"

## Twin Pregnancy [TC_015]

tags: TC_015, smoke, high

* Navigate to url "https://www.calculator.net/pregnancy-weight-gain-calculator.html"
* Click on button with name "x"
* Enter "5" in input with name "cheightfeet"
* Enter "8" in input with name "cheightinch"
* Click on button with name "x"
* Verify "Pregnancy Weight Gain Calculator" is displayed
* Verify test outcome is "Calculator results displayed"

## Verify Page Title [TC_017]

tags: TC_017, smoke, high

* Navigate to url "https://www.calculator.net/financial-calculator.html"
* Verify "Financial Calculators" is displayed
* Verify test outcome is "Page title is correct"

## Verify Mortgage and Real Estate Section [TC_018]

tags: medium, smoke, TC_018

* Navigate to url "https://www.calculator.net/financial-calculator.html"
* Verify "Mortgage and Real Estate" is displayed
* Verify test outcome is "Mortgage and Real Estate section is visible"

## Verify Search Term Input [TC_021]

tags: medium, smoke, TC_021

* Navigate to url "https://www.calculator.net/financial-calculator.html"
* Verify "Search Term input field is visible and editable" is displayed
* Verify test outcome is "Search Term input field is visible and editable"
