# Form Tests

Generated : 2026-02-28 19:12
Base URL  : https://www.calculator.net/
Scenarios : 2

tags: form, automated

## About Us Page Form Submission Works [TC_036]

tags: smoke, high, TC_036

<!-- Pre: Navigate to the About Us page -->

* Navigate to url "https://www.calculator.net/about-us.html"
* Enter "John Doe" in input with name "name1"
* Enter "john.doe@example.com" in input with name "email1"
* Click on button with name "Submits"
* Verify test outcome is "Form submission works"

## About Us Page Form Validation Works [TC_037]

tags: smoke, high, TC_037

<!-- Pre: Navigate to the About Us page -->

* Navigate to url "https://www.calculator.net/about-us.html"
* Enter "value" in input with name "name1"
* Enter "value" in input with name "email1"
* Click on button with name "Submits"
* Verify test outcome is "Form validation works"
