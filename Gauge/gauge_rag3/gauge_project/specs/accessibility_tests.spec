# Accessibility Tests

Generated : 2026-02-28 11:34
Base URL  : https://www.calculator.net/
Scenarios : 6

tags: accessibility, automated

## Accessibility: Alt Text for Images

tags: low, TC_012

<!-- Pre: User is on the loan calculator page -->

* Verify element with xpath <//img[@alt]> is visible
* Verify test outcome is <Image with alt text displayed>

## Accessibility: Images Have Alt Text

tags: regression, low, TC_017

<!-- Pre: User is on the math calculator page -->

* Verify element with id <image1> is visible
* Verify test outcome is <Image has alt text>

## Accessibility: images need alt text

tags: regression, low, TC_022

<!-- Pre: User is on the page -->

* Verify element with css <img> is visible
* Verify test outcome is <Alt text is present for every image>

## All Images Have Alt Text

tags: smoke, high, TC_026

<!-- Pre: User is on the page -->

* Verify element with xpath <//img> is visible
* Verify test outcome is <All images have alt text>

## Accessibility: Alt Text for Images

tags: low, TC_041

<!-- Pre: User is on the salary calculator page -->

* Verify element with id <calculator-image> is visible
* Verify test outcome is <Alt text appears for calculator image>

## All images have alt text

tags: smoke, high, TC_045

<!-- Pre: User is on the page -->

* Verify element with alt <Calculator> is visible
* Verify test outcome is <All images have alt text>
