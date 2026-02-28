# Accessibility Tests

Generated : 2026-02-28 12:01
Base URL  : https://www.calculator.net/
Scenarios : 6

tags: accessibility, automated

## Accessibility: images need alt text [TC_004]

tags: accessibility, medium, TC_004

<!-- Pre: User is on the calculator page -->

* Verify element with id "calculator-image" is visible
* Verify element with id "finance-image" is visible
* Verify element with id "science-image" is visible
* Verify test outcome is "All images have alt text"

## Accessibility: Alt Text for Images [TC_009]

tags: regression, low, TC_009

<!-- Pre: User is on the loan calculator page -->

* Verify element with css ".calculator-image" is visible
* Verify test outcome is "Alt text present"

## Accessibility: Alt Text [TC_019]

tags: low, TC_019

<!-- Pre: User is on the page -->

* Verify element with id "image1" is visible
* Verify element with id "image2" is visible
* Verify test outcome is "Alt text present"

## Accessibility: Image Alt Text [TC_024]

tags: low, TC_024

<!-- Pre: User is on the interest rate calculator page -->

* Verify element with id "calculator-image" is visible
* Verify test outcome is "Alt text should be present"

## All Images Have Alt Text [TC_028]

tags: smoke, high, TC_028

<!-- Pre: User is on the page -->

* Verify element with css "img" is visible
* Verify test outcome is "All images have alt text"

## All images have alt text [TC_045]

tags: accessibility, high, TC_045

<!-- Pre: User is on the page -->

* Verify element with css "img" is visible
* Verify test outcome is "All images have alt text"
