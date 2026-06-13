# Huddle
Huddle is a Progressive Web App (PWA) that helps friend groups organise and commit to social plans. Users can propose activities, vote on them (Yes/No/Maybe), and track attendance - all without relying on messy group chats.

---

## Status
**Current Sprint:** Sprint 3 - PWA Responsiveness & UI/UX Design ✅ Complete  
**Last Increment:** Sprint 3 - Fully responsive layout (320px–2560px), unified frontend theme across all pages, cross-platform breakpoint testing (PB-009)  
**Next Planned Increment:** Sprint 4 - Documentation (finalise Systems Report, Client Log, Developer Diary)

---

## Features
- User authentication with Google Authenticator 2FA
- Group creation with unique 6-character invite codes
- Event proposal system (name, date/time, location with address autofill)
- Yes/No/Maybe voting with vote tallies and percentage breakdown
- Detailed event view with interactive location map (Leaflet.js + OpenStreetMap)
- Role assignment by group leaders (custom roles, saved per group)
- Attendance tracking with per-member attendance percentage
- Fully responsive UI from 320px (mobile) to 2560px (desktop)

---

## How to Run
1. Clone this repository to your local machine.
2. Open a terminal in the project root directory.
3. Install dependancies:
   `pip install -r requirements.txt`
4. Set up your environment variables - copy `.env` and fill in your secret key and database config.
5. Run the app:
   `python main.py`
6. Open your browser and navigate to `http://localhost:5000`
7. To use 2FA, you will need Google Authenticator installed on your phone. Scan the QR code shown on registration.

---

## Backlog Files
- [PRODUCTBACKLOG.md](./PRODUCTBACKLOG.md) - Full list of features, user stories, priorities, and acceptance criteria
- [SPRINTBACKLOG.md](./SPRINTBACKLOG.md) - Sprint-by-sprint goals, tasks, test results, reviews, and retrospectives
