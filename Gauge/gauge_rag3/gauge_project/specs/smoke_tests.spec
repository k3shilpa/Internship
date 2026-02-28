# Smoke Tests — High Priority

Generated : 2026-02-28 11:34
Base URL  : https://www.calculator.net/

tags: smoke, high-priority, automated

## Calculator loads without error

tags: smoke, high, TC_001

<!-- Pre: User is on the calculator page -->

* Navigate to url <https://www.calculator.net/>
* Verify test outcome is <Calculator page loads without error>

## Calculator form happy path

tags: smoke, high, TC_002

<!-- Pre: User is on the calculator page -->

* Enter <1000> in input with id <amount>
* Enter <5> in input with id <rate>
* Enter <3> in input with id <time>
* Click on button with id <calculate>
* Verify test outcome is <Calculation result is displayed>

## Calculator form empty required fields

tags: smoke, high, TC_003

<!-- Pre: User is on the calculator page -->

* Enter <value> in input with id <amount>
* Enter <value> in input with id <rate>
* Enter <value> in input with id <time>
* Click on button with id <calculate>
* Verify test outcome is <Error messages are displayed>

## Navigation to homepage

tags: smoke, high, TC_005

<!-- Pre: User is on the calculator page -->

* Click on link with id <logo>
* Verify test outcome is <User is redirected to homepage>

## Happy Path: Valid Loan Amount and Rate

tags: smoke, high, TC_006

<!-- Pre: User is on the loan calculator page -->

* Enter <100000> in input with name <loanamount>
* Enter <5> in input with name <annualrate>
* Click on button with name <Calculate>
* Verify element with css <.result> is visible
* Verify test outcome is <Monthly payment result displayed>

## Empty Required Fields: Loan Amount and Rate

tags: smoke, high, TC_007

<!-- Pre: User is on the loan calculator page -->

* Clear field with name <loanamount>
* Clear field with name <annualrate>
* Click on button with name <Calculate>
* Verify element with css <.error> is visible
* Verify test outcome is <Validation errors displayed>

## Happy Path: Valid Loan Amount and Interest Rate

tags: smoke, high, TC_009

<!-- Pre: User is on the loan calculator page -->

* Enter <100000> in input with name <loanamount>
* Enter <5> in input with name <interest>
* Click on button with name <Calculate>
* Verify element with xpath <//div[@id='results']//p> is visible
* Verify test outcome is <Monthly payment calculation result displayed>

## Negative Path: Empty Loan Amount

tags: smoke, high, TC_010

<!-- Pre: User is on the loan calculator page -->

* Clear field with name <loanamount>
* Click on button with name <Calculate>
* Verify element with xpath <//div[@id='error']//p> is visible
* Verify test outcome is <Error message for empty loan amount displayed>

## Happy Path: All Valid Inputs

tags: smoke, high, TC_013

<!-- Pre: User is on the math calculator page -->

* Enter <10> in input with id <num1>
* Enter <5> in input with id <num2>
* Click on button with id <calculate>
* Verify element with id <result> is visible
* Verify test outcome is <Calculation result displayed>

## Empty Required Fields: All Empty

tags: smoke, high, TC_014

<!-- Pre: User is on the math calculator page -->

* Clear field with id <num1>
* Clear field with id <num2>
* Click on button with id <calculate>
* Verify element with id <error> is visible
* Verify test outcome is <Validation message displayed>
