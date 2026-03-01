# Navigation Tests

Generated : 2026-03-01 11:41
Base URL  : https://www.calculator.net/
Scenarios : 7

tags: navigation, automated

## Sign In Link Works Correctly [TC_002]

tags: low, navigation, TC_002

* Navigate to url "https://www.calculator.net/"
* Click on link with link_text "sign in"
* Verify test outcome is "Sign in link works correctly"

## Mortgage Calculator Link Works Correctly [TC_003]

tags: low, navigation, TC_003

* Navigate to url "https://www.calculator.net/"
* Click on link with link_text "Mortgage Calculator"
* Verify test outcome is "Mortgage calculator link works correctly"

## Click on a link [TC_006]

tags: low, TC_006

* Navigate to url "https://www.calculator.net/fitness-and-health-calculator.html"
* Click on link with link_text "BMI Calculator"
* Verify test outcome is "User is on the BMI Calculator page"

## Click on Sign In Link [TC_011]

tags: medium, smoke, TC_011

* Navigate to url "https://www.calculator.net/tdee-calculator.html"
* Click on link with link_text "sign in"
* Verify test outcome is "Sign in page loaded successfully"

## Sign In [TC_016]

tags: TC_016, smoke, high

* Navigate to url "https://www.calculator.net/pregnancy-weight-gain-calculator.html"
* Click on link with link_text "sign in"
* Verify "Sign in" is displayed
* Verify test outcome is "Sign in page displayed"

## Verify Sign In Link [TC_019]

tags: TC_019, low, smoke

* Navigate to url "https://www.calculator.net/financial-calculator.html"
* Click on link with link_text "sign in"
* Verify test outcome is "Sign In link is clickable"

## Verify Mortgage Calculator Link [TC_020]

tags: low, smoke, TC_020

* Navigate to url "https://www.calculator.net/financial-calculator.html"
* Click on link with link_text "Mortgage Calculator"
* Verify test outcome is "Mortgage Calculator link is clickable"
