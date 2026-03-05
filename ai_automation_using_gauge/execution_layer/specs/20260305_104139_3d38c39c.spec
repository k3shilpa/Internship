# AI Exploratory Tests

Report ID  : 20260305_104139_3d38c39c
Target URL : https://www.calculators.net/
Generated  : 20260305_104226
Test Count : 10
DOM Summary: 19 forms, 99 inputs, 157 buttons, 100 links

tags: accessibility, edge_case, functional, navigation, security

## Suite Setup
tags: setup

* Open browser and navigate to base URL
* Take a screenshot

## 1. Search Functionality
tags: functional

* Enter test-query in search
* Click button Search

* Verify: the search results are displayed correctly

* Verify: Search results are displayed with relevant calculators, worksheets, and exercises
* Take a screenshot

## 2. Invalid Search Query
tags: edge_case

* Enter test-query in search
* Click button Search

* Verify: an error message is displayed

* Verify: An error message is displayed indicating that no results were found
* Take a screenshot

## 3. Login Functionality
tags: functional

* Click button Login
* Enter testuser in username
* Click button Login

* Verify: the user is logged in successfully

* Verify: The user is logged in and can access their account
* Take a screenshot

## 4. Invalid Login Credentials
tags: edge_case

* Click button Login
* Enter testuser in username
* Click button Login

* Verify: an error message is displayed

* Verify: An error message is displayed indicating that the login credentials are invalid
* Take a screenshot

## 5. Calculator Functionality
tags: functional

* Perform action Select a calculator from the list of available calculators
* Enter test-value in input
* Click button Calculate

* Verify: the result is displayed correctly

* Verify: The result is displayed correctly based on the input values
* Take a screenshot

## 6. Accessibility Check
tags: accessibility

* Perform action Use a screen reader to navigate the website

* Verify: all elements are accessible and can be read by the screen reader

* Verify: All elements on the website are accessible and can be read by the screen reader
* Take a screenshot

## 7. SQL Injection Test
tags: security

* Enter a sql injection string in the login form
* Click button Login
* Submit the form

* Verify: The website does not display any error messages or sensitive data and prevents the SQL injection attack
* Take a screenshot

## 8. Password Reset Functionality
tags: functional

* Click on forgot password link
* Enter test-value in input
* Click button Reset Password

* Verify: a password reset email is sent to the user

* Verify: A password reset email is sent to the user with instructions on how to reset their password
* Take a screenshot

## 9. Navigation and Routing
tags: navigation

* Click on a navigation link

* Verify: the correct page is displayed
* Click button Back
* Go back to previous page

* Verify: The navigation links work correctly and the back button takes the user to the previous page
* Take a screenshot

## 10. Error Handling
tags: edge_case

* Perform action Simulate a network error

* Verify: an error message is displayed
* Click on a link that does not exist

* Verify: a 404 error page is displayed

* Verify: An error message is displayed for network errors and a 404 error page is displayed for non-existent links
* Take a screenshot

## Suite Teardown
tags: teardown

* Wait for network idle
* Take a screenshot
