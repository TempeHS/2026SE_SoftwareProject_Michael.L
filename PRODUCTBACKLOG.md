# Huddle - Product Backlog

## Vision

To make it easier for friend groups to organise and commit to social plans by providing a simple platform where users can propose activities, vote on them, and confirm attendance - without relying on messy group chats or inconsistent responses.

---

## Backlog Table

| ID | User Story | Priority | Acceptance Criteria | Sprint | Status |
|----|------------|----------|---------------------|--------|--------|
| PB-001 | As a user, I want to register an account with my email and password so that I can access Huddle. | Must | User can submit email + password; account is created and stored in the database. Duplicate emails are rejected. | Sprint 1 | Done |
| PB-002 | As a user, I want to set up Google Authenticator 2FA so that my account is secure. | Must | After registration, user is prompted to scan a QR code in Google Authenticator. A valid 6-digit TOTP code completes setup. | Sprint 1 | Done |
| PB-003 | As a user, I want to log in with my email, password, and 2FA code so that I can access my groups and events. | Must | User is authenticated and redirected to the dashboard within 3 seconds of entering a valid 2FA code. Invalid/expired codes are rejected with an error message. | Sprint 1 | Done |
| PB-004 | As a user, I want to create a new friend group so that I can invite my friends to plan together. | Must | A new group is created with a unique 6-character alphanumeric invite code. The group appears in the creator's group list. | Sprint 2 | Done |
| PB-005 | As a user, I want to join a group using an invite code so that I can participate in my friend group's plans. | Must | Entering a valid 6-character code adds the user to the group. The group appears in their group list and they are visible to the group creator. Invalid codes display a clear error message. | Sprint 2 | Done |
| PB-006 | As a group member, I want to propose an event with a name, date/time, and location so that my group can consider it. | Must | Event is saved with: name (max 30 chars), date/time (via picker), location (max 100 chars). Event appears in the group's event feed for all members. Inputs exceeding character limits are rejected. | Sprint 2 | Done |
| PB-007 | As a group member, I want to vote Yes, No, or Maybe on a proposed event so that the group can reach a decision. | Must | User can cast one vote per event. Vote tally (percentage breakdown of Yes/No/Maybe) is visible to all group members. Changing a vote updates the tally. Note: real-time auto-update (2s refresh) was descoped — tally updates on page load. | Sprint 2 | Done |
| PB-008 | As a group member, I want to see a confirmed attendance list after an event so that I know who actually showed up. | Must | After an event is closed, the group leader can mark each member as attended/not attended. Attendance percentage is calculated per member and displayed next to their name across all event views. | Sprint 2 | Done |
| PB-009 | As a user, I want the app to work on my phone and my laptop so that I can use it anywhere. | Must | Interface renders correctly on screens from 320px (mobile) to 2560px (desktop) with no broken layouts, cut-off text, or overlapping elements. Verified across 7 breakpoints. | Sprint 3 | Done |
| PB-010 | As a user, I want my group's data to be private from other groups so that our plans stay secure. | Must | A user in Group A cannot view or interact with Group B's events or attendance data without a valid invite code. | Sprint 1/2 | Done |
| PB-011 | As a group member, I want to assign roles to attending members (e.g. "Food Bringer", "Ride Home") so that responsibilities are clear. | Nice | Role input accepts custom text. Pre-defined roles available via dropdown. Custom roles are saved per group and reappear in future assignments. Roles displayed next to member's name. | Sprint 2 | Done |
| PB-012 | As a user, I want to see a map pin for the event location so that I know exactly where to go. | Nice | A Leaflet.js interactive map displays a marker at the event location, derived from address autofill input. Map is visible to all group members on the event detail screen. | Sprint 2 | Done |

---

## Changelog

| Date | Change | Reason |
|------|--------|--------|
| Week 4 | PB-001 to PB-010 added | Initial backlog created from Phase 1 functional and non-functional requirements |
| Week 5 | PB-011 added | "Assign Roles" identified as Nice to Have feature in requirements meeting — as requested by client |
| Week 5 | PB-012 added | "Interactive Event Map" identified as Nice to Have feature in requirements meeting — as requested by client |
| Sprint 1 (Week 5) | PB-001, PB-002, PB-003 marked Done | Sprint 1 completed and merged to main on 2026-05-20. All three items delivered. |
| Sprint 2 (Weeks 6–7) | PB-004, PB-005, PB-006, PB-007, PB-008, PB-011, PB-012 marked Done | Sprint 2 completed and merged to main on 2026-06-06. All committed items plus two client-requested extras (PB-011, PB-012) delivered. |
| Sprint 2 (Week 7) | PB-007 acceptance criteria updated — real-time auto-update descoped | Real-time vote refresh (2s auto-update) was attempted but formally marked out of scope. Vote tally updates on page load instead. Documented in diary Sprint 2, Day 7. |
| Sprint 3 (Weeks 7–8) | PB-009, PB-010 marked Done | Sprint 3 completed and merged to main on 2026-06-11. Responsive design verified across 7 breakpoints (320px–2560px). Group data isolation confirmed via invite code system. |
