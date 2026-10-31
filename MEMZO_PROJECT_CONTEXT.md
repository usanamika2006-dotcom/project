# MEMZO

## Subscription Management System -- Complete Project Handoff

> **Project name:** Brightloop -- Subscription Management System\
> **Company:** Brightloop Software (fictional company)\
> **Project type:** Web-based Subscription Management System

------------------------------------------------------------------------

## 1. Project Overview

Brightloop is a software company that sells subscription-based software
products to customers.

The project is to develop a centralized web application that allows the
company to manage its products, subscription plans, customers,
quotations, subscriptions, invoices, discounts and payments.

The system will have three user roles:

1.  Admin
2.  Staff
3.  Customer

### Important project clarification

This is **NOT** a platform that combines subscriptions from Netflix,
Amazon Prime, Spotify or other external companies.

Brightloop is one software company selling its own software products.
Customers purchase subscriptions to Brightloop's products through our
application.

We are developing the subscription management platform, not the actual
software products being sold.

## 2. Business Scenario

Brightloop Software offers different software products.

Examples:

-   BrightBooks -- Accounting software
-   StaffTrack -- Employee management software
-   StockMaster -- Inventory management software
-   EduManage -- Educational management software
-   ShopFlow -- Retail management software

These are illustrative product examples.

The Admin adds products and creates subscription plans for them.

Customers visit the public website, browse available products, select a
plan and purchase a subscription.

Staff members handle daily operations such as managing customers,
subscriptions, quotations, invoices and payments.

The Admin controls the entire system.

## 3. Problem Statement

Currently, Brightloop manages its subscription business using
spreadsheets and manual processes.

This creates several problems:

-   Missed subscription renewals.
-   Incorrect invoice generation.
-   Manual payment matching.
-   Difficulty tracking outstanding payments.
-   Lack of clear recurring revenue reports.
-   Difficulty managing large numbers of subscriptions.

The proposed system should automate and centralize these operations.

## 4. Main Project Requirements

### A. User Management

-   Customer registration.
-   Common login system.
-   Password hashing.
-   Password reset functionality.
-   Role-based access control.
-   Admin can create staff accounts.
-   Each customer can access only their own records.

### B. Product Management

Admin should be able to:

-   Add products.
-   Edit products.
-   Delete or deactivate products.
-   Enter product name, type and description.
-   Enter sales price and cost price.
-   Add notes.
-   Manage product variants and add-ons.
-   Publish or unpublish products.

Published products should automatically appear in the public customer
catalogue.

### C. Subscription Plan Management

Admin should be able to create plans for products.

Plans should support:

-   Daily billing.
-   Weekly billing.
-   Monthly billing.
-   Yearly billing.
-   Pricing.
-   Minimum quantity.
-   Availability dates.
-   Automatic closure options.
-   Early closure options.
-   Pause options.
-   Renewal options.

### D. Subscription Management

The system should:

-   Create subscriptions.
-   Assign customers and plans.
-   Record subscription start and expiry dates.
-   Track subscription status.
-   Support renewal.
-   Support pause and closure where permitted.
-   Monitor upcoming renewals.

The assignment specifies these subscription statuses:

**Draft → Quotation → Confirmed → Active → Closed**

### E. Quotation Management

The system should allow quotations to be created for customers.

Quotation details include:

-   Quotation number.
-   Customer details.
-   Products.
-   Quantities.
-   Unit prices.
-   Taxes.
-   Total amount.
-   Validity date.
-   Quotation status.

### F. Invoice Management

The system should:

-   Generate invoices from subscriptions.
-   Display customer details.
-   Display product details.
-   Calculate taxes.
-   Calculate discounts.
-   Calculate total amounts.
-   Confirm invoices.
-   Cancel invoices.
-   Send invoices.
-   Print invoices.

Invoice statuses:

**Draft → Confirmed → Paid**

The system should avoid duplicate or missing billing.

### G. Discount Management

Only Admin should create discount rules.

Discounts should support:

-   Fixed discounts.
-   Percentage discounts.
-   Minimum purchase amount.
-   Minimum quantity.
-   Start date.
-   End date.
-   Usage limits.
-   Active/inactive status.

Discounts should automatically apply when eligible and stop applying
when expired or exhausted.

### H. Payment Management

The system should:

-   Record payments.
-   Associate payments with invoices.
-   Record payment methods.
-   Record payment dates.
-   Record amounts.
-   Store transaction references.
-   Add payment notes.
-   Display paid and outstanding amounts.

### I. Reports and Dashboard

The Admin dashboard should display:

-   Total customers.
-   Active subscriptions.
-   Total revenue.
-   Payments received.
-   Outstanding invoices.
-   Overdue invoices.
-   Subscription statistics.
-   Revenue summaries.

Reports should support useful filtering.

### J. Notifications

Notifications should cover:

-   Upcoming renewals.
-   Payment updates.
-   Failed payments.
-   Invoice updates.
-   Subscription updates.

## 5. User Roles and Permissions

The application must have three separate roles.

### A. Admin

Admin has complete control over the system.

**Admin pages:**

1.  Admin Dashboard --- `admin_dashboard.html`
2.  Product Management --- `admin_products.html`
3.  Plan Management --- `admin_plans.html`
4.  Staff Management --- `admin_staff.html`
5.  Customer Management --- `admin_customers.html`
6.  Subscription Management --- `admin_subscriptions.html`
7.  Quotation Management --- `admin_quotations.html`
8.  Invoice Management --- `admin_invoices.html`
9.  Discount Management --- `admin_discounts.html`
10. Payment Management --- `admin_payments.html`
11. Reports --- `admin_reports.html`
12. Settings --- `admin_settings.html`

**Admin permissions:**

-   Add, edit and manage products.
-   Create and manage subscription plans.
-   Add staff accounts.
-   Manage all customers.
-   Manage subscriptions.
-   Manage quotations and invoices.
-   Create discount rules.
-   Monitor payments.
-   View financial reports.
-   Configure system settings.

### B. Staff

Staff handles daily business operations.

**Staff pages:**

1.  Staff Dashboard --- `staff_dashboard.html`
2.  Customer Management --- `staff_customers.html`
3.  Subscription Management --- `staff_subscriptions.html`
4.  Quotation Management --- `staff_quotations.html`
5.  Invoice Management --- `staff_invoices.html`
6.  Payment Management --- `staff_payments.html`
7.  Notifications --- `staff_notifications.html`
8.  Staff Profile --- `staff_profile.html`

**Staff permissions:**

-   View and manage customer information.
-   View and manage subscriptions within their permissions.
-   Create and manage quotations.
-   Generate and manage invoices.
-   Record and monitor payments.
-   View notifications.
-   Manage their own profile.

**Staff should NOT be able to:**

-   Create other staff accounts.
-   Create discount rules.
-   Change restricted Admin settings.
-   Access restricted administrative controls.

Staff permissions must be enforced in the Flask backend, not merely by
hiding sidebar links.

### C. Customer

Customers use the platform to purchase and manage their own
subscriptions.

**Customer pages:**

1.  Customer Dashboard --- `customer_dashboard.html`
2.  My Subscriptions --- `customer_subscriptions.html`
3.  My Invoices --- `customer_invoices.html`
4.  Payment History --- `customer_payments.html`
5.  Notifications --- `customer_notifications.html`
6.  My Profile --- `customer_profile.html`

**Customer permissions:**

-   Browse published software products.
-   View product details.
-   View available subscription plans.
-   Purchase subscription plans.
-   View their own subscriptions.
-   View and download their own invoices.
-   View their payment history.
-   Receive notifications.
-   Update their profile.

Customers must only access their own subscription, invoice and payment
records.

## 6. Public Pages

Public pages are common pages accessible to visitors and customers. They
are **not** a fourth user role.

  Filename                Purpose
  ----------------------- -------------------------------
  `index.html`            Website home page
  `register.html`         Customer registration
  `login.html`            Common login for all roles
  `products.html`         Public software catalogue
  `product_detail.html`   Product information and plans
  `checkout.html`         Customer purchase process

### Important

-   Admin and Staff should use the common login page.
-   Only customers should be allowed to register through the public
    registration page.
-   Admin creates staff accounts.

After login, the system checks the user's role and redirects them:

-   Admin → Admin Dashboard
-   Staff → Staff Dashboard
-   Customer → Customer Dashboard

## 7. Complete Project File Structure

Use this as the common directory structure. More files can be added if a
feature requires them.

``` text
Brightloop/
│
├── app.py
├── models.py
├── database.db
├── requirements.txt
│
├── templates/
│   │
│   ├── base.html
│   │
│   ├── index.html
│   ├── register.html
│   ├── login.html
│   ├── products.html
│   ├── product_detail.html
│   ├── checkout.html
│   │
│   ├── admin/
│   │   ├── admin_dashboard.html
│   │   ├── admin_products.html
│   │   ├── admin_plans.html
│   │   ├── admin_staff.html
│   │   ├── admin_customers.html
│   │   ├── admin_subscriptions.html
│   │   ├── admin_quotations.html
│   │   ├── admin_invoices.html
│   │   ├── admin_discounts.html
│   │   ├── admin_payments.html
│   │   ├── admin_reports.html
│   │   └── admin_settings.html
│   │
│   ├── staff/
│   │   ├── staff_dashboard.html
│   │   ├── staff_customers.html
│   │   ├── staff_subscriptions.html
│   │   ├── staff_quotations.html
│   │   ├── staff_invoices.html
│   │   ├── staff_payments.html
│   │   ├── staff_notifications.html
│   │   └── staff_profile.html
│   │
│   └── customer/
│       ├── customer_dashboard.html
│       ├── customer_subscriptions.html
│       ├── customer_invoices.html
│       ├── customer_payments.html
│       ├── customer_notifications.html
│       └── customer_profile.html
│
├── static/
│   │
│   ├── css/
│   │   └── style.css
│   │
│   ├── js/
│   │   └── script.js
│   │
│   └── images/
│       ├── logo.png
│       └── banner.png
│
└── venv/
```

## 8. Database Design

All three roles must use the **same database**.

Do not create separate databases for Admin, Staff and Customers.

**Recommended database:** SQLite.

### Main Tables

    No. Table                  Purpose
  ----- ---------------------- -------------------------------------------
      1 `users`                Stores Admin, Staff and Customer accounts
      2 `products`             Stores software products
      3 `product_variants`     Stores product variants and add-ons
      4 `plans`                Stores subscription plans
      5 `subscriptions`        Stores customer subscriptions
      6 `subscription_items`   Stores subscription product lines
      7 `quotations`           Stores quotations
      8 `quotation_items`      Stores quotation product lines
      9 `tax_rules`            Stores tax rules
     10 `discounts`            Stores discount rules
     11 `invoices`             Stores invoices
     12 `invoice_items`        Stores invoice product lines
     13 `payments`             Stores payment transactions
     14 `notifications`        Stores user notifications

### Important Columns

**`users`**

-   `user_id`
-   `name`
-   `email`
-   `password_hash`
-   `role`
-   `phone`
-   `created_at`

Role values: `admin`, `staff`, `customer`.

**`products`**

-   `product_id`
-   `product_name`
-   `description`
-   `product_type`
-   `sales_price`
-   `cost_price`
-   `notes`
-   `image`
-   `is_published`
-   `created_at`

**`plans`**

-   `plan_id`
-   `product_id`
-   `plan_name`
-   `billing_cycle`
-   `price`
-   `minimum_quantity`
-   `available_from`
-   `available_until`
-   `auto_close`
-   `allow_early_close`
-   `allow_pause`
-   `allow_renew`

**`subscriptions`**

-   `subscription_id`
-   `customer_id`
-   `plan_id`
-   `start_date`
-   `expiry_date`
-   `status`
-   `payment_terms`

**`subscription_items`**

-   `item_id`
-   `subscription_id`
-   `product_id`
-   `quantity`
-   `unit_price`
-   `tax_amount`
-   `total_amount`

**`quotations`**

-   `quotation_id`
-   `customer_id`
-   `quotation_date`
-   `valid_until`
-   `total_amount`
-   `status`

**`quotation_items`**

-   `item_id`
-   `quotation_id`
-   `product_id`
-   `quantity`
-   `unit_price`
-   `total_amount`

**`tax_rules`**

-   `tax_id`
-   `tax_name`
-   `tax_percentage`
-   `is_active`

**`discounts`**

-   `discount_id`
-   `discount_name`
-   `discount_type`
-   `discount_value`
-   `minimum_purchase`
-   `start_date`
-   `end_date`
-   `usage_limit`
-   `used_count`
-   `is_active`

**`invoices`**

-   `invoice_id`
-   `subscription_id`
-   `customer_id`
-   `invoice_date`
-   `due_date`
-   `subtotal`
-   `tax_amount`
-   `discount_amount`
-   `total_amount`
-   `status`

**`invoice_items`**

-   `item_id`
-   `invoice_id`
-   `product_id`
-   `quantity`
-   `unit_price`
-   `tax_amount`
-   `total_amount`

**`payments`**

-   `payment_id`
-   `invoice_id`
-   `customer_id`
-   `amount`
-   `payment_method`
-   `payment_date`
-   `transaction_reference`
-   `status`
-   `notes`

**`notifications`**

-   `notification_id`
-   `user_id`
-   `message`
-   `notification_type`
-   `is_read`
-   `created_at`

Additional columns can be introduced when necessary.

### Database Relationships

-   One product can have multiple plans.
-   One product can have multiple variants.
-   One customer can have multiple subscriptions.
-   One plan can be selected by multiple customers.
-   One subscription can generate multiple invoices over time.
-   One invoice can have multiple invoice items.
-   One invoice can have one or more payment records.
-   One quotation can contain multiple quotation items.
-   One user can receive multiple notifications.

Use primary keys and foreign keys to maintain these relationships.

## 9. Main Application Workflow

The most important end-to-end flow is:

### Step 1: Admin Adds Products

Admin logs in and adds software products.

Example: BrightBooks.

The product is saved in the `products` table.

### Step 2: Admin Creates Plans

Admin creates plans for BrightBooks.

Example:

-   Monthly: ₹499
-   Yearly: ₹4,999

These are saved in the `plans` table.

### Step 3: Product Appears in Public Catalogue

The customer opens `products.html`.

The Flask backend retrieves published products from the `products`
table.

The customer sees BrightBooks and its available plans.

**Do not hardcode products separately in the customer page.**

### Step 4: Customer Selects a Plan

Customer opens `product_detail.html`, selects a plan and proceeds to
`checkout.html`.

### Step 5: Customer Completes Payment

For the prototype, use simulated payment.

Possible payment results:

-   Successful
-   Pending
-   Failed

Real payment gateway integration is optional and should not be attempted
unless time and credentials are available.

### Step 6: Subscription Activation

After successful payment verification:

-   Create the subscription.
-   Update subscription status to Active.
-   Record the payment.
-   Generate the invoice.
-   Update the invoice status appropriately.

### Step 7: Customer Dashboard

Customer can view:

-   Purchased subscriptions.
-   Subscription status.
-   Expiry dates.
-   Invoices.
-   Payment history.

### Step 8: Staff Operations

Staff can view customers, subscriptions, quotations, invoices and
payments according to their permissions.

### Step 9: Admin Dashboard

Admin can view overall business statistics, manage the system and
monitor revenue.

## 10. Design and UI Requirements

Use a consistent design system throughout the application.

Suggested style:

-   Modern SaaS dashboard.
-   Clean and professional.
-   Responsive layout.
-   Consistent navigation.
-   Reusable sidebar.
-   Clear tables.
-   Summary cards.
-   Search and filter options.
-   Status badges.
-   Confirmation messages.
-   Form validation.

### Role-specific interfaces

All roles can share the same overall design language, but they must have
separate interfaces and permissions.

-   **Admin:** Full company-level overview and controls.
-   **Staff:** Operational dashboard and limited management options.
-   **Customer:** Personal subscription information and purchasing
    interface.

Use separate dashboards and sidebars for all three roles.

## 11. Suggested Technology Stack

  Layer                  Technology
  ---------------------- ---------------------------
  Frontend               HTML
  Styling                CSS, Bootstrap
  Interactivity          JavaScript
  Backend                Python Flask
  Database               SQLite
  Database integration   Flask-SQLAlchemy
  Authentication         Flask-Login
  Password security      Werkzeug password hashing

This is a suggested implementation stack, not a mandatory requirement
from the assignment.

Avoid introducing multiple backend frameworks unless there is a strong
reason.

## 12. Important Development Rules

All team members and AI assistants must follow these rules:

1.  Use the Brightloop Software business scenario.
2.  Maintain the three roles: Admin, Staff and Customer.
3.  Use one common database.
4.  Keep role-specific dashboards separate.
5.  Keep public pages separate from authenticated dashboards.
6.  Admin-created published products must appear dynamically in the
    customer catalogue.
7.  Plans must be linked to products.
8.  Subscriptions must be linked to customers and plans.
9.  Invoices must be linked to customers and subscriptions.
10. Payments must be linked to invoices.
11. Only Admin can create staff accounts.
12. Only Admin can create discount rules.
13. Customers must only access their own records.
14. Staff must have restricted permissions.
15. Enforce permissions in backend routes.
16. Never store plain-text passwords.
17. Validate form inputs on both frontend and backend.
18. Avoid hardcoding sample data as the final implementation.
19. Do not confuse invoice status with payment status.
20. Do not claim real payment processing when only simulated payments
    are implemented.

### Important Status Distinction

**Subscription status:**

-   Draft
-   Quotation
-   Confirmed
-   Active
-   Closed

**Invoice status:**

-   Draft
-   Confirmed
-   Paid

**Payment status:**

-   Pending
-   Successful
-   Failed

Payment statuses are a proposed implementation detail; the assignment
requires payment recording but does not prescribe these exact values.

## 13. Prototype Development Priority

Build the project in this order.

### Priority 1 -- Essential Working Flow

1.  Flask project setup.
2.  SQLite database setup.
3.  User registration and login.
4.  Role-based redirection.
5.  Admin product management.
6.  Admin plan management.
7.  Public product catalogue.
8.  Product details.
9.  Customer checkout.
10. Simulated payment.
11. Subscription creation.
12. Invoice generation.

### Priority 2 -- Staff Section

1.  Staff dashboard.
2.  Customer management.
3.  Subscription management.
4.  Invoice management.
5.  Payment management.
6.  Quotation management.

### Priority 3 -- Additional Admin Features

1.  Discount management.
2.  Tax management.
3.  Reports.
4.  Staff management.
5.  Notifications.
6.  Settings.

### Priority 4 -- Improvements

1.  Search and filters.
2.  Better dashboard charts.
3.  Invoice printing.
4.  Responsive design.
5.  Better validation and error handling.
6.  Subscription renewal reminders.

**Do not attempt to implement every feature before testing the main
customer purchase flow.**

## 14. Proposed Enhancements

These are optional improvements and should not replace the required
assignment features.

### 1. Smart Subscription Setup

Provide a guided form for Admin to create plans.

Steps:

-   Select product.
-   Select billing cycle.
-   Enter price.
-   Set availability.
-   Configure renewal and pause options.
-   Review and save.

### 2. Custom Reports

Allow Admin to filter revenue and subscription reports by:

-   Product.
-   Date range.
-   Subscription status.
-   Payment status.

### 3. Better Payment Monitoring

Provide clear payment indicators:

-   Pending.
-   Successful.
-   Failed.

### 4. User-friendly Dashboard

Display useful statistics and simple visual summaries rather than
overwhelming users with data.

These enhancements are proposed ideas, not requirements explicitly
stated in the assignment.

## 15. Instructions for AI Coding Agents -- IMPORTANT

Anyone using this handoff in their own AI coding assistant or VS Code
Agent should provide this document as the common project specification.

The AI coding assistant must:

1.  Treat this document as the common project specification.
2.  Follow the same Brightloop business scenario.
3.  Preserve the three roles: Admin, Staff and Customer.
4.  Use the same page names and file structure unless the team
    explicitly agrees to a change.
5.  Use the same database entities and relationships.
6.  Avoid inventing new mandatory requirements.
7.  Clearly label additional suggestions as optional.
8.  Keep code compatible with the agreed technology stack.
9.  Avoid changing the architecture without discussing the impact.
10. Reuse existing files and functions rather than unnecessarily
    creating duplicates.
11. Make sure frontend and backend functionality are connected.
12. Prioritize a working end-to-end prototype.
13. Explain which files need to be created or modified for each feature
    when explanation is requested.
14. Keep all project members aligned with this specification.

### Special Coding Challenge Instructions

This project may be developed during a **three-hour coding challenge**.
Therefore:

-   Do not build the entire project unless explicitly requested.
-   Build only the specific part or feature requested by the user.
-   Do not start coding until the user identifies the required part.
-   Prioritize a working implementation that fits the available time.
-   Keep explanations minimal; provide direct, usable code.
-   Avoid unnecessary features, files, dependencies and architecture
    changes.
-   Follow the existing project structure and reuse existing code.
-   Mention the exact filename for every code change.
-   Provide complete code for the requested part when asked.
-   Include required database changes and concise run/test instructions.
-   Do not use placeholder functions while claiming a feature is
    complete.
-   Keep naming consistent across the application.
-   If a requirement is unclear or conflicts with this specification,
    ask before making a major architectural change.

## Final Project Goal

Build one integrated Subscription Management System for Brightloop
Software.

The application must allow Admin to manage products, plans and business
operations; Staff to handle daily subscription operations; and Customers
to browse products, purchase plans and manage their own subscriptions.

All three roles must work through one connected application and one
shared database.

------------------------------------------------------------------------

## Quick Instruction to Give the VS Code AI Agent

Read `MEMZO_PROJECT_CONTEXT.md` completely and treat it as the official
project specification.

Do not build the entire project. Wait for my specific coding task and
implement only that part. Follow the existing Flask architecture, folder
structure, database design, naming conventions and role permissions.
Reuse existing files and code. Keep explanations minimal and prioritize
correct, working code suitable for a three-hour coding challenge. Do not
add unnecessary features or change the architecture without asking me.
