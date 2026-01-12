# Laboratory Management System - Workflow Documentation

## Table of Contents

1. [Introduction](#introduction)
2. [Authentication Workflows](#authentication-workflows)
3. [Equipment Management Workflows](#equipment-management-workflows)
4. [Lab Experiment Workflows](#lab-experiment-workflows)
5. [Booking Workflows](#booking-workflows)
6. [Maintenance Workflows](#maintenance-workflows)
7. [Asset Lifecycle Workflows](#asset-lifecycle-workflows)
8. [Payment Workflows](#payment-workflows)
9. [Administrative Workflows](#administrative-workflows)
10. [Integration Workflows](#integration-workflows)

---

## Introduction

### Purpose of This Document

This workflow documentation provides detailed process flows for all major operations in the Laboratory Management System. Each workflow includes:

- **Process Flow Diagram**: Visual representation of the workflow
- **Step-by-Step Instructions**: Detailed actions for each step
- **Role Responsibilities**: Who does what at each stage
- **Decision Points**: Criteria for different paths
- **Expected Outcomes**: What happens at completion
- **Error Handling**: How to handle exceptions

### Workflow Notation Guide

```
[Start] → Process Step → {Decision?} → [End]

Symbols:
→       : Flow direction
[ ]     : Start/End point
( )     : Process/Action
{ }     : Decision point
[A]     : Approval required
[N]     : Notification sent
||      : Parallel processes
⚠       : Warning/Alert
✓       : Success
✗       : Failure/Rejection
```

---

## Authentication Workflows

### 1. User Login Workflow

```
[Start: User visits system]
         ↓
(Enter email and password)
         ↓
{Credentials valid?} ──✗→ (Show error message) → [End]
         ↓ ✓
{Account active?} ──✗→ (Show "Account locked") → [End]
         ↓ ✓
(Generate authentication token)
         ↓
(Store token in localStorage + cookies)
         ↓
(Load user profile and permissions)
         ↓
{Which role?}
    ↓        ↓        ↓         ↓
  Admin   Lecturer  Student  Technician
    ↓        ↓        ↓         ↓
(Redirect to role-specific dashboard)
         ↓
[End: User logged in successfully]
```

#### Detailed Steps:

**Step 1: Access Login Page**
- User navigates to `/login`
- System loads login form
- Form displays email and password fields

**Step 2: Submit Credentials**
- User enters institutional email
- User enters password
- Clicks "Login" button
- Form validation executed (client-side)

**Step 3: Server Authentication**
- Request sent to `/api/auth/login`
- Laravel validates credentials against database
- Password verified using bcrypt
- Account status checked (active/locked)

**Step 4: Token Generation**
- If valid: Laravel Sanctum generates token
- Token includes user ID and permissions
- Token expiration set (configurable)
- Token stored in database

**Step 5: Client Storage**
- Token received by client
- Stored in localStorage: `auth_token`
- Stored in cookies: `auth_token` (for middleware)
- User data stored: `current_user`

**Step 6: Role-Based Redirection**
- System reads user roles from token
- Determines primary role (priority: Admin > Technician > Lecturer > Student)
- Redirects to appropriate dashboard
- Loads role-specific navigation

**Error Scenarios:**

| Error | Cause | User Message | Action |
|-------|-------|--------------|--------|
| 401 | Invalid credentials | "Invalid email or password" | Stay on login page |
| 403 | Account locked | "Account locked. Contact admin" | Display contact info |
| 422 | Validation error | "Please check your input" | Highlight invalid fields |
| 500 | Server error | "System error. Try again" | Retry option |

---

### 2. Password Reset Workflow

```
[Start: User forgot password]
         ↓
(Click "Forgot Password")
         ↓
(Enter email address)
         ↓
{Email exists?} ──✗→ (Show "Email not found") → [End]
         ↓ ✓
(Generate password reset token)
         ↓
(Send reset link to email) [N]
         ↓
[Wait for user to click email link]
         ↓
(User clicks reset link)
         ↓
{Token valid?} ──✗→ (Show "Link expired") → [End]
         ↓ ✓
(Display password reset form)
         ↓
(User enters new password × 2)
         ↓
{Passwords match?} ──✗→ (Show error) → (Re-enter)
         ↓ ✓
{Password meets requirements?} ──✗→ (Show requirements) → (Re-enter)
         ↓ ✓
(Update password in database)
         ↓
(Invalidate all existing tokens)
         ↓
(Send confirmation email) [N]
         ↓
[End: Password reset successful]
```

#### Password Requirements:
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one number
- At least one special character
- Not same as previous 3 passwords

---

### 3. User Logout Workflow

```
[Start: User clicks logout]
         ↓
(Confirm logout action)
         ↓
{Confirmed?} ──✗→ [Cancel: Stay logged in]
         ↓ ✓
(Send logout request to server)
         ↓
(Server revokes authentication token)
         ↓
(Clear localStorage: auth_token, current_user)
         ↓
(Clear cookies: auth_token, current_user)
         ↓
(Clear session data)
         ↓
(Redirect to login page)
         ↓
[End: User logged out]
```

---

## Equipment Management Workflows

### 1. Add New Equipment Workflow (Admin)

```
[Start: Admin wants to add equipment]
         ↓
(Navigate to Equipment → All Equipment)
         ↓
(Click "Add New Equipment")
         ↓
(Fill equipment information form)
    - Basic Info (Name, Category, Model)
    - Purchase Info (Date, Price, Vendor)
    - Location & Status
    - Technical Specifications
         ↓
{Required fields completed?} ──✗→ (Show validation errors) → (Fix errors)
         ↓ ✓
(Upload equipment photos) [Optional]
         ↓
(Select custodian) [Optional]
         ↓
(Click "Save")
         ↓
(Validate data on server)
         ↓
{Data valid?} ──✗→ (Return errors) → (Fix and resubmit)
         ↓ ✓
(Generate unique Equipment ID)
         ↓
(Save to database)
         ↓
(Create equipment record)
         ↓
(Generate QR code/barcode)
         ↓
|| Parallel Actions ||
    ↓                ↓                    ↓
(Log activity)  (Notify custodian) [N]  (Add to inventory)
         ↓
(Display success message)
         ↓
[End: Equipment added successfully]
         ↓
{Add another?} ──✓→ (Return to add form)
         ↓ ✗
(Return to equipment list)
```

#### Equipment Information Required:

**Basic Information:**
- Equipment Name (required)
- Category (required, dropdown)
- Subcategory (optional)
- Model Number (required)
- Serial Number (required, unique)
- Manufacturer (required)

**Purchase Information:**
- Purchase Date (required)
- Purchase Price (required)
- Vendor/Supplier (required)
- Warranty Period (optional)
- Warranty Expiry Date (auto-calculated)

**Location & Status:**
- Building (required)
- Room/Lab (required)
- Storage Location (optional)
- Status (required): Available, In Use, Under Maintenance, Out of Service
- Condition (required): New, Good, Fair, Poor

**Technical Specifications:**
- Technical details (text area)
- Operating voltage (if applicable)
- Power requirements
- Dimensions
- Weight
- Special requirements

**Assignment:**
- Custodian (optional, select from staff list)
- Department (required)
- Responsibility date (auto: today)

---

### 2. Equipment Booking Workflow (Student/Lecturer)

```
[Start: User needs equipment]
         ↓
(Navigate to Equipment List)
         ↓
(Browse/Search for equipment)
         ↓
(View equipment details)
         ↓
{Equipment available?} ──✗→ (Check alternative) or (Book future date)
         ↓ ✓
(Click "Book Equipment")
         ↓
(Fill booking form)
    - Date & Time
    - Duration
    - Purpose
    - Supervisor (if student)
         ↓
{Meet booking requirements?} ──✗→ (Show requirements) → [End]
    - Course enrollment ✓
    - No outstanding fees ✓
    - Orientation completed ✓
         ↓ ✓
{Conflicts detected?} ──✓→ (Show conflicts) → (Choose different time)
         ↓ ✗
(Submit booking request)
         ↓
(Booking queued for approval)
         ↓
(Notification sent to admin) [N]
         ↓
[Wait for admin approval] [A]
         ↓
{Approved or Rejected?}
    ↓ Approved              ↓ Rejected
(Update calendar)      (Notify user with reason) [N]
(Send confirmation) [N]      ↓
(Add to user's bookings)  [End: Booking rejected]
    ↓
[End: Booking confirmed]
    ↓
[Booking Day Arrives]
    ↓
(Send reminder 24h before) [N]
    ↓
{User shows up?}
    ↓ Yes                   ↓ No
(Check out equipment)   (Mark as no-show)
(Record start time)     (Apply penalty) ⚠
    ↓                       ↓
[Use equipment]         [End: Booking missed]
    ↓
(Check in equipment)
(Inspect condition)
    ↓
{Equipment OK?}
    ↓ Yes                   ↓ No
(Mark booking complete) (Create damage report)
(Process payment)       (Assess damages)
    ↓                   (Notify admin) [N]
[End: Completed]            ↓
                    (Initiate liability process)
                            ↓
                    [End: Incident recorded]
```

#### Booking Rules & Policies:

**Advance Booking:**
- Minimum: 24 hours in advance
- Maximum: 30 days in advance
- Exceptions require admin approval

**Duration Limits:**
| User Type | Max Duration | Extensions |
|-----------|--------------|------------|
| Student | 4 hours | 1 extension (2 hours) |
| Lecturer | 8 hours | Unlimited |
| Researcher | 24 hours | Negotiable |

**Cancellation Policy:**
- Free cancellation: >24 hours notice
- Late cancellation (< 24h): Warning issued
- No-show: 1 strike (3 strikes = suspension)

**Equipment Checkout:**
1. Present student/staff ID
2. Sign equipment log
3. Inspect equipment with technician
4. Take photos if needed
5. Receive equipment

**Equipment Return:**
1. Return on time (grace period: 15 minutes)
2. Inspect with technician
3. Report any issues
4. Sign return log
5. Complete feedback form

---

### 3. Equipment Maintenance Request Workflow

```
[Start: Equipment issue detected]
         ↓
{Who detected issue?}
    ↓ Student          ↓ Lecturer       ↓ Technician
(Report to lecturer) (Access system) (Create task directly)
    ↓                      ↓                ↓
(Lecturer logs in)  (Click "Request     [Skip to Admin Review]
    ↓                Maintenance")
(Navigate to Maintenance)      ↓
         ↓              ↓
         └──────────────┘
                ↓
(Fill maintenance request form)
    - Select equipment
    - Describe issue
    - Select issue type
    - Set urgency
    - Upload photos
         ↓
{Is safety issue?} ──✓→ (Mark as CRITICAL) [Auto-prioritize]
         ↓ ✗
(Submit request)
         ↓
(Request logged in system)
         ↓
(Notification sent to admin) [N]
         ↓
[Admin Review] [A]
         ↓
(Admin reviews request)
         ↓
{Approve maintenance?}
    ↓ No                        ↓ Yes
(Reject with reason)    (Create maintenance task)
(Notify requester) [N]      ↓
    ↓                   (Assess priority)
[End: Rejected]             ↓
                    {Priority level?}
                        ↓
            ┌───────────┼───────────┐
         Critical    High      Medium/Low
            ↓           ↓            ↓
    (Assign immediately) (Assign within 24h) (Add to queue)
            ↓           ↓            ↓
            └───────────┴────────────┘
                        ↓
            (Notify assigned technician) [N]
                        ↓
            [Technician receives task]
                        ↓
            (See Maintenance Execution Workflow)
```

---

### 4. Equipment Disposal Workflow

```
[Start: Equipment candidate for disposal]
         ↓
(Custodian/Lecturer identifies equipment)
         ↓
(Assess equipment condition)
    - Age and usage
    - Repair costs vs. value
    - Safety concerns
    - Obsolescence
    - Replacement availability
         ↓
{Meets disposal criteria?} ──✗→ [End: Keep equipment]
         ↓ ✓
(Navigate to Asset Disposal → Proposals)
         ↓
(Click "New Disposal Proposal")
         ↓
(Fill disposal proposal form)
    - Equipment selection
    - Disposal reason
    - Condition assessment
    - Cost analysis
    - Proposed disposal method
    - Photos/documentation
         ↓
{Required fields complete?} ──✗→ (Show errors) → (Fix)
         ↓ ✓
(Submit proposal)
         ↓
(Proposal logged with timestamp)
         ↓
(Notification sent to admin) [N]
         ↓
[Admin Review Phase] [A]
         ↓
(Admin reviews proposal)
         ↓
{Additional info needed?} ──✓→ (Request clarification) → (Lecturer updates)
         ↓ ✗                           ↓
{Technical review needed?} ──✓→ (Assign to tech team) → (Technical report)
         ↓ ✗                           ↓
{Financial review needed?} ──✓→ (Forward to finance) → (Financial analysis)
         ↓ ✗                           ↓
         └────────────────────────────┘
                        ↓
            (Compile all reviews)
                        ↓
            {Final decision?}
                ↓               ↓
            Approve         Reject
                ↓               ↓
    (Approve disposal)  (Reject with reason)
    (Select disposal method) (Notify submitter) [N]
    (Set timeline)          ↓
    (Assign responsible)  [End: Proposal rejected]
    (Notify all parties) [N]
                ↓
    [Disposal Execution Phase]
                ↓
    (Equipment decommissioned)
                ↓
    {Has sensitive data?} ──✓→ (Data wiping/destruction)
                ↓ ✗
    (Remove from active inventory)
                ↓
    (Update equipment status: "Disposed")
                ↓
    {Disposal method?}
        ↓           ↓           ↓           ↓
      Sale      Donation    Recycling    Disposal
        ↓           ↓           ↓           ↓
    (Conduct    (Transfer    (Arrange      (Proper
     auction)    to org)     recycling)    disposal)
        ↓           ↓           ↓           ↓
    (Record     (Get receipt)(Get cert)   (Document)
     revenue)
        ↓           ↓           ↓           ↓
        └───────────┴───────────┴───────────┘
                        ↓
            (Complete disposal form)
                        ↓
            (Upload documentation)
            - Disposal certificate
            - Photos
            - Financial records
            - Transfer documents
                        ↓
            (Archive equipment record)
                        ↓
            (Update disposal history)
                        ↓
            (Close proposal)
                        ↓
            (Notify submitter) [N]
                        ↓
        [End: Disposal completed]
```

---

## Lab Experiment Workflows

### 1. Create Lab Experiment Workflow (Lecturer)

```
[Start: Lecturer needs new experiment]
         ↓
(Navigate to Lab Experiments)
         ↓
(Click "Create New Experiment")
         ↓
(Enter basic information)
    - Title
    - Course/Subject
    - Duration
    - Difficulty level
    - Max students
         ↓
(Select required equipment)
    - Search equipment
    - Add to list
    - Specify quantities
    - Note special requirements
         ↓
(Add experiment content)
    Section 1: Introduction/Theory
    Section 2: Learning Objectives
    Section 3: Materials List
    Section 4: Safety Precautions
    Section 5: Procedure (step-by-step)
    Section 6: Observations/Data Tables
    Section 7: Calculations/Analysis
    Section 8: Discussion Questions
    Section 9: References
         ↓
{Content complete?} ──✗→ (Save as draft) → [End: Draft saved]
         ↓ ✓
(Upload resources)
    - Lab manual PDF
    - Diagrams/images
    - Data sheets
    - Videos
    - Additional references
         ↓
(Set experiment parameters)
    - Prerequisite knowledge
    - Safety level
    - Supervision required
    - Assessment method
         ↓
(Preview experiment)
         ↓
{Satisfied with preview?} ──✗→ (Edit content)
         ↓ ✓
(Click "Publish")
         ↓
(System validates content)
         ↓
{Validation passed?} ──✗→ (Show errors) → (Fix issues)
         ↓ ✓
(Publish experiment)
         ↓
|| Parallel Actions ||
    ↓                   ↓                   ↓
(Add to course)  (Notify students) [N]  (Update catalog)
    ↓                   ↓                   ↓
    └───────────────────┴───────────────────┘
                        ↓
        (Display success message)
                        ↓
        [End: Experiment published]
```

---

### 2. Student Access Experiment Workflow

```
[Start: Student needs experiment info]
         ↓
(Login to system)
         ↓
(Navigate to Lab Experiments)
         ↓
(View available experiments)
    - Filter by course
    - Filter by difficulty
    - Search by keyword
         ↓
(Select experiment)
         ↓
(View experiment details)
    - Read introduction
    - Review objectives
    - Check equipment list
    - Read safety precautions
    - Study procedure
         ↓
{Download materials?}
    ↓ Yes                       ↓ No
(Download lab manual)      (Continue reading)
(Download data sheets)          ↓
(Save to device)         {Understand content?}
    ↓                        ↓ Yes    ↓ No
(Materials saved)       (Prepared)  (Review again)
    ↓                        ↓            ↓
    └────────────────────────┘            │
                ↓                          │
{Watch tutorial video?}                   │
    ↓ Yes           ↓ No                 │
(Play video)    (Skip video)              │
    ↓               ↓                     │
    └───────────────┘                     │
                ↓                          │
{Ready for lab?} ◄─────────────────────────┘
    ↓ Yes               ↓ No
(Book lab session)  (Study more)
    ↓                   ↓
[See Booking Workflow] [End: Needs more prep]
```

---

## Booking Workflows

### 1. Lab Session Booking Workflow (Comprehensive)

```
[Start: Lecturer plans lab session]
         ↓
(Navigate to Booking → Lab Session)
         ↓
(View calendar of available slots)
         ↓
(Select date and time)
         ↓
{Lab available?} ──✗→ (Show conflicts) → (Choose different slot)
         ↓ ✓
(Click "Book Session")
         ↓
(Fill booking form)
    - Course name/code
    - Class/Group name
    - Number of students
    - Lab preference
    - Duration
    - Associated experiment
    - Special requirements
    - Equipment needed
         ↓
{All required fields filled?} ──✗→ (Highlight missing) → (Complete)
         ↓ ✓
(Check equipment availability)
         ↓
{All equipment available?}
    ↓ No                        ↓ Yes
(Show missing equipment)    (Continue booking)
    ↓                           ↓
{Use alternatives?}         (Review booking details)
    ↓ No        ↓ Yes          ↓
[Cancel]  (Select alt)    (Submit booking)
              ↓                 ↓
              └─────────────────┘
                        ↓
            (Booking request created)
                        ↓
            (Set status: "Pending")
                        ↓
            || Parallel Notifications ||
                ↓               ↓
        (Notify admin) [N]  (Confirm to lecturer) [N]
                ↓               ↓
                └───────────────┘
                        ↓
            [Admin Review Phase] [A]
                        ↓
        (Admin reviews booking)
                        ↓
        {Check conflicts with:}
            - Other bookings
            - Maintenance schedules
            - Lab capacity
            - Equipment availability
            - Holidays/closures
                        ↓
        {Conflicts found?}
            ↓ Yes                   ↓ No
    (Contact lecturer)      (Check lab capacity)
    (Propose alternatives)          ↓
    (Negotiate time)        {Capacity sufficient?}
            ↓                   ↓ Yes    ↓ No
    {Resolved?}         (Approve)  (Reject: Overcapacity)
        ↓ Yes   ↓ No       ↓           ↓
    (Approve) [Reject]     │           │
        ↓           ↓      │           │
        └───────────┴──────┘           │
                ↓                       │
        (Update booking status)         │
                ↓                       │
        {Status?}                       │
            ↓ Approved                  │
    (Status: "Confirmed")               │
    (Reserve lab)                       │
    (Reserve equipment)                 │
    (Block calendar)                    │
    (Generate booking ID)               │
            ↓                           │
    || Parallel Actions ||              │
        ↓               ↓               │
(Notify lecturer) [N] (Notify students) [N]
(Send confirmation)   (Send details)    │
        ↓               ↓               │
        └───────────────┘               │
                ↓                       │
    (Add to lecturer's schedule)        │
    (Add to students' calendars)        │
            ↓                           │
    [Reminder Phase]                    │
        ↓                               │
    (24h before: Send reminder) [N]    │
        ↓                               │
    (2h before: Send alert) [N]        │
        ↓                               │
    [Session Day]                       │
        ↓                               │
    (Mark session as "In Progress")     │
        ↓                               │
    {Lecturer checks in?}               │
        ↓ Yes                  ↓ No    │
    (Session started)    (Wait 30 min)  │
    (Record start time)         ↓       │
        ↓               {Checked in?}   │
    (Take attendance)       ↓ No       │
        ↓           (Mark no-show) ⚠   │
    [Session in progress]       ↓       │
        ↓           (Notify admin) [N]  │
    {Issues during session?}    ↓       │
        ↓ Yes          [End: Cancelled] │
(Report issue)                          │
(Create incident report)                │
        ↓ No                            │
    [Session ends]                      │
        ↓                               │
    (Lecturer marks complete)           │
        ↓                               │
    (Final attendance confirmed)        │
        ↓                               │
    (Equipment returned)                │
        ↓                               │
    {Equipment condition OK?}           │
        ↓ Yes              ↓ No        │
    (Mark complete)  (Report damage)    │
        ↓            (Create incident)  │
        │                   ↓           │
        │           (Assess liability)  │
        │                   ↓           │
        └───────────────────┘           │
                ↓                       │
    (Generate session report)           │
        ↓                               │
    (Record in session logs)            │
        ↓                               │
    (Process any fees)                  │
        ↓                               │
    (Send feedback form to students) [N]│
        ↓                               │
    [End: Session completed]            │
                                        │
            ↓ Rejected ◄────────────────┘
    (Status: "Rejected")
    (Notify lecturer with reason) [N]
    (Suggest alternatives)
        ↓
    [End: Booking rejected]
```

---

## Maintenance Workflows

### 1. Complete Maintenance Task Workflow (Technician)

```
[Start: Technician assigned task]
         ↓
(Receive task notification) [N]
         ↓
(Login to system)
         ↓
(Navigate to Maintenance Management)
         ↓
(View assigned tasks)
         ↓
(Select task to work on)
         ↓
(Review task details)
    - Equipment info
    - Issue description
    - Priority level
    - Due date
    - Special instructions
    - Previous maintenance history
         ↓
(Click "Start Task")
         ↓
(Status changed to "In Progress")
         ↓
(Record start time - automatic)
         ↓
[Physical Work Phase]
         ↓
(Go to equipment location)
         ↓
(Inspect equipment)
         ↓
(Take "before" photos)
         ↓
(Diagnose issue)
         ↓
{Issue confirmed?}
    ↓ No                        ↓ Yes
(Add note: Issue different) (Proceed with repair)
(Update task description)       ↓
    ↓                   (Gather tools/parts)
    └───────────────────────────┘
                ↓
        {Parts available?}
            ↓ No                    ↓ Yes
    (Click "Request Parts")     (Begin work)
    (List required parts)           ↓
    (Set urgency)           (Perform maintenance)
    (Submit request)                ↓
        ↓                   (Follow procedures)
    [Wait for parts] [A]            ↓
        ↓                   (Document steps)
    (Parts arrive)                  ↓
    (Resume work)           (Add progress notes)
        ↓                           ↓
        └───────────────────────────┘
                        ↓
            (Complete physical work)
                        ↓
            (Test equipment)
                        ↓
            {Equipment functional?}
                ↓ No                ↓ Yes
        (Further diagnosis)     (Take "after" photos)
        (Additional work)           ↓
                ↓               (Clean work area)
                └───────────────────┘
                        ↓
        [System Update Phase]
                        ↓
        (Click "Complete Task")
                        ↓
        (Fill completion report)
            - Work summary
            - Parts used (with quantities)
            - Total time spent
            - Tests performed
            - Final equipment status
            - Recommendations
                        ↓
        (Upload photos)
            - Before photos
            - During work
            - After completion
            - Any issues found
                        ↓
        (Update equipment status)
            {New status?}
                ↓               ↓               ↓
          "Operational"    "Needs Monitoring"  "Out of Service"
                ↓               ↓               ↓
        (Set as available) (Schedule follow-up) (Remove from service)
                ↓               ↓               ↓
                └───────────────┴───────────────┘
                        ↓
        {Recommend future action?}
            ↓ Yes                       ↓ No
    (Add recommendations)           (Skip)
    - Preventive maintenance            ↓
    - Part replacement schedule         │
    - Usage precautions                 │
    - Follow-up inspection              │
            ↓                           │
            └───────────────────────────┘
                        ↓
        (Submit completion report)
                        ↓
        (Status: "Pending Approval")
                        ↓
        (Notification sent to admin) [N]
                        ↓
        [Admin Review] [A]
                        ↓
        (Admin reviews report)
                        ↓
        {Report acceptable?}
            ↓ No                    ↓ Yes
    (Request revisions)         (Approve completion)
    (Specify issues)            (Update records)
    (Return to technician)      (Close task)
            ↓                       ↓
    (Technician revises)    (Generate completion certificate)
    (Resubmit)                      ↓
            ↓               (Update maintenance history)
            │                       ↓
            │               (Update equipment record)
            │                       ↓
            │               || Parallel Actions ||
            │                   ↓           ↓
            │           (Notify requester) (Log for audit)
            │                   ↓           ↓
            │                   └───────────┘
            │                       ↓
            │               (Archive task)
            │                       ↓
            │               [End: Task completed]
            │
            └──────────────────────►
```

---

### 2. Preventive Maintenance Workflow

```
[Start: Scheduled preventive maintenance]
         ↓
(System checks maintenance schedules daily)
         ↓
{Equipment due for maintenance?}
    ↓ No                        ↓ Yes
[End: Nothing due]      (Generate task list)
                                ↓
                        (For each equipment:)
                        (Create maintenance task)
                            - Equipment ID
                            - Task type: "Preventive"
                            - Priority: "Medium"
                            - Due date: Today + 7 days
                            - Standard procedure
                                ↓
                        (Assign to technician)
                        (Based on: Specialization, Workload, Availability)
                                ↓
                        (Send notifications) [N]
                                ↓
                        [Follow regular maintenance workflow]
```

---

## Asset Lifecycle Workflows

### 1. Purchase Proposal Workflow

```
[Start: Need new equipment]
         ↓
(Lecturer identifies need)
         ↓
(Navigate to Asset Purchase → Purchase Proposal)
         ↓
(Click "New Request")
         ↓
(Fill proposal form)
    Equipment Details:
        - Name and description
        - Specifications (detailed)
        - Quantity needed
        - Estimated cost per unit
        - Total estimated cost
        - Preferred vendor/model
    Justification:
        - Course requirements
        - Research needs
        - Current equipment gap
        - Expected usage
        - Number of students affected
        - Learning outcomes
    Budget:
        - Proposed budget source
        - Account/grant number
        - Budget availability
    Supporting Documents:
        - Vendor quotations (3 preferred)
        - Technical specifications
        - Course syllabus excerpt
        - Usage projections
         ↓
{All required fields complete?} ──✗→ (Show missing) → (Complete)
         ↓ ✓
(Upload attachments)
         ↓
(Preview proposal)
         ↓
{Ready to submit?} ──✗→ (Save as draft) → [End: Draft saved]
         ↓ ✓
(Submit proposal)
         ↓
(Proposal logged with ID)
         ↓
(Timestamp and submitter recorded)
         ↓
(Notification to admin) [N]
         ↓
[Admin Initial Review] [A]
         ↓
(Admin reviews proposal)
         ↓
{Meets basic criteria?}
    ↓ No                            ↓ Yes
(Reject immediately)        (Proceed to detailed review)
(Notify with feedback) [N]          ↓
    ↓                       (Check budget availability)
[End: Rejected]                     ↓
                            {Budget available?}
                                ↓ No            ↓ Yes
                        (Reject: No budget) (Continue review)
                        (Suggest alternatives)  ↓
                                ↓           (Technical review)
                        [End: Rejected]         ↓
                                        {Technical approval?}
                                            ↓ No        ↓ Yes
                                    (Request revision) (Forward to committee)
                                    (Specify issues)    ↓
                                            ↓       [Committee Review] [A]
                                    (Lecturer revises)  ↓
                                    (Resubmit)      (Committee evaluates)
                                            ↓           ↓
                                            │   {Criteria evaluation:}
                                            │   - Educational value
                                            │   - Cost-benefit analysis
                                            │   - Priority vs. other requests
                                            │   - Alternative solutions
                                            │   - Long-term sustainability
                                            │           ↓
                                            │   {Committee decision?}
                                            │       ↓           ↓
                                            │   Approve     Reject
                                            │       ↓           ↓
                                            │   (Set priority) (Notify with reason)
                                            │   (Assign to     ↓
                                            │    procurement) [End: Rejected]
                                            │       ↓
                                            │   (Notify lecturer) [N]
                                            │       ↓
                                            │   [Procurement Phase]
                                            │       ↓
                                            │   (Create purchase order)
                                            │       ↓
                                            │   (Request quotations)
                                            │       ↓
                                            │   (Vendor selection)
                                            │       ↓
                                            │   {Best vendor?}
                                            │   (Evaluate: Price, Quality,
                                            │    Warranty, Delivery, Support)
                                            │       ↓
                                            │   (Issue PO to vendor)
                                            │       ↓
                                            │   (Track order status)
                                            │       ↓
                                            │   (Update lecturer on progress) [N]
                                            │       ↓
                                            │   [Delivery Phase]
                                            │       ↓
                                            │   (Equipment arrives)
                                            │       ↓
                                            │   (Receiving inspection)
                                            │       ↓
                                            │   {Inspection passed?}
                                            │       ↓ No         ↓ Yes
                                            │   (Reject shipment) (Accept delivery)
                                            │   (Contact vendor)  ↓
                                            │   (Request replacement) (Sign receipt)
                                            │       ↓               ↓
                                            │       └───────────────┘
                                            │               ↓
                                            │       (Add to inventory)
                                            │       (See "Add Equipment" workflow)
                                            │               ↓
                                            │       (Notify lecturer) [N]
                                            │               ↓
                                            │       (Schedule orientation)
                                            │               ↓
                                            │       (Equipment ready for use)
                                            │               ↓
                                            │       (Close purchase proposal)
                                            │               ↓
                                            │       (Update purchase history)
                                            │               ↓
                                            │       [End: Purchase completed]
                                            │
                                            └───────────────►
```

---

## Payment Workflows

### 1. Booking Payment Workflow

```
[Start: Booking approved with fee]
         ↓
(System calculates fee)
    Based on:
        - Booking duration
        - Equipment type
        - User type (student/external)
        - Course vs. personal use
        - Peak/off-peak hours
         ↓
(Generate payment record)
    - Booking ID
    - User ID
    - Amount due
    - Due date
    - Description
         ↓
(Status: "Pending Payment")
         ↓
(Send payment notification) [N]
         ↓
{Payment within 48h?}
    ↓ No                        ↓ Yes
(Send reminder) [N]         (User accesses payment)
    ↓                           ↓
(Wait 24h more)         (View payment details)
    ↓                           ↓
{Still not paid?}           (Select payment method)
    ↓ Yes                       ↓
(Mark overdue) ⚠            {Payment method?}
(Notify admin)           ↓           ↓           ↓
(Risk cancellation)   Online     Counter     Invoice
    ↓                   ↓           ↓           ↓
[Payment finally made] (Pay via    (Visit     (Request
    ↓                   gateway)    finance)    invoice)
    └───────────────────┴───────────┴───────────┘
                        ↓
            (Process payment)
                        ↓
            {Payment successful?}
                ↓ No                ↓ Yes
        (Payment failed)        (Update record)
        (Retry or cancel)       (Status: "Paid")
                ↓                   ↓
        [Resolved or         (Generate receipt)
         booking cancelled]         ↓
                            (Email receipt) [N]
                                    ↓
                            (Confirm booking)
                                    ↓
                            [End: Payment completed]
```

---

## Administrative Workflows

### 1. User Management Workflow

```
[Start: Need to manage user]
         ↓
{What action?}
    ↓           ↓           ↓           ↓
Add User  Edit User  Delete User  Reset Password
    ↓           ↓           ↓           ↓
(Admin navigates to User Management)
    ↓
(Select appropriate action)
    ↓
[ADD USER PATH]
(Click "Add New User")
    ↓
(Fill user information)
    - Name
    - Email
    - Role
    - Department
    - Employee/Student ID
    ↓
(Assign permissions)
    ↓
(Generate temporary password)
    ↓
(Create user account)
    ↓
(Send welcome email with credentials) [N]
    ↓
[End: User created]

[EDIT USER PATH]
(Search and select user)
    ↓
(Modify details)
    ↓
{Change role?}
    ↓ Yes                   ↓ No
(Update permissions)    (Save changes)
(Reassign resources)        ↓
    ↓                   [End: User updated]
    └───────────────────►

[DELETE USER PATH]
(Search and select user)
    ↓
{Confirm deletion?}
    ↓ No                    ↓ Yes
[Cancel]            (Deactivate account)
                            ↓
                    (Transfer ownership of resources)
                            ↓
                    (Archive user data)
                            ↓
                    [End: User deleted]

[RESET PASSWORD PATH]
(Search and select user)
    ↓
(Generate reset link)
    ↓
(Send reset email) [N]
    ↓
[End: Reset email sent]
```

---

### 2. Report Generation Workflow

```
[Start: Need to generate report]
         ↓
(Navigate to Reports section)
         ↓
(Select report type)
    ↓           ↓           ↓           ↓
Equipment  Bookings  Maintenance  Financial
    ↓           ↓           ↓           ↓
    └───────────┴───────────┴───────────┘
                ↓
    (Configure report parameters)
        - Date range
        - Filters (department, user, status)
        - Grouping
        - Sort order
        - Output format (PDF, Excel, CSV)
                ↓
    (Preview report)
                ↓
    {Satisfied?} ──✗→ (Adjust parameters)
                ↓ ✓
    (Generate report)
                ↓
    (System compiles data)
                ↓
    (Format output)
                ↓
    (Download/Email report)
                ↓
    {Schedule recurring?}
        ↓ Yes               ↓ No
(Set schedule)      [End: Report generated]
(Auto-send recipients)
        ↓
[End: Scheduled report created]
```

---

## Integration Workflows

### 1. Email Notification Workflow

```
[Trigger Event Occurs]
    ↓
(System detects notification trigger)
    ↓
{Notification type?}
    ↓           ↓           ↓           ↓
Booking   Approval   Reminder  Alert
    ↓           ↓           ↓           ↓
    └───────────┴───────────┴───────────┘
                ↓
    (Retrieve notification template)
                ↓
    (Populate with event data)
                ↓
    (Get recipient email)
                ↓
    {Recipient preferences?}
(Check: Does user want this notification?)
                ↓
        {Enabled?}
            ↓ No                ↓ Yes
    [Skip: User opted out] (Prepare email)
                                ↓
                        (Queue for sending)
                                ↓
                        (Send via email service)
                                ↓
                        {Sent successfully?}
                            ↓ No        ↓ Yes
                    (Retry 3 times) (Log success)
                            ↓           ↓
                    {Still failed?}     │
                        ↓ Yes           │
                (Log error)             │
                (Alert admin)           │
                        ↓               │
                [End: Failed]           │
                                        │
                                [End: Sent] ◄─┘
```

---

### 2. System Backup Workflow

```
[Start: Scheduled backup time (Daily 2 AM)]
         ↓
(Check system load)
         ↓
{Safe to proceed?} ──✗→ (Wait 30 minutes) → (Retry)
         ↓ ✓
(Notify admin: Backup starting) [N]
         ↓
(Lock database for consistency)
         ↓
|| Parallel Backup ||
    ↓               ↓               ↓
(Database    (File storage)  (Configuration
 backup)        backup)         backup)
    ↓               ↓               ↓
    └───────────────┴───────────────┘
                ↓
    (Compress backup files)
                ↓
    (Encrypt backup)
                ↓
    (Upload to cloud storage)
                ↓
    {Upload successful?}
        ↓ No                ↓ Yes
(Retry 3 times)     (Verify backup integrity)
        ↓                   ↓
{Still failed?}     {Integrity OK?}
    ↓ Yes               ↓ No        ↓ Yes
(Alert admin) ⚠   (Delete bad   (Mark successful)
(Log error)         backup)         ↓
    ↓               (Alert admin)   (Update backup log)
[End: Failed]           ↓               ↓
                [End: Failed]   (Delete old backups >30 days)
                                        ↓
                                (Send success report) [N]
                                        ↓
                                (Unlock database)
                                        ↓
                                [End: Backup completed]
```

---

## Workflow Metrics & KPIs

### Performance Indicators

**Booking Workflows:**
- Average approval time: < 24 hours
- Booking success rate: > 95%
- No-show rate: < 5%
- Cancellation rate: < 10%

**Maintenance Workflows:**
- Average response time (Critical): < 4 hours
- Average completion time: < 48 hours
- First-time fix rate: > 80%
- Maintenance backlog: < 10 pending tasks

**Approval Workflows:**
- Proposal review time: < 5 days
- Approval rate: 60-70%
- Revision requests: < 30%
- Appeal success rate: 20-30%

**System Performance:**
- Login success rate: > 99%
- Page load time: < 2 seconds
- API response time: < 500ms
- System uptime: > 99.5%

---

## Troubleshooting Common Workflow Issues

### Issue: Booking Stuck in Pending

**Symptoms:**
- Booking not approved after 48 hours
- No response from admin
- Status remains "Pending"

**Resolution Steps:**
1. Check admin workload (may be backlog)
2. Verify all required information provided
3. Check for conflicting bookings
4. Contact admin directly if urgent
5. Admin can manually review and process

**Prevention:**
- Submit bookings well in advance
- Provide complete information
- Check availability before booking
- Set up admin workload alerts

---

### Issue: Maintenance Task Not Assigned

**Symptoms:**
- Task created but no technician assigned
- Task in queue for > 24 hours
- No notification received by technicians

**Resolution Steps:**
1. Check technician availability
2. Verify skill matching
3. Check workload distribution
4. Manually assign if automatic fails
5. Notify technician directly

**Prevention:**
- Maintain updated technician skills
- Balance workload distribution
- Set up assignment failure alerts
- Have backup assignment procedure

---

### Issue: Payment Not Reflecting

**Symptoms:**
- Payment made but status still pending
- No receipt generated
- Booking not confirmed

**Resolution Steps:**
1. Check payment gateway status
2. Verify transaction ID
3. Check for processing delays (24h)
4. Contact finance department
5. Manual verification and update

**Prevention:**
- Use reliable payment gateways
- Automated reconciliation daily
- Clear payment confirmation messages
- Receipt generation immediately after success

---

## Workflow Optimization Tips

### For Administrators:

1. **Batch Processing:**
   - Review multiple bookings at once
   - Approve similar proposals together
   - Schedule dedicated review times

2. **Automation:**
   - Auto-approve low-risk bookings
   - Set up recurring maintenance schedules
   - Automate reminder notifications

3. **Delegation:**
   - Assign booking approvals to department heads
   - Delegate routine tasks
   - Create approval hierarchies

### For Lecturers:

1. **Planning:**
   - Book lab sessions for entire semester
   - Prepare experiments in advance
   - Schedule equipment early

2. **Standardization:**
   - Reuse experiment templates
   - Create standard booking profiles
   - Use saved preferences

3. **Communication:**
   - Clear booking descriptions
   - Detailed maintenance requests
   - Complete proposal documentation

### For Students:

1. **Preparation:**
   - Read experiments before booking
   - Check equipment availability first
   - Have alternative time slots ready

2. **Punctuality:**
   - Arrive on time for bookings
   - Cancel with proper notice
   - Complete sessions as scheduled

3. **Feedback:**
   - Report issues immediately
   - Provide session feedback
   - Suggest improvements

### For Technicians:

1. **Organization:**
   - Prioritize by urgency and impact
   - Group similar tasks
   - Plan route for efficiency

2. **Documentation:**
   - Detailed work notes
   - Photos before/after
   - Parts and time tracking

3. **Proactive:**
   - Identify recurring issues
   - Suggest preventive maintenance
   - Report equipment trends

---

## Conclusion

This workflow documentation provides comprehensive guidance for all major processes in the Laboratory Management System. Each workflow is designed to:

- **Maximize Efficiency**: Streamlined steps reduce processing time
- **Ensure Quality**: Built-in checks and validations
- **Maintain Accountability**: Clear role assignments and audit trails
- **Enable Flexibility**: Decision points allow for exceptions
- **Support Collaboration**: Notifications keep all parties informed

### Continuous Improvement

Workflows should be reviewed and updated:
- **Quarterly**: Minor adjustments based on user feedback
- **Annually**: Major review and optimization
- **As Needed**: When new features added or policies change

### Feedback and Updates

To suggest workflow improvements:
- Email: workflows@university.edu
- Submit via system feedback form
- Discuss at user group meetings
- Contact system administrator

---

**Document Version:** 1.0
**Last Updated:** October 29, 2025
**Next Review:** January 29, 2026
**System Version:** Lab Management System v1.0

---

*This workflow documentation is a living document and will be updated as the system evolves and best practices are identified.*
