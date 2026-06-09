# Huddle

Huddle is a Progressive Web App (PWA) that helps friend groups organise and commit to social plans. Users can propose activities, vote on them (Yes/No/Maybe), and track attendance - all without relying on messy group chats.

---
## Status
**Current Sprint:** Sprint 2 - Core Features ✅ Complete

**Last Increment:** Sprint 2 - Group creation/joining, event proposals, Yes/No/Maybe voting, map view, role assignment, and attendance tracking (PB-004 through PB-007)

**Next Planned Increment:** Sprint 3 - TBD
 
---
## Features
- User authentication with Google Authenticator 2FA
- Group creation and invite codes
- Event proposal system (name, date/time, location with map autofill)
- Yes/No/Maybe voting with live vote tallies
- Detailed event view with location map (Leaflet.js + OpenStreetMap)
- Role assignment by group leaders (custom roles, saved per group)
- Attendance tracking with per-member attendance percentage
## How to Run
1. Clone this repository to your local machine.
2. Open a terminal in the project root directory.
3. Install dependencies:
`npm install`
4. Start the development server:
`npm run dev`
5. Open your browser and navigate to `http://localhost:3000`
6. To use the full app, you will need Google Authenticator installed on your phone and linked to your test account.
> **Note:** An active internet connection is required for voting sync and authentication.
 
---
## Backlog Files
- [PRODUCTBACKLOG.md](./PRODUCTBACKLOG.md) - Full list of features, user stories, priorities, and acceptance criteria
- [SPRINTBACKLOG.md](./SPRINTBACKLOG.md) - Sprint-by-sprint goals, tasks, test results, reviews, and retrospectives
