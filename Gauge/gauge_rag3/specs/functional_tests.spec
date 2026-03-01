# Functional Tests

Generated : 2026-03-01 11:52
Base URL  : https://www.calculator.net/
Scenarios : 17

tags: functional, automated

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

## Time Calculator in Expression [TC_012]

tags: smoke, high, TC_012

<!-- Pre: Navigate to page URL -->

* Navigate to url "https://www.calculator.net/time-calculator.html"
* Enter "2 hours 30 minutes" in input with id "tcexpression"
* Click on button with name "x"
* Verify test outcome is "Result is displayed correctly"

## Invalid Input [TC_013]

tags: smoke, high, TC_013

<!-- Pre: Navigate to page URL -->

* Navigate to url "https://www.calculator.net/time-calculator.html"
* Enter "invalid" in input with id "tcday1"
* Verify test outcome is "Invalid input is handled correctly"

## Sitemap Page Loads Successfully [TC_014]

tags: smoke, high, TC_014

<!-- Pre: Navigate to page URL -->

* Navigate to url "https://www.calculator.net/sitemap.html"
* Verify test outcome is "Page loads successfully"

## Page Loads Successfully [TC_017]

tags: smoke, high, TC_017

<!-- Pre: Navigate to page URL -->

* Navigate to url "https://www.calculator.net/about-us.html#terms"
* Verify test outcome is "Page loaded without errors"

## Page Title is Correct [TC_018]

tags: smoke, high, TC_018

<!-- Pre: Page loaded successfully -->

* Navigate to url "https://www.calculator.net/about-us.html#terms"
* Verify heading with xpath "//h1" contains "About Us"
* Verify test outcome is "Page title is correct"

## Navigation Links are Functional [TC_019]

tags: smoke, high, TC_019

<!-- Pre: Page loaded successfully -->

* Navigate to url "https://www.calculator.net/about-us.html#terms"
* Click on link with text "about us"
* Click on link with text "sign in"
* Verify test outcome is "All navigation links are functional"

## Form Fields are Present [TC_020]

tags: medium, TC_020

<!-- Pre: Page loaded successfully -->

* Navigate to url "https://www.calculator.net/about-us.html#terms"
* Verify element with name "name1" is visible
* Verify element with name "email1" is visible
* Verify test outcome is "All form fields are present"

## Form Submission is Successful [TC_021]

tags: smoke, high, TC_021

<!-- Pre: Page loaded successfully -->

* Navigate to url "https://www.calculator.net/about-us.html#terms"
* Enter "John Doe" in input with name "name1"
* Enter "john.doe@example.com" in input with name "email1"
* Click on button with name "Submits"
* Verify test outcome is "Form submission is successful"
