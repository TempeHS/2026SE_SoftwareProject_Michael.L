# Huddle — Sprint Backlog

---

## Sprint 1 — Database + Skeleton

**Sprint Goal:** Build a working login page with Google Authenticator 2FA and set up the SQL database schema with empty placeholder pages for the main app views.

**Committed Items (from Product Backlog):**

| PB ID | User Story |
|-------|------------|
| PB-001 | Register an account with email and password |
| PB-002 | Set up Google Authenticator 2FA |
| PB-003 | Log in with email, password, and 2FA code |

**Sprint Plan:**

| # | Task | PB ID |
|---|------|-------|
| 1 | Design and create SQL database schema for login | PB-001 |
| 2 | Build registration form (email + password input, validation, store to DB) | PB-001 |
| 3 | Integrate Google Authenticator — generate QR code on registration, verify TOTP on login | PB-002 |
| 4 | Build login page (email + password + 2FA code entry, session handling) | PB-003 |
| 5 | Create empty placeholder pages for: Dashboard, Group View, Event Feed, Vote Screen | — |
| 6 | Set up basic routing between login and placeholder pages | — |

**Unit Test Summary Table:**

| Test ID | Test Name | What It Tests | Input | Expected Output | Actual Output | Pass / Fail |
|---------|-----------|---------------|-------|-----------------|---------------|-------------|
| T1-01 | Valid Registration | PB-001 criterion 1 — account creation with valid email/password | New email + strong password | Account created; user redirected to 2FA setup | | |
| T1-02 | Duplicate Email Rejection | PB-001 criterion 1 — duplicate email handling | Already-registered email + any password | Error: "Email already in use" displayed; no duplicate account created | | |
| T1-03 | 2FA Setup | PB-002 criterion 1 — QR code generated and valid TOTP accepted | Scan QR with Google Authenticator; enter 6-digit code | 2FA setup confirmed; user account marked as 2FA-enabled in DB | | |
| T1-04 | Valid Login with 2FA | PB-003 criterion 1 — successful login flow | Valid email, password, and current 6-digit TOTP code | User authenticated; redirected to dashboard within 3 seconds | | |
| T1-05 | Invalid 2FA Code Rejected | PB-003 criterion 1 — expired/wrong TOTP handling | Valid email + password + incorrect/expired 6-digit code | Error: "Invalid or expired code" displayed; login blocked | | |

**Sprint Review:**

- What was built and demonstrated: Working login page with Google Authenticator 2FA, SQL database schema, and empty placeholder pages for Dashboard and Group View (will eventually hole Event Feed, and Vote Screen). All committed items (PB-001, PB-002, PB-003) were completed.
- Client/stakeholder feedback:
  - "Secure form feedback has an empty page – it leads to a 'not found' error" → Fixed: added missing route for secure form template button.
  - "Logout button failed. It just took me back to the home screen" → Fixed: changed route so logout button returns to the login page and clears the session keys.
- Items not completed and reason: None — all Sprint 1 items were completed.

**Sprint Retrospective:**

- What went well: All three committed backlog items were delivered within the sprint. Client testing caught two routing bugs that were identified and resolved quickly.
- What didn't go well: Two routing errors (secure form template and logout button) were not caught before client testing, suggesting more thorough pre-review testing is needed.
- What will be improved in Sprint 2: Manually test all navigation routes and button flows before client review to catch routing issues earlier.

---

## Sprint 2 — Core Features

**Sprint Goal:** Implement core event proposal and voting logic, and group creation/joining.

to be done ✍️(◔◡◔)
