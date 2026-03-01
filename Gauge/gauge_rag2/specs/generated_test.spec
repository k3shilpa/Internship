# calculator.net Automated Test Suite


  ## CALCULATOR_TC_001: Happy Path: Search for a calculator
  tags: happy_path, calculator

  * Navigate to "/"
  * Enter "loan calculator" into "calcSearchTerm"
  * Click "Search"

  ## CALCULATOR_TC_002: Negative: Invalid search term
  tags: negative, calculator

  * Navigate to "/"
  * Enter "xss-attack-string" into "calcSearchTerm"
  * Click "Search"

  ## CALCULATOR_TC_003: Boundary: Search term with maximum length
  tags: boundary, calculator

  * Navigate to "/"
  * Enter "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" into "calcSearchTerm"
  * Click "Search"

  ## CALCULATOR_TC_004: e2e: Search for a calculator and verify results
  tags: e2e, calculator

  * Navigate to "/"
  * Enter "loan calculator" into "calcSearchTerm"
  * Click "Search"
  * Verify: Page contains "Loan Calculator"

  ## LOGIN_TC_001: Happy Path - Valid Credentials
  tags: happy_path, login

  * Navigate to "/my-account/sign-in.php"
  * Enter "test@example.com" into "email"
  * Enter "password123" into "password"
  * Click "submit"

  ## LOGIN_TC_002: Negative - Invalid Email
  tags: negative, login

  * Navigate to "/my-account/sign-in.php"
  * Enter "invalid" into "email"
  * Enter "password123" into "password"
  * Click "submit"

  ## LOGIN_TC_003: Boundary - Empty Email
  tags: boundary, login

  * Navigate to "/my-account/sign-in.php"
  * Enter "password123" into "password"
  * Click "submit"

  ## LOGIN_TC_004: E2E - User is Logged In
  tags: e2e, login

  * Navigate to "/my-account/sign-in.php"
  * Enter "test@example.com" into "email"
  * Enter "password123" into "password"
  * Click "submit"
  * Verify: User is logged in

  ## FINANCIAL_CALCULATOR_TC_001: Happy Path: Search for a financial calculator
  tags: financial_calculator, happy_path

  * Navigate to "/financial-calculator.html"
  * Enter "mortgage" into "calcSearchTerm"
  * Click "Search"
  * Verify: Page contains "Mortgage Calculator"

  ## FINANCIAL_CALCULATOR_TC_002: Negative: Search with an empty input
  tags: financial_calculator, negative

  * Navigate to "/financial-calculator.html"
  * Enter "empty" into "calcSearchTerm"
  * Click "Search"
  * Verify: Page contains "All Calculators"

  ## FINANCIAL_CALCULATOR_TC_003: Boundary: Search with a very long search term
  tags: financial_calculator, boundary

  * Navigate to "/financial-calculator.html"
  * Enter "a very long search term that exceeds max length" into "calcSearchTerm"
  * Click "Search"
  * Verify: Page contains "Error: Search term too long"

  ## FINANCIAL_CALCULATOR_TC_004: E2E: Select a financial calculator and use it
  tags: financial_calculator, e2e

  * Navigate to "/financial-calculator.html"
  * Enter "mortgage" into "calcSearchTerm"
  * Click "Search"
  * Click "Mortgage Calculator"
  * Enter "100000" into "chouseprice"
  * Enter "5" into "cinterestrate"
  * Enter "30" into "cloanterm"
  * Click "See your local rates"
  * Verify: Monthly payment is displayed

  ## MORTGAGE_CALCULATOR_TC_001: Happy Path: Calculate Mortgage Payments
  tags: happy_path, mortgage_calculator

  * Navigate to "/mortgage-calculator.html"
  * Enter "100000" into "chouseprice"
  * Enter "4" into "cinterestrate"
  * Enter "30" into "cloanterm"
  * Click "See your local rates"
  * Verify: Page contains "Monthly Payment: $"
  * Verify: Monthly payment is displayed

  ## MORTGAGE_CALCULATOR_TC_002: Negative: Invalid Input
  tags: negative, mortgage_calculator

  * Navigate to "/mortgage-calculator.html"
  * Enter "abc" into "chouseprice"
  * Enter "4" into "cinterestrate"
  * Enter "30" into "cloanterm"
  * Click "See your local rates"
  * Verify: Page contains "Error: Invalid input"

  ## MORTGAGE_CALCULATOR_TC_003: Boundary: Maximum Loan Amount
  tags: boundary, mortgage_calculator

  * Navigate to "/mortgage-calculator.html"
  * Enter "1000000" into "chouseprice"
  * Enter "4" into "cinterestrate"
  * Enter "30" into "cloanterm"
  * Click "See your local rates"
  * Verify: Page contains "Maximum loan amount reached"

  ## MORTGAGE_CALCULATOR_TC_004: E2E: Calculate Mortgage Payments and View Amortization Schedule
  tags: e2e, mortgage_calculator

  * Navigate to "/mortgage-calculator.html"
  * Enter "100000" into "chouseprice"
  * Enter "4" into "cinterestrate"
  * Enter "30" into "cloanterm"
  * Click "See your local rates"
  * Verify: Monthly payment is displayed
  * Click "Show/Hide Amortization Schedule"
  * Verify: Amortization schedule is displayed

  ## LOAN_CALCULATOR_TC_001: Happy Path: Valid Loan Repayment Calculation
  tags: loan_calculation, happy_path

  * Navigate to "/loan-calculator.html"
  * Select "frequency monthly" in "ccompound"
  * Click "x"

  ## LOAN_CALCULATOR_TC_002: Negative: Invalid Loan Amount
  tags: loan_calculation, negative

  * Navigate to "/loan-calculator.html"
  * Select "frequency monthly" in "ccompound"
  * Click "x"

  ## LOAN_CALCULATOR_TC_003: Boundary: Loan Term at Maximum
  tags: loan_calculation, boundary

  * Navigate to "/loan-calculator.html"
  * Select "frequency monthly" in "ccompound"
  * Click "x"

  ## LOAN_CALCULATOR_TC_004: E2E: Loan Repayment Calculation with Different Compounding Frequency
  tags: loan_calculation, e2e

  * Navigate to "/loan-calculator.html"
  * Select "frequency annually" in "ccompound"
  * Click "x"

  ## AUTO_LOAN_CALCULATOR_TC_001: Happy Path: Valid Auto Loan Calculation
  tags: happy_path, auto_loan

  * Navigate to "/auto-loan-calculator.html"
  * Enter "50000" into "csaleprice"
  * Enter "60" into "cloanterm"
  * Enter "5" into "cinterestrate"
  * Enter "0" into "cincentive"
  * Enter "10000" into "cdownpayment"
  * Enter "0" into "ctradeinvalue"
  * Enter "0" into "ctradeowned"
  * Select "percent" in "cdownpaymentunit"
  * Select "CA" in "cstate"
  * Enter "5" into "csaletax"
  * Enter "2000" into "ctitle"
  * Click "x"

  ## AUTO_LOAN_CALCULATOR_TC_002: Negative: Invalid Form Submission
  tags: negative, auto_loan

  * Navigate to "/auto-loan-calculator.html"
  * Enter "abc" into "csaleprice"
  * Click "x"

  ## AUTO_LOAN_CALCULATOR_TC_003: Boundary: Maximum Sale Price
  tags: boundary, auto_loan

  * Navigate to "/auto-loan-calculator.html"
  * Enter "1000000" into "csaleprice"
  * Click "x"

  ## AUTO_LOAN_CALCULATOR_TC_004: E2E: Auto Loan Calculation and Results
  tags: e2e, auto_loan

  * Navigate to "/auto-loan-calculator.html"
  * Enter "50000" into "csaleprice"
  * Enter "60" into "cloanterm"
  * Enter "5" into "cinterestrate"
  * Enter "0" into "cincentive"
  * Enter "10000" into "cdownpayment"
  * Enter "0" into "ctradeinvalue"
  * Enter "0" into "ctradeowned"
  * Select "percent" in "cdownpaymentunit"
  * Select "CA" in "cstate"
  * Enter "5" into "csaletax"
  * Enter "2000" into "ctitle"
  * Click "x"
  * Verify: Page contains "Auto Loan Calculator Results"

  ## TC_001: Verify form page loads successfully
  tags: smoke, functional

  * Navigate to "/interest-calculator.html"
  * Verify: Page loaded successfully

  ## TC_002: Submit Calculate interest on investments and loans with valid data
  tags: functional, form

  * Navigate to "/interest-calculator.html"
  * Verify: Page loaded successfully

  ## TC_003: Submit Search for a calculator with valid data
  tags: functional, form

  * Navigate to "/interest-calculator.html"
  * Verify: Page loaded successfully

  ## PAYMENT_CALCULATOR_TC_001: Happy Path: Valid Loan Details
  tags: happy_path, payment_calculator

  * Navigate to "/payment-calculator.html"
  * Enter "100000" into "cloanamount"
  * Enter "5" into "cinterestrate"
  * Enter "5" into "cloanterm"
  * Click "x"
  * Verify: Page contains "Monthly Payment: $"
  * Verify: Monthly payment is displayed

  ## PAYMENT_CALCULATOR_TC_002: Negative: Invalid Loan Amount
  tags: negative, payment_calculator

  * Navigate to "/payment-calculator.html"
  * Enter "abc" into "cloanamount"
  * Enter "5" into "cinterestrate"
  * Enter "5" into "cloanterm"
  * Click "x"
  * Verify: Page contains "Error: Invalid loan amount"

  ## PAYMENT_CALCULATOR_TC_003: Boundary: Maximum Loan Amount
  tags: boundary, payment_calculator

  * Navigate to "/payment-calculator.html"
  * Enter "999999999" into "cloanamount"
  * Enter "5" into "cinterestrate"
  * Enter "5" into "cloanterm"
  * Click "x"
  * Verify: Page contains "Monthly Payment: $"

  ## PAYMENT_CALCULATOR_TC_004: E2E: Clear Previous Calculations
  tags: e2e, payment_calculator

  * Navigate to "/payment-calculator.html"
  * Click "Clear"
  * Verify: Page contains "Loan Amount: $"
  * Verify: loan amount input field is empty

  ## RETIREMENT_CALCULATOR_TC_001: Happy Path: Calculate Retirement Savings
  tags: happy_path, retirement_calculator

  * Navigate to "/retirement-calculator.html"
  * Enter "65" into "cagenow"
  * Enter "70" into "cretireage"
  * Enter "80" into "clifeexpectancy"
  * Enter "50000" into "cincomenow"
  * Enter "5" into "cincgrowth"
  * Enter "60000" into "cretireincome"
  * Select "dollars" in "cincomeunit"
  * Click "x"

  ## RETIREMENT_CALCULATOR_TC_002: Negative: Invalid Input
  tags: negative, retirement_calculator

  * Navigate to "/retirement-calculator.html"
  * Enter "-1" into "cagenow"
  * Enter "70" into "cretireage"
  * Enter "80" into "clifeexpectancy"
  * Enter "50000" into "cincomenow"
  * Enter "5" into "cincgrowth"
  * Enter "60000" into "cretireincome"
  * Select "dollars" in "cincomeunit"
  * Click "x"

  ## RETIREMENT_CALCULATOR_TC_003: Boundary: Minimum Input
  tags: boundary, retirement_calculator

  * Navigate to "/retirement-calculator.html"
  * Enter "25" into "cagenow"
  * Enter "65" into "cretireage"
  * Enter "75" into "clifeexpectancy"
  * Enter "20000" into "cincomenow"
  * Enter "0" into "cincgrowth"
  * Enter "40000" into "cretireincome"
  * Select "dollars" in "cincomeunit"
  * Click "x"

  ## RETIREMENT_CALCULATOR_TC_004: E2E: Retirement Planning Options
  tags: e2e, retirement_calculator

  * Navigate to "/retirement-calculator.html"
  * Click "Show Retirement Planning Options"
  * Verify: Page contains "Retirement Planning Options"
