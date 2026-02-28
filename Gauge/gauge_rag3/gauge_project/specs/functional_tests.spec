# Functional Tests

Generated : 2026-02-28 11:34
Base URL  : https://www.calculator.net/
Scenarios : 29

tags: functional, automated

## Calculator loads without error

tags: smoke, high, TC_001

<!-- Pre: User is on the calculator page -->

* Navigate to url <https://www.calculator.net/>
* Verify test outcome is <Calculator page loads without error>

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

## Invalid Input: Loan Amount and Rate

tags: smoke, medium, TC_008

<!-- Pre: User is on the loan calculator page -->

* Enter <abc> in input with name <loanamount>
* Enter <abc> in input with name <annualrate>
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

## Invalid Inputs: Text in Number Fields

tags: regression, medium, TC_015

<!-- Pre: User is on the math calculator page -->

* Enter <abc> in input with id <num1>
* Click on button with id <calculate>
* Verify element with id <error> is visible
* Verify test outcome is <Validation message displayed>

## Happy path: valid submission succeeds

tags: smoke, high, TC_018

<!-- Pre: User is on the page -->

* Enter <10000> in input with id <loanAmount>
* Enter <5> in input with id <interestRate>
* Enter <3> in input with id <term>
* Click on button with id <calculate>
* Verify element with css <.result> is visible
* Verify test outcome is <Result section appears with correct calculation>

## Empty required fields: validation shown

tags: smoke, high, TC_019

<!-- Pre: User is on the page -->

* Clear field with id <loanAmount>
* Clear field with id <interestRate>
* Click on button with id <calculate>
* Verify element with css <.error> is visible
* Verify test outcome is <Error message appears with correct text>

## Invalid format: error shown

tags: regression, medium, TC_020

<!-- Pre: User is on the page -->

* Enter <10000> in input with id <loanAmount>
* Enter <abc> in input with id <interestRate>
* Click on button with id <calculate>
* Verify element with css <.error> is visible
* Verify test outcome is <Error message appears with correct text>

## Page Loads Without Error

tags: smoke, high, TC_023

<!-- Pre: User is on the page -->

* Verify element with url <https://www.calculator.net/about-us.html> is visible
* Verify test outcome is <Page loads without error>

## H1 Heading Present and Matches Page Topic

tags: smoke, high, TC_024

<!-- Pre: User is on the page -->

* Verify element with xpath <//h1> is visible
* Verify test outcome is <H1 heading present and matches page topic>

## All Navigation Links Functional

tags: smoke, high, TC_025

<!-- Pre: User is on the page -->

* Click on link with xpath <//a>
* Verify test outcome is <All navigation links are functional>

## No Broken Links

tags: smoke, high, TC_027

<!-- Pre: User is on the page -->

* Verify element with xpath <//a> is visible
* Verify test outcome is <No broken links>

## Happy path: all valid inputs → success

tags: smoke, high, TC_032

<!-- Pre: User is on the page -->

* Enter <1000> in input with id <amount>
* Enter <5> in input with id <taxRate>
* Click on button with id <calculate>
* Verify test outcome is <Calculation result displayed>

## Empty required fields → all required errors

tags: smoke, high, TC_033

<!-- Pre: User is on the page -->

* Clear field with id <amount>
* Clear field with id <taxRate>
* Click on button with id <calculate>
* Verify test outcome is <All required errors displayed>

## One empty, rest valid → error on empty field only

tags: smoke, high, TC_034

<!-- Pre: User is on the page -->

* Enter <1000> in input with id <amount>
* Clear field with id <taxRate>
* Click on button with id <calculate>
* Verify test outcome is <Error on empty field only>

## One invalid, rest valid → error on invalid field only

tags: smoke, high, TC_035

<!-- Pre: User is on the page -->

* Enter <abc> in input with id <amount>
* Enter <5> in input with id <taxRate>
* Click on button with id <calculate>
* Verify test outcome is <Error on invalid field only>

## Happy Path: All Valid Inputs

tags: smoke, high, TC_037

<!-- Pre: User is on the salary calculator page -->

* Enter <100000> in input with id <salary>
* Enter <5> in input with id <rate>
* Click on button with id <calculate>
* Verify test outcome is <Result section displays calculation result>

## Empty Required Fields

tags: smoke, high, TC_038

<!-- Pre: User is on the salary calculator page -->

* Clear field with id <salary>
* Clear field with id <rate>
* Click on button with id <calculate>
* Verify test outcome is <Validation errors appear for empty fields>

## Invalid Input: Text in Number Field

tags: medium, TC_039

<!-- Pre: User is on the salary calculator page -->

* Enter <abc> in input with id <salary>
* Verify test outcome is <Error message appears for invalid input>

## Page loads without error

tags: smoke, high, TC_042

<!-- Pre: User is on the page -->

* Verify element with url <https://www.calculator.net/other-calculator.html> is visible
* Verify test outcome is <Page loads without error>

## H1 heading present and matches page topic

tags: smoke, high, TC_043

<!-- Pre: User is on the page -->

* Verify element with text <Other Calculators> is visible
* Verify test outcome is <H1 heading present and matches page topic>

## All navigation links functional

tags: smoke, high, TC_044

<!-- Pre: User is on the page -->

* Click on link with text <Calculator>
* Verify element with url <https://www.calculator.net/calculator.html> is visible
* Verify test outcome is <All navigation links functional>

## Happy Path: Valid Inputs

tags: smoke, high, TC_049

<!-- Pre: User is on the credit card calculator page -->

* Enter <10000> in input with id <loanAmount>
* Enter <5> in input with id <interestRate>
* Enter <3> in input with id <years>
* Click on button with id <calculate>
* Verify element with css <.result> is visible
* Verify test outcome is <Calculator returns correct result>

## Empty Required Fields: Validation Errors

tags: smoke, high, TC_050

<!-- Pre: User is on the credit card calculator page -->

* Clear field with id <loanAmount>
* Click on button with id <calculate>
* Verify element with css <.error-message> is visible
* Verify test outcome is <Calculator shows validation errors>

## Invalid Inputs: Error Messages

tags: regression, medium, TC_051

<!-- Pre: User is on the credit card calculator page -->

* Enter <abc> in input with id <loanAmount>
* Click on button with id <calculate>
* Verify element with css <.error-message> is visible
* Verify test outcome is <Calculator shows error messages>
