# Navigation Tests

Generated : 2026-02-28 11:34
Base URL  : https://www.calculator.net/
Scenarios : 7

tags: navigation, automated

## Navigation to homepage

tags: smoke, high, TC_005

<!-- Pre: User is on the calculator page -->

* Click on link with id <logo>
* Verify test outcome is <User is redirected to homepage>

## Navigation: Calculate Button

tags: medium, TC_011

<!-- Pre: User is on the loan calculator page -->

* Click on button with name <Calculate>
* Verify element with xpath <//div[@id='results']//h1> is visible
* Verify test outcome is <Calculation result page title displayed>

## Navigation: Every Unique Link

tags: smoke, high, TC_016

<!-- Pre: User is on the math calculator page -->

* Click on link with id <link1>
* Verify element with id <url> is visible
* Verify test outcome is <Correct link URL displayed>

## Navigation: every link loads the correct page

tags: smoke, high, TC_021

<!-- Pre: User is on the page -->

* Click on link with link text <Calculator>
* Click on link with link text <About>
* Verify test outcome is <Correct page appears after clicking link>

## Navigation: every unique link navigates to correct URL

tags: smoke, high, TC_036

<!-- Pre: User is on the page -->

* Click on link with text <About Us>
* Click on link with text <Contact Us>
* Verify test outcome is <Correct page loaded>

## Navigation: Logo/Home Link

tags: smoke, high, TC_040

<!-- Pre: User is on the salary calculator page -->

* Click on link with link text <Calculator.net>
* Verify test outcome is <User is redirected to homepage>

## Navigation: Link to Homepage

tags: smoke, low, TC_052

<!-- Pre: User is on the credit card calculator page -->

* Click on link with link text <Calculator.net>
* Verify test outcome is <Link to homepage works>
