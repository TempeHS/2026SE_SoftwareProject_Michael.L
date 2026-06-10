# Huddle - Sprint Backlog

---

## Sprint 1 - Database + Skeleton

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
| 3 | Integrate Google Authenticator - generate QR code on registration, verify TOTP on login | PB-002 |
| 4 | Build login page (email + password + 2FA code entry, session handling) | PB-003 |
| 5 | Create empty placeholder pages for: Dashboard, Group View, Event Feed, Vote Screen | - |
| 6 | Set up basic routing between login and placeholder pages | - |

**Unit Test Summary Table:**

| Test ID | Test Name | What It Tests | Input | Expected Output | Actual Output | Pass / Fail |
|---------|-----------|---------------|-------|-----------------|---------------|-------------|
| T1-01 | Valid Registration | PB-001 criterion 1 - account creation with valid email/password | New email + strong password | Account created; user redirected to 2FA setup | Account created successfully; user redirected to 2FA setup page | Pass |
| T1-02 | Duplicate Email Rejection | PB-001 criterion 1 - duplicate email handling | Already-registered email + any password | Error: "Email already in use" displayed; no duplicate account created | Error displayed; no duplicate account created | Pass |
| T1-03 | 2FA Setup | PB-002 criterion 1 - QR code generated and valid TOTP accepted | Scan QR with Google Authenticator; enter 6-digit code | 2FA setup confirmed; user account marked as 2FA-enabled in DB | QR code generated; TOTP verified; account marked 2FA-enabled in DB | Pass |
| T1-04 | Valid Login with 2FA | PB-003 criterion 1 - successful login flow | Valid email, password, and current 6-digit TOTP code | User authenticated; redirected to dashboard within 3 seconds | User authenticated and redirected to dashboard successfully | Pass |
| T1-05 | Invalid 2FA Code Rejected | PB-003 criterion 1 - expired/wrong TOTP handling | Valid email + password + incorrect/expired 6-digit code | Error: "Invalid or expired code" displayed; login blocked | Error displayed; login blocked for invalid/expired code | Pass |

**Sprint Review:**

- What was built and demonstrated: Working login page with Google Authenticator 2FA, SQL database schema, and empty placeholder pages for Dashboard and Group View (will eventually hole Event Feed, and Vote Screen). All committed items (PB-001, PB-002, PB-003) were completed.
- Client/stakeholder feedback:
  - "Secure form feedback has an empty page - it leads to a 'not found' error" → Fixed: added missing route for secure form template button.
  - "Logout button failed. It just took me back to the home screen" → Fixed: changed route so logout button returns to the login page and clears the session keys.
- Items not completed and reason: None - all Sprint 1 items were completed.

**Sprint Retrospective:**

- What went well: All three committed backlog items were delivered within the sprint. Client testing caught two routing bugs that were identified and resolved quickly.
- What didn't go well: Two routing errors (secure form template and logout button) were not caught before client testing, suggesting more thorough pre-review testing is needed.
- What will be improved in Sprint 2: Manually test all navigation routes and button flows before client review to catch routing issues earlier.

---

## Sprint 2 - Core Features

**Sprint Goal:** Implement core event proposal and voting logic, and group creation/joining.

**Committed Items (from Product Backlog):**

| PB ID | User Story |
|-------|------------|
| PB-004 | Create a new friend group |
| PB-005 | Join a group using an invite code |
| PB-006 | Propose an event with name, date/time, and location |
| PB-007 | Vote Yes/No/Maybe on a proposed event |

**Sprint Plan:**

| # | Task | PB ID |
|---|------|-------|
| 1 | Build group creation form (group name input, generate 6-char invite code, save to DB) | PB-004 |
| 2 | Build group joining flow (invite code input, validate against DB, link user to group) | PB-005 |
| 3 | Build event proposal form (name max 30 chars, date/time picker, location max 100 chars) | PB-006 |
| 4 | Display proposed events in group event feed | PB-006 |
| 5 | Build Yes/No/Maybe voting buttons per event | PB-007 |
| 6 | Implement real-time vote tally (percentage breakdown, updates within 2 seconds) | PB-007 |

**Unit Test Summary Table:**

| Test ID | Test Name | What It Tests | Input | Expected Output | Actual Output | Pass / Fail |
|---------|-----------|---------------|-------|-----------------|---------------|-------------|
| T2-01 | Group Creation | PB-004 criterion 1 - group created with name and invite code | Valid group name | Group saved to DB; unique 6-char invite code generated and displayed | Group created successfully with invite code generated | Pass |
| T2-02 | Group Join via Invite Code | PB-005 criterion 1 - valid invite code links user to group | Valid 6-char invite code | User linked to group; group appears in their dashboard | User successfully joined group via invite code | Pass |
| T2-03 | Invalid Invite Code Rejected | PB-005 criterion 1 - invalid code handling | Non-existent invite code | Error displayed; user not added to any group | Error shown; user not added to group | Pass |
| T2-04 | Event Proposal Form | PB-006 criterion 1 - event created with name, date/time, location | Event name (≤30 chars), date/time, location (≤100 chars) | Event saved to DB and appears in group event feed | Event proposal form completed; events display correctly in feed | Pass |
| T2-05 | Yes/No/Maybe Voting | PB-007 criterion 1 - vote recorded and tally displayed | Logged-in user clicks Yes, No, or Maybe on an event | Vote saved to DB; updated tally visible to user | Voting implemented; vote totals display correctly | Pass |
| T2-06 | Real-Time Vote Tally Update | PB-007 criterion 2 - tally updates within 2 seconds without page reload | Two users vote on same event | Vote percentages update within 2 seconds for all group members | Feature determined out of scope; removed from sprint | Fail |

**Sprint Review:**

- What was built and demonstrated: Group creation (PB-004) and joining via invite code (PB-005) were completed. Event proposal form with name, date/time, and location fields was built and events display correctly in the group feed (PB-006). Yes/No/Maybe voting with visible vote tallies was implemented, along with a detailed event view showing location, attendee votes, and role assignment (PB-007).
- Client/stakeholder feedback:
  - Client requested a map view for event locations → Implemented using Leaflet.js and OpenStreetMap API; location input updated to autofill.
  - Client requested role assignment for group leaders → Implemented; group leader can assign and create custom roles, which are saved per group in the DB.
  - Client requested attendance tracking → Group leader can now close events and mark attendance; attendance percentage is displayed next to member names.
- Items not completed and reason:
  - Real-time vote tally updates (PB-007 criterion 2) - after investigation, auto-refreshing votes every 2 seconds was determined to be out of scope for this sprint and will not be carried forward.

**Sprint Retrospective:**

- What went well: All four core committed backlog items (PB-004 through PB-007) were delivered. Several client-requested enhancements (map view, role assignment, attendance tracking) were implemented as nice-to-haves on top of the committed scope.
- What didn't go well: A routing bug was introduced when the detailed event view was added - voting from that screen redirected users back to the original voting page instead of staying in context. This wasn't caught before it was committed. The real-time voting tally feature was started before it was confirmed as feasible, leading to wasted effort before it was scoped out.
- What will be improved in Sprint 3: Test all routing paths after adding new screens before committing. Assess technical feasibility of a feature before beginning implementation to avoid scope creep and abandoned work.

## Sprint 3 - Finalisation

**Sprint Goal:** Complete PWA responsiveness across all screen sizes, finalise the UI/UX design, and build the front home page.

**Committed Items (from Product Backlog):**

| PB ID | User Story |
|-------|------------|
| PB-008 | View the app correctly on any device screen size (320px–1920px) |
| PB-009 | Experience a consistent and intuitive UI across all app screens |

**Sprint Plan:**

| # | Task | PB ID |
|---|------|-------|
| 1 | Implement responsive CSS/layout so all screens render correctly from 320px to 1920px | PB-008 |
| 2 | Test and fix layout breakpoints on mobile, tablet, and desktop | PB-008 |
| 3 | Design and build the front home/landing page | PB-009 |
| 4 | Apply consistent UI styling (typography, colours, spacing) across all screens | PB-009 |
| 5 | Conduct pre-review navigation and routing check across all pages | - |

**Unit Test Summary Table:**

| Test ID | Test Name | What It Tests | Input | Expected Output | Actual Output | Pass / Fail |
|---------|-----------|---------------|-------|-----------------|---------------|-------------|
| T3-01 | Mobile Responsiveness (320px) | PB-008 criterion 1 – layout renders correctly at minimum width | Browser resized to 320px; navigate all core screens | No overlapping elements, cut-off text, or broken layouts; all buttons usable | | |
| T3-02 | Desktop Responsiveness (1920px) | PB-008 criterion 1 – layout renders correctly at maximum width | Browser at full 1920px; navigate all core screens | Content is readable, well-spaced, and no layout breaks | | |
| T3-03 | Cross-Browser Compatibility | PB-008 criterion 1 – consistent rendering across browsers | Open app in Chrome, Firefox, and Safari; perform login and vote | All features and layouts function identically across all three browsers | | |
| T3-04 | Home Page Load | PB-009 criterion 1 – landing page displays correctly | Navigate to the app's root URL | Home page loads with correct layout, navigation links, and branding | | |
| T3-05 | UI Consistency Across Screens | PB-009 criterion 1 – consistent styling across all views | Navigate through all screens (login, dashboard, group view, event feed, vote screen) | Typography, colours, and spacing are consistent; no unstyled or broken elements | | |
