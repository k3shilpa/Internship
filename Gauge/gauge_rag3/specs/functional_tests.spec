# Functional Tests

Generated : 2026-02-28 19:12
Base URL  : https://www.calculator.net/
Scenarios : 36

tags: functional, automated

## Calculator loads successfully [TC_001]

tags: smoke, high, TC_001

<!-- Pre: Navigate to page URL -->

* Navigate to url "https://www.calculator.net/"
* Verify element with xpath "//h1" is visible
* Verify test outcome is "Calculator loads successfully"

## Search calculator functionality [TC_002]

tags: smoke, high, TC_002

<!-- Pre: Navigate to page URL -->

* Navigate to url "https://www.calculator.net/"
* Verify test outcome is "Search calculator functionality works"

## Mortgage calculator functionality [TC_003]

tags: smoke, high, TC_003

<!-- Pre: Navigate to page URL -->

* Navigate to url "https://www.calculator.net/"
* Click on link with link_text "Mortgage Calculator"
* Verify test outcome is "Mortgage calculator functionality works"

## Loan calculator functionality [TC_004]

tags: smoke, high, TC_004

<!-- Pre: Navigate to page URL -->

* Navigate to url "https://www.calculator.net/"
* Click on link with link_text "Loan Calculator"
* Verify test outcome is "Loan calculator functionality works"

## Auto loan calculator functionality [TC_005]

tags: smoke, high, TC_005

<!-- Pre: Navigate to page URL -->

* Navigate to url "https://www.calculator.net/"
* Click on link with link_text "Auto Loan Calculator"
* Verify test outcome is "Auto loan calculator functionality works"

## Interest calculator functionality [TC_006]

tags: smoke, high, TC_006

<!-- Pre: Navigate to page URL -->

* Navigate to url "https://www.calculator.net/"
* Click on link with link_text "Interest Calculator"
* Verify test outcome is "Interest calculator functionality works"

## Payment calculator functionality [TC_007]

tags: smoke, high, TC_007

<!-- Pre: Navigate to page URL -->

* Navigate to url "https://www.calculator.net/"
* Click on link with link_text "Payment Calculator"
* Verify test outcome is "Payment calculator functionality works"

## Retirement calculator functionality [TC_008]

tags: smoke, high, TC_008

<!-- Pre: Navigate to page URL -->

* Navigate to url "https://www.calculator.net/"
* Click on link with link_text "Retirement Calculator"
* Verify test outcome is "Retirement calculator functionality works"

## Amortization calculator functionality [TC_009]

tags: smoke, high, TC_009

<!-- Pre: Navigate to page URL -->

* Navigate to url "https://www.calculator.net/"
* Click on link with link_text "Amortization Calculator"
* Verify test outcome is "Amortization calculator functionality works"

## Investment calculator functionality [TC_010]

tags: smoke, high, TC_010

<!-- Pre: Navigate to page URL -->

* Navigate to url "https://www.calculator.net/"
* Click on link with link_text "Investment Calculator"
* Verify test outcome is "Investment calculator functionality works"

## Inflation calculator functionality [TC_011]

tags: smoke, high, TC_011

<!-- Pre: Navigate to page URL -->

* Navigate to url "https://www.calculator.net/"
* Click on link with link_text "Inflation Calculator"
* Verify test outcome is "Inflation calculator functionality works"

## Mortgage calculator functionality with valid input [TC_012]

tags: smoke, medium, TC_012

<!-- Pre: Navigate to page URL -->

* Navigate to url "https://www.calculator.net/"
* Click on link with link_text "Mortgage Calculator"
* Verify test outcome is "Mortgage calculator functionality works with valid input"

## Loan calculator functionality with valid input [TC_013]

tags: smoke, medium, TC_013

<!-- Pre: Navigate to page URL -->

* Navigate to url "https://www.calculator.net/"
* Click on link with link_text "Loan Calculator"
* Verify test outcome is "Loan calculator functionality works with valid input"

## Auto loan calculator functionality with valid input [TC_014]

tags: general, auto-generated, medium, TC_014

<!-- Pre: Navigate to page URL -->

* Navigate to url "https://www.calculator.net/"
* Click on link with link_text "Auto Loan Calculator"
* Verify test outcome is "Test passes"

## Navigate to Loan Calculator Page [TC_015]

tags: smoke, high, TC_015

<!-- Pre: Navigate to page URL -->

* Navigate to url "https://www.calculator.net/loan-calculator.html"
* Verify test outcome is "Loan calculator page loaded"

## Submit Loan Calculator with Valid Inputs [TC_016]

tags: smoke, high, TC_016

<!-- Pre: Navigate to page URL -->

* Navigate to url "https://www.calculator.net/loan-calculator.html"
* Enter "5" in input with id "rate"
* Click on button with name "x"
* Verify test outcome is "Loan calculation result displayed"

## Submit Loan Calculator with Empty Required Fields [TC_017]

tags: smoke, high, TC_017

<!-- Pre: Navigate to page URL -->

* Navigate to url "https://www.calculator.net/loan-calculator.html"
* Enter "value" in input with id "rate"
* Click on button with name "x"
* Verify test outcome is "Validation errors displayed"

## Loan Calculator Page Loads Successfully [TC_020]

tags: smoke, high, TC_020

<!-- Pre: Navigate to page URL -->

* Navigate to url "https://www.calculator.net/loan-calculator.html#fixedend"
* Verify element with xpath "//h1" is visible
* Verify test outcome is "Page title is correct"

## Calculate Loan Payment with Valid Inputs [TC_021]

tags: high, TC_021

<!-- Pre: Navigate to page URL -->

* Navigate to url "https://www.calculator.net/loan-calculator.html#fixedend"
* Click on button with name "x"
* Verify element with css "h2.h2result" is visible
* Verify test outcome is "Loan payment is calculated correctly"

## Empty Required Fields Show Validation Errors [TC_022]

tags: high, TC_022

<!-- Pre: Navigate to page URL -->

* Navigate to url "https://www.calculator.net/loan-calculator.html#fixedend"
* Click on button with name "x"
* Verify element with css "h2.h2red" is visible
* Verify test outcome is "Validation errors are shown for empty required fields"

## Invalid Inputs Show Error Messages [TC_023]

tags: high, TC_023

<!-- Pre: Navigate to page URL -->

* Navigate to url "https://www.calculator.net/loan-calculator.html#fixedend"
* Click on button with name "x"
* Verify element with css "h2.h2red" is visible
* Verify test outcome is "Error messages are shown for invalid inputs"

## Clear Button Resets All Fields [TC_024]

tags: high, TC_024

<!-- Pre: Navigate to page URL -->

* Navigate to url "https://www.calculator.net/loan-calculator.html#fixedend"
* Click on button with name "x"
* Click on button with name "x"
* Verify element with css "h2.h2result" is visible
* Verify test outcome is "All fields are reset correctly"

## Verify Calculator Form Fields [TC_027]

tags: functional, high, TC_027

<!-- Pre: Page is open -->

* Navigate to url "https://www.calculator.net/math-calculator.html"
* Verify element with id "calcSearchTerm" is visible
* Verify element with name "calcSearchTerm" is visible
* Verify test outcome is "Search term field is present and enabled"

## Submit Calculator Form with Empty Required Fields [TC_028]

tags: functional, high, TC_028

<!-- Pre: Page is open -->

* Navigate to url "https://www.calculator.net/math-calculator.html"
* Verify test outcome is "Error message is displayed"

## Interest Rate Calculator Happy Path [TC_030]

tags: smoke, high, TC_030

<!-- Pre: Navigate to the interest rate calculator page -->

* Navigate to url "https://www.calculator.net/interest-rate-calculator.html"
* Enter "10000" in input with id "cloanamount"
* Enter "5" in input with id "cloanterm"
* Click on button with name "x"
* Verify element with css "h2.h2result" is visible
* Verify test outcome is "Calculation result displayed"

## Interest Rate Calculator Empty Fields [TC_031]

tags: smoke, high, TC_031

<!-- Pre: Navigate to the interest rate calculator page -->

* Navigate to url "https://www.calculator.net/interest-rate-calculator.html"
* Enter "value" in input with id "cloanamount"
* Enter "value" in input with id "cloanterm"
* Verify test outcome is "Error messages displayed for empty fields"

## Interest Rate Calculator Invalid Inputs [TC_032]

tags: smoke, high, TC_032

<!-- Pre: Navigate to the interest rate calculator page -->

* Navigate to url "https://www.calculator.net/interest-rate-calculator.html"
* Enter "abc" in input with id "cloanamount"
* Enter "abc" in input with id "cloanterm"
* Verify test outcome is "Error messages displayed for invalid inputs"

## About Us Page Loads Successfully [TC_034]

tags: smoke, high, TC_034

<!-- Pre: Navigate to the About Us page -->

* Navigate to url "https://www.calculator.net/about-us.html"
* Verify element with xpath "//h1" is visible
* Verify test outcome is "Page loads successfully with correct title"

## Calculate Salary with Valid Inputs [TC_044]

tags: smoke, high, TC_044

<!-- Pre: Navigate to page URL -->

* Navigate to url "https://www.calculator.net/salary-calculator.html"
* Enter "10000" in input with id "camount"
* Enter "40" in input with id "chours"
* Click on button with name "x"
* Verify test outcome is "Calculation result displayed"

## Calculate Salary with Empty Required Fields [TC_045]

tags: smoke, high, TC_045

<!-- Pre: Navigate to page URL -->

* Navigate to url "https://www.calculator.net/salary-calculator.html"
* Enter "value" in input with id "camount"
* Enter "value" in input with id "chours"
* Click on button with name "x"
* Verify test outcome is "Error messages displayed for empty fields"

## Calculate Salary with Invalid Inputs [TC_046]

tags: smoke, high, TC_046

<!-- Pre: Navigate to page URL -->

* Navigate to url "https://www.calculator.net/salary-calculator.html"
* Enter "abc" in input with id "camount"
* Enter "abc" in input with id "chours"
* Click on button with name "x"
* Verify test outcome is "Error messages displayed for invalid fields"

## Verify Search functionality [TC_049]

tags: functional, medium, TC_049

<!-- Pre: Navigate to Other Calculators page -->

* Navigate to url "https://www.calculator.net/other-calculator.html"
* Verify element with css "//h1" is visible
* Verify test outcome is "Search results appear"

## Submit valid data [TC_061]

tags: smoke, high, TC_061

<!-- Pre: User is on the credit card calculator page -->

* Navigate to url "https://www.calculator.net/credit-card-calculator.html"
* Enter "10000" in input with id "balance"
* Enter "5" in input with id "rate"
* Click on button with name "x"
* Verify test outcome is "User gets the correct result"

## Submit empty required fields [TC_062]

tags: smoke, high, TC_062

<!-- Pre: User is on the credit card calculator page -->

* Navigate to url "https://www.calculator.net/credit-card-calculator.html"
* Enter "value" in input with id "balance"
* Enter "value" in input with id "rate"
* Click on button with name "x"
* Verify test outcome is "User gets validation errors"

## Submit invalid data [TC_063]

tags: smoke, high, TC_063

<!-- Pre: User is on the credit card calculator page -->

* Navigate to url "https://www.calculator.net/credit-card-calculator.html"
* Enter "abc" in input with id "balance"
* Enter "abc" in input with id "rate"
* Click on button with name "x"
* Verify test outcome is "User gets validation errors"

## Clear button [TC_064]

tags: smoke, high, TC_064

<!-- Pre: User is on the credit card calculator page -->

* Navigate to url "https://www.calculator.net/credit-card-calculator.html"
* Enter "10000" in input with id "balance"
* Enter "5" in input with id "rate"
* Click on button with name "x"
* Click on button with name "x"
* Verify test outcome is "All fields are empty"
