# AI Exploratory Tests

Report ID  : 20260305_113533_c5d5ae49
Target URL : https://www.calculators.net/
Generated  : 20260305_113621
Test Count : 16
DOM Summary: 19 forms, 98 inputs, 157 buttons, 100 links

tags: accessibility, edge_case, form, functional, navigation, negative, performance, security

## Suite Setup
tags: setup

* Open browser and navigate to base URL
* Take a screenshot

## 1. Successful Search
tags: functional

* Open browser and navigate to base URL
* Enter calculators in search
* Click button Submit

* Verify: search results are displayed

* Verify: A list of relevant search results appears on the page
* Take a screenshot

## 2. Invalid Search
tags: functional

* Open browser and navigate to base URL
* Enter test-query in search
* Click button Submit

* Verify: error message is displayed

* Verify: An error message appears on the page indicating that no results were found
* Take a screenshot

## 3. Navigation to Login Page
tags: navigation

* Open browser and navigate to base URL
* Click button Login

* Verify: login page is displayed

* Verify: The login page appears with username and password fields
* Take a screenshot

## 4. Successful Login
tags: form

* Open browser and navigate to base URL
* Click button Login
* Enter valid username in username
* Enter valid password in password
* Click button Submit

* Verify: user is logged in

* Verify: The user is redirected to the dashboard or home page with a welcome message
* Take a screenshot

## 5. Invalid Login
tags: negative

* Open browser and navigate to base URL
* Click button Login
* Enter invalid username in username
* Enter wrongpassword in password
* Click button Submit

* Verify: error message is displayed

* Verify: An error message appears on the page indicating that the username or password is incorrect
* Take a screenshot

## 6. SQL Injection Attempt
tags: security

* Open browser and navigate to base URL
* Click button Login
* Enter a sql injection string in the login form
* Click button Submit

* Verify: error message is displayed

* Verify: An error message appears on the page indicating that the input is invalid
* Take a screenshot

## 7. Tab Key Navigation
tags: accessibility

* Open browser and navigate to base URL
* Click on key tab

* Verify: focus moves to the first focusable element

* Verify: The focus moves to the first focusable element on the page
* Take a screenshot

## 8. Keyboard-Only Form Completion
tags: accessibility

* Open browser and navigate to base URL
* Click button Login
* Click on key tab
* Enter valid username in username
* Click on key tab
* Enter valid password in password
* Click on key enter

* Verify: user is logged in

* Verify: The user is logged in and redirected to the dashboard or home page
* Take a screenshot

## 9. Slow Network Simulation
tags: performance

* Open browser and navigate to base URL
* Perform action Simulate slow network conditions
* Click button Login

* Verify: page loads within a reasonable time

* Verify: The page loads within a reasonable time despite the slow network conditions
* Take a screenshot

## 10. Rapid Repeated Clicks
tags: performance

* Open browser and navigate to base URL
* Click button Login
* Click button Submit

* Verify: page does not crash or become unresponsive

* Verify: The page remains responsive and does not crash despite the rapid repeated clicks
* Take a screenshot

## 11. Empty Input Field
tags: edge_case

* Open browser and navigate to base URL
* Click button Login
* Enter empty string in username
* Click button Submit

* Verify: error message is displayed

* Verify: An error message appears on the page indicating that the input is required
* Take a screenshot

## 12. Whitespace-Only Input Field
tags: edge_case

* Open browser and navigate to base URL
* Click button Login
* Enter whitespace-only string in username
* Click button Submit

* Verify: error message is displayed

* Verify: An error message appears on the page indicating that the input is invalid
* Take a screenshot

## 13. Long Input Field
tags: edge_case

* Open browser and navigate to base URL
* Click button Login
* Enter long string in username
* Click button Submit

* Verify: error message is displayed

* Verify: An error message appears on the page indicating that the input is too long
* Take a screenshot

## 14. Special Characters in Input Field
tags: edge_case

* Open browser and navigate to base URL
* Click button Login
* Enter test-special in search
* Click button Submit

* Verify: error message is displayed

* Verify: An error message appears on the page indicating that the input is invalid
* Take a screenshot

## 15. XSS Probe in Input Field
tags: security

* Open browser and navigate to base URL
* Click button Login
* Enter xss-probe in input
* Click button Submit

* Verify: error message is displayed

* Verify: An error message appears on the page indicating that the input is invalid
* Take a screenshot

## 16. Sensitive Data in URL
tags: security

* Open browser and navigate to base URL
* Click button Login
* Enter sensitive data in url
* Click button Submit

* Verify: error message is displayed

* Verify: An error message appears on the page indicating that the input is invalid
* Take a screenshot

## Suite Teardown
tags: teardown

* Wait for network idle
* Take a screenshot
