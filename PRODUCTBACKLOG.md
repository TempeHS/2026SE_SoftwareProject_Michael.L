# Huddle - Product Backlog

## Vision

To make it easier for friend groups to organise and commit to social plans by providing a simple platform where users can propose activities, vote on them, and confirm attendance - without relying on messy group chats or inconsistent responses.

---

## Backlog Table

| ID | User Story | Priority | Acceptance Criteria | Status |
|----|------------|----------|---------------------|--------|
| PB-001 | As a user, I want to register an account with my email and password so that I can access Huddle. | Must | User can submit email + password; account is created and stored in the database. Duplicate emails are rejected. | To Do |
| PB-002 | As a user, I want to set up Google Authenticator 2FA so that my account is secure. | Must | After registration, user is prompted to scan a QR code in Google Authenticator. A valid 6-digit TOTP code completes setup. | To Do |
| PB-003 | As a user, I want to log in with my email, password, and 2FA code so that I can access my groups and events. | Must | User is authenticated and redirected to the dashboard within 3 seconds of entering a valid 2FA code. Invalid/expired codes are rejected with an error message. | To Do |
| PB-004 | As a user, I want to create a new friend group so that I can invite my friends to plan together. | Must | A new group is created with a unique 6-character alphanumeric invite code. The group appears in the creator's group list. | To Do |
| PB-005 | As a user, I want to join a group using an invite code so that I can participate in my friend group's plans. | Must | Entering a valid 6-character code adds the user to the group. The group appears in their group list and they are visible to the group creator. Invalid codes display a clear error message. | To Do |
| PB-006 | As a group member, I want to propose an event with a name, date/time, and location so that my group can consider it. | Must | Event is saved with: name (max 30 chars), date/time (via picker), location (max 100 chars). Event appears in the group's event feed for all members. Inputs exceeding character limits are rejected. | To Do |
| PB-007 | As a group member, I want to vote Yes, No, or Maybe on a proposed event so that the group can reach a decision. | Must | User can cast one vote per event. Vote tally (percentage breakdown of Yes/No/Maybe) updates in real time within 2 seconds and is visible to all group members. Changing a vote updates the tally immediately. | To Do |
| PB-008 | As a group member, I want to see a confirmed attendance list after an event so that I know who actually showed up. | Must | After an event date passes, the event proposer can mark each member as attended/not attended. A "Confirmed" list updates immediately and is visible to all group members. | To Do |
| PB-009 | As a user, I want the app to work on my phone and my laptop so that I can use it anywhere. | Must | Interface renders correctly on screens from 320px (mobile) to 1920px (desktop) with no broken layouts, cut-off text, or overlapping elements. | To Do |
| PB-010 | As a user, I want my group's data to be private from other groups so that our plans stay secure. | Must | A user in Group A cannot view or interact with Group B's events or attendance data without a valid invite code. | To Do |
| PB-011 | As a group member, I want to assign roles to attending members (e.g. "Food Bringer", "Ride Home") so that responsibilities are clear. | Nice | Role input accepts 3–50 characters of text. Pre-defined roles are available in a dropdown. Profanity in custom roles is blocked. Roles are displayed next to the member's name. | To Do |
| PB-012 | As a user, I want to see a map pin for the event location so that I know exactly where to go. | Nice | A single map marker displays based on the event's location string. | To Do |

---

## Changelog

| Date | Change | Reason |
|------|--------|--------|
| Week 4 | PB-001 to PB-010 added | Initial backlog created from Phase 1 functional and non-functional requirements |
| Week 5 | PB-011 added | "Assign Roles" identified as Nice to Have feature in requirements - as by client|
| Week 5 | PB-012 added | "Interactive Event Map" identified as Nice to Have feature in requirements - as by client|
