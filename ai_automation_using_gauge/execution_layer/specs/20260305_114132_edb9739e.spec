# AI Exploratory Tests

Report ID  : 20260305_114132_edb9739e
Target URL : https://www.calculators.net/
Generated  : 20260305_114210
Test Count : 17
DOM Summary: 19 forms, 98 inputs, 157 buttons, 100 links

tags: accessibility, edge_case, error_handling, form, functional, navigation, negative, performance, security

## Suite Setup
tags: setup

* Open browser and navigate to base URL
* Take a screenshot

## 1. Search Functionality
tags: functional, medium

* Open browser and navigate to base URL
* Enter test in search
* Click button Search

* Verify: search results are displayed

* Verify: A list of relevant search results is displayed on the page
* Take a screenshot

## 2. Invalid Search Query
tags: edge_case, medium

* Open browser and navigate to base URL
* Enter !@#$ in search
* Click button Search

* Verify: error message is displayed

* Verify: An error message is displayed indicating that the search query is invalid
* Take a screenshot

## 3. Login with Valid Credentials
tags: functional, medium

* Open browser and navigate to base URL
* Navigate to /login.php
* Enter test@example.com in email
* Enter test123 in password
* Click button Submit

* Verify: login is successful

* Verify: The user is logged in and redirected to the dashboard page
* Take a screenshot

## 4. Login with Invalid Credentials
tags: negative, medium

* Open browser and navigate to base URL
* Navigate to /login.php
* Enter test@example.com in email
* Enter wrongpassword in password
* Click button Submit

* Verify: error message is displayed

* Verify: An error message is displayed indicating that the login credentials are invalid
* Take a screenshot

## 5. SQL Injection Attack
tags: security, medium

* Open browser and navigate to base URL
* Navigate to /login.php
* Enter test@example.com in email
* Enter a sql injection string in the login form
* Click button Submit

* Verify: error message is displayed

* Verify: An error message is displayed indicating that the SQL injection attack was detected and prevented
* Take a screenshot

## 6. Calculator Functionality
tags: functional, medium

* Open browser and navigate to base URL
* Click on a calculator link
* Enter 2 in number field
* Click button Calculate

* Verify: result is displayed

* Verify: The result of the calculation is displayed on the page
* Take a screenshot

## 7. Navigation Links
tags: navigation, medium

* Open browser and navigate to base URL
* Click link Home

* Verify: home page is displayed

* Verify: The home page is displayed with no errors
* Take a screenshot

## 8. Back Button Behaviour
tags: navigation, medium

* Open browser and navigate to base URL
* Click link About
* Go back to previous page

* Verify: previous page is displayed

* Verify: The previous page is displayed with no errors
* Take a screenshot

## 9. Form Validation
tags: form, medium

* Open browser and navigate to base URL
* Navigate to /signup.php
* Enter test@example.com in email
* Enter test123 in password
* Click button Submit

* Verify: form is validated

* Verify: The form is validated and an error message is displayed if any field is invalid
* Take a screenshot

## 10. Accessibility
tags: accessibility, medium

* Open browser and navigate to base URL
* Press key Tab

* Verify: focus is on the first focusable element

* Verify: The focus is on the first focusable element and the user can navigate the page using the keyboard
* Take a screenshot

## 11. Performance
tags: performance, medium

* Open browser and navigate to base URL
* Wait 2 seconds

* Verify: page is loaded

* Verify: The page is loaded within the expected time frame
* Take a screenshot

## 12. Error Handling
tags: error_handling, medium

* Open browser and navigate to base URL
* Navigate to a non-existent page

* Verify: 404 page is displayed

* Verify: A 404 page is displayed with a link to the home page
* Take a screenshot

## 13. File Upload
tags: form, medium

* Open browser and navigate to base URL
* Navigate to a page with a file upload field
* Select a file to upload
* Click button Upload

* Verify: file is uploaded

* Verify: The file is uploaded and a success message is displayed
* Take a screenshot

## 14. Checkbox and Radio Buttons
tags: form, medium

* Open browser and navigate to base URL
* Navigate to a page with checkbox and radio buttons
* Check checkbox test
* Select radio button test

* Verify: checkbox and radio button are selected

* Verify: The checkbox and radio button are selected and the form is submitted successfully
* Take a screenshot

## 15. Date and Time Pickers
tags: form, medium

* Open browser and navigate to base URL
* Navigate to a page with date and time pickers
* Select a date and time

* Verify: date and time are selected

* Verify: The date and time are selected and the form is submitted successfully
* Take a screenshot

## 16. Data Table and List Views
tags: functional, medium

* Open browser and navigate to base URL
* Navigate to a page with a data table or list view

* Verify: data is displayed in the table or list

* Verify: The data is displayed in the table or list with no errors
* Take a screenshot

## 17. Pagination
tags: functional, medium

* Open browser and navigate to base URL
* Navigate to a page with pagination
* Click on a page number

* Verify: correct page is displayed

* Verify: The correct page is displayed with no errors
* Take a screenshot

## Suite Teardown
tags: teardown

* Wait for network idle
* Take a screenshot
