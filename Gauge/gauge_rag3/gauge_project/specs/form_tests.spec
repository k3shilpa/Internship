# Form Tests

Generated : 2026-02-28 11:34
Base URL  : https://www.calculator.net/
Scenarios : 10

tags: form, automated

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

## Calculator form invalid input

tags: medium, TC_004

<!-- Pre: User is on the calculator page -->

* Enter <abc> in input with id <amount>
* Enter <abc> in input with id <rate>
* Enter <abc> in input with id <time>
* Click on button with id <calculate>
* Verify test outcome is <Error messages are displayed>

## Empty Required Fields Show Validation Errors

tags: medium, TC_028

<!-- Pre: User is on the page -->

* Clear field with xpath <//input>
* Verify test outcome is <Empty required fields show validation errors>

## Invalid Formats Show Appropriate Errors

tags: medium, TC_029

<!-- Pre: User is on the page -->

* Enter <invalid format> in input with xpath <//input>
* Verify test outcome is <Invalid formats show appropriate errors>

## Clear Button Resets All Fields

tags: medium, TC_030

<!-- Pre: User is on the page -->

* Click on button with xpath <//button>
* Verify test outcome is <Clear button resets all fields>

## Submit Button Disabled State

tags: low, TC_031

<!-- Pre: User is on the page -->

* Verify element with xpath <//button> is visible
* Verify test outcome is <Submit button is in correct state>

## Happy path: all valid inputs → success

tags: smoke, high, TC_046

<!-- Pre: User is on the page -->

* Enter <10> in input with id <field1>
* Enter <20> in input with id <field2>
* Click on button with id <submitButton>
* Verify test outcome is <Happy path: all valid inputs → success>

## Empty required fields: validation shown

tags: smoke, high, TC_047

<!-- Pre: User is on the page -->

* Clear field with id <field1>
* Click on button with id <submitButton>
* Verify test outcome is <Empty required fields: validation shown>

## Invalid formats: appropriate errors

tags: smoke, high, TC_048

<!-- Pre: User is on the page -->

* Enter <abc> in input with id <field1>
* Click on button with id <submitButton>
* Verify test outcome is <Invalid formats: appropriate errors>
