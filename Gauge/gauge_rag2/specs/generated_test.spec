Tags: regression

# calculator.net Automated Test Suite

## CALCULATOR_TC_001: Happy Path: Search for a calculator

* Navigate to "https://www.calculator.net/"
* Enter search term "loan calculator"
* Click the search button
* Verify the page contains "Loan Calculator"

## CALCULATOR_TC_002: Negative: Invalid search term

* Navigate to "https://www.calculator.net/"
* Enter search term "xss-attack-string"
* Click the search button
* Verify search does not crash

## CALCULATOR_TC_003: Boundary: Search term with maximum length

* Navigate to "https://www.calculator.net/"
* Enter search term "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
* Click the search button
* Verify search does not crash

## CALCULATOR_TC_004: e2e: Search for a calculator and verify results

* Navigate to "https://www.calculator.net/"
* Enter search term "loan calculator"
* Click the search button
* Verify the page contains "Loan Calculator"

## LOGIN_TC_001: Happy Path - Valid Credentials

* Navigate to "https://www.calculator.net/my-account/sign-in.php"
* Enter email "test@example.com"
* Enter password "password123"
* Click the login button
* Verify login was attempted

## LOGIN_TC_002: Negative - Invalid Email

* Navigate to "https://www.calculator.net/my-account/sign-in.php"
* Enter email "invalid"
* Enter password "password123"
* Click the login button
* Verify login was attempted

## LOGIN_TC_003: Boundary - Empty Email

* Navigate to "https://www.calculator.net/my-account/sign-in.php"
* Enter email ""
* Enter password "password123"
* Click the login button
* Verify login was attempted

## LOGIN_TC_004: E2E - User is Logged In

* Navigate to "https://www.calculator.net/my-account/sign-in.php"
* Enter email "test@example.com"
* Enter password "password123"
* Click the login button
* Verify the user is logged in

## FINANCIAL_CALCULATOR_TC_001: Happy Path: Search for a financial calculator

* Navigate to "https://www.calculator.net/financial-calculator.html"
* Enter search term "mortgage"
* Click the search button
* Verify the page contains "Mortgage"

## FINANCIAL_CALCULATOR_TC_002: Negative: Search with an empty input

* Navigate to "https://www.calculator.net/financial-calculator.html"
* Enter search term ""
* Click the search button
* Verify search does not crash

## FINANCIAL_CALCULATOR_TC_003: Boundary: Search with a very long search term

* Navigate to "https://www.calculator.net/financial-calculator.html"
* Enter search term "a very long search term that exceeds max length"
* Click the search button
* Verify the page contains "A Very Long Search Term That Exceeds Max Length"

## FINANCIAL_CALCULATOR_TC_004: E2E: Select a financial calculator and use it

* Navigate to "https://www.calculator.net/financial-calculator.html"
* Enter search term "mortgage"
* Click the search button
* Click the "Mortgage Calculator" link
* Enter loan amount "100000"
* Enter interest rate "5"
* Enter loan term "30"
* Click the calculate button
* Verify the page contains "Mortgage"

## MORTGAGE_CALCULATOR_TC_001: Happy Path: Calculate Mortgage Payments

* Navigate to "https://www.calculator.net/mortgage-calculator.html"
* Enter loan amount "100000"
* Enter interest rate "4"
* Enter loan term "30"
* Click the calculate button
* Verify monthly payment is displayed
* Verify calculated result contains "$477.42"

## MORTGAGE_CALCULATOR_TC_002: Negative: Invalid Input

* Navigate to "https://www.calculator.net/mortgage-calculator.html"
* Enter loan amount "abc"
* Enter interest rate "4"
* Enter loan term "30"
* Click the calculate button
* Verify page does not show valid result for "abc"

## MORTGAGE_CALCULATOR_TC_003: Boundary: Maximum Loan Amount

* Navigate to "https://www.calculator.net/mortgage-calculator.html"
* Enter loan amount "1000000"
* Enter interest rate "4"
* Enter loan term "30"
* Click the calculate button
* Verify monthly payment is displayed
* Verify calculated result contains "$4,774.15"

## MORTGAGE_CALCULATOR_TC_004: E2E: Calculate Mortgage Payments and View Amortization Schedule

* Navigate to "https://www.calculator.net/mortgage-calculator.html"
* Enter loan amount "100000"
* Enter interest rate "4"
* Enter loan term "30"
* Click the calculate button
* Click the view amortization schedule button
* Verify monthly payment is displayed
* Verify calculated result contains "$477.42"
* Verify amortization schedule is displayed

## LOAN_CALCULATOR_TC_001: Happy Path: Valid Loan Repayment Calculation

* Navigate to "https://www.calculator.net/loan-calculator.html"
* Enter loan amount "100000"
* Enter interest rate "6"
* Enter loan term "10"
* Select compounding frequency "monthly"
* Click the calculate button
* Verify monthly payment is displayed
* Verify calculated result contains "$1,110.21"

## LOAN_CALCULATOR_TC_002: Negative: Invalid Loan Amount

* Navigate to "https://www.calculator.net/loan-calculator.html"
* Enter loan amount "abc"
* Enter interest rate "6"
* Enter loan term "10"
* Select compounding frequency "monthly"
* Click the calculate button
* Verify page does not show valid result for "abc"

## LOAN_CALCULATOR_TC_003: Boundary: Loan Term at Maximum

* Navigate to "https://www.calculator.net/loan-calculator.html"
* Enter loan amount "100000"
* Enter interest rate "6"
* Enter loan term "100"
* Select compounding frequency "monthly"
* Click the calculate button
* Verify monthly payment is displayed
* Verify calculated result contains "$501.26"

## LOAN_CALCULATOR_TC_004: E2E: Loan Repayment Calculation with Different Compounding Frequency

* Navigate to "https://www.calculator.net/loan-calculator.html"
* Enter loan amount "100000"
* Enter interest rate "6"
* Enter loan term "10"
* Select compounding frequency "annually"
* Click the calculate button
* Verify monthly payment is displayed
* Verify calculated result contains "$1,102.24"

## AUTO_LOAN_CALCULATOR_TC_001: Happy Path: Valid Auto Loan Calculation

* Navigate to "https://www.calculator.net/auto-loan-calculator.html"
* Enter sale price "50000"
* Enter loan term "60"
* Enter interest rate "5"
* Enter incentive "0"
* Enter down payment "10000"
* Enter trade in value "0"
* Enter trade in owned "0"
* Select down payment unit "percent"
* Select down payment unit "percent"
* Select state "CA"
* Enter sale tax "5"
* Enter title and registration "2000"
* Click the calculate button
* Verify monthly payment is displayed
* Verify calculated result contains "$219.32"

## AUTO_LOAN_CALCULATOR_TC_002: Negative: Invalid Form Submission

* Navigate to "https://www.calculator.net/auto-loan-calculator.html"
* Enter sale price "abc"
* Click the calculate button
* Verify page does not show valid result for "abc"

## AUTO_LOAN_CALCULATOR_TC_003: Boundary: Maximum Sale Price

* Navigate to "https://www.calculator.net/auto-loan-calculator.html"
* Enter sale price "1000000"
* Click the calculate button
* Verify monthly payment is displayed

## AUTO_LOAN_CALCULATOR_TC_004: E2E: Auto Loan Calculation and Results

* Navigate to "https://www.calculator.net/auto-loan-calculator.html"
* Enter sale price "50000"
* Enter loan term "60"
* Enter interest rate "5"
* Enter incentive "0"
* Enter down payment "10000"
* Enter trade in value "0"
* Enter trade in owned "0"
* Select down payment unit "percent"
* Select down payment unit "percent"
* Select state "CA"
* Enter sale tax "5"
* Enter title and registration "2000"
* Click the calculate button
* Verify monthly payment is displayed
* Verify calculated result contains "$219.32"

## MODULE_TC_001: Verify form page loads successfully

* Navigate to "https://www.calculator.net/interest-calculator.html"

## MODULE_TC_002: Submit Calculate interest on investments and loans with valid data

* Navigate to "https://www.calculator.net/interest-calculator.html"

## MODULE_TC_003: Submit Search for a calculator with valid data

* Navigate to "https://www.calculator.net/interest-calculator.html"

## PAYMENT_CALCULATOR_TC_001: Happy Path: Valid Loan Details

* Navigate to "https://www.calculator.net/payment-calculator.html"
* Enter loan amount "100000"
* Enter interest rate "5"
* Enter loan term "5"
* Click the calculate button
* Verify monthly payment is displayed
* Verify calculated result contains "$1,887.12"

## PAYMENT_CALCULATOR_TC_002: Negative: Invalid Loan Amount

* Navigate to "https://www.calculator.net/payment-calculator.html"
* Enter loan amount "abc"
* Enter interest rate "5"
* Enter loan term "5"
* Click the calculate button
* Verify page does not show valid result for "abc"

## PAYMENT_CALCULATOR_TC_003: Boundary: Maximum Loan Amount

* Navigate to "https://www.calculator.net/payment-calculator.html"
* Enter loan amount "999999999"
* Enter interest rate "5"
* Enter loan term "5"
* Click the calculate button
* Verify monthly payment is displayed
* Verify calculated result contains "$18,871,233.63"

## PAYMENT_CALCULATOR_TC_004: E2E: Clear Previous Calculations

* Navigate to "https://www.calculator.net/payment-calculator.html"
* Click the clear button

## RETIREMENT_CALCULATOR_TC_001: Happy Path: Calculate Retirement Savings

* Navigate to "https://www.calculator.net/retirement-calculator.html"
* Enter current age "65"
* Enter retirement age "70"
* Enter life expectancy "80"
* Enter current income "50000"
* Enter income growth rate "5"
* Enter desired retirement income "60000"
* Select income unit "dollars"
* Click the calculate button
* Verify retirement result is displayed

## RETIREMENT_CALCULATOR_TC_002: Negative: Invalid Input

* Navigate to "https://www.calculator.net/retirement-calculator.html"
* Enter current age "-1"
* Enter retirement age "70"
* Enter life expectancy "80"
* Enter current income "50000"
* Enter income growth rate "5"
* Enter desired retirement income "60000"
* Select income unit "dollars"
* Click the calculate button
* Verify retirement result is displayed

## RETIREMENT_CALCULATOR_TC_003: Boundary: Minimum Input

* Navigate to "https://www.calculator.net/retirement-calculator.html"
* Enter current age "25"
* Enter retirement age "65"
* Enter life expectancy "75"
* Enter current income "20000"
* Enter income growth rate "0"
* Enter desired retirement income "40000"
* Select income unit "dollars"
* Click the calculate button
* Verify retirement result is displayed

## RETIREMENT_CALCULATOR_TC_004: E2E: Retirement Planning Options

* Navigate to "https://www.calculator.net/retirement-calculator.html"
* Click the view retirement planning options button
