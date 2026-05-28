# MedVerify v3 — Session Handoff

> Generated: 2026-05-28
> Project root: C:\Users\pasul\Desktop\InternStuff\v3_webapp

---

## 1. Project Overview

**MedCheckPro / MedVerify** — A pharmacy medicine verification system built for a Thai hospital internship project. A pharmacist places a bag of medicines under a dual-camera rig, the system scans and identifies each medicine, then compares the result against an expected prescription list.

### Tech Stack
| Layer | Technology |
|---|---|
| Frontend | React + Vite + Tailwind CSS |
| Backend | Python FastAPI |
| Camera | OpenCV (dual USB cameras via DirectShow/CAP_DSHOW) |
| Detection | YOLO OBB (Layer 1), QR decode (Layer 2), Tesseract OCR (Layer 3), YOLO Vision (Layer 4) |
| Drug DB | CSV file (backend/data/medicine_db.csv) — no real database yet |
| History | React useState in memory — lost on every page refresh |
| Auth | Hardcoded admin / 1234 in LoginPage.jsx — not real |

### How to run
```
# Backend
cd backend && uvicorn server:app --reload

# Frontend
cd frontend && npm run dev
```

---

## 2. Key File Structure

### Backend
```
backend/
├── server.py               # FastAPI app — all REST endpoints
├── camera.py               # Dual-camera capture, stitching, brightness equalization
├── config.py               # App config (camera indices, paths, thresholds)
├── pipeline/
│   ├── layer1_detect.py    # YOLO OBB detection + perspective warp (straightens crops)
│   ├── layer2_qr.py        # QR code decode
│   ├── layer3_ocr.py       # Tesseract OCR on text label
│   ├── layer4_vision.py    # YOLO visual classifier (fallback)
│   └── consensus.py        # Merges layer 2/3/4 results into final_name
├── utils/
│   ├── image.py            # get_perspective() — perspective transform, crop straightening
│   ├── medicine_db.py      # CSV read helpers used by pipeline
│   └── font.py             # Thai font rendering for annotated output
└── data/
    ├── medicine_db.csv     # Drug name list (one name per row, header: "name")
    ├── medicine_images/    # Reference images per drug (used by Layer 4)
    └── homography.npy      # Camera homography calibration matrix
```

### Frontend
```
frontend/src/
├── App.jsx                 # Root: auth gate, all state (history, scan, expected), nav
├── api/index.js            # All fetch() calls to backend API
├── pages/
│   ├── LoginPage.jsx       # Login form (hardcoded admin/1234)
│   ├── ScanPage.jsx        # Main scan UI — camera feed, expected list, results table
│   ├── HistoryPage.jsx     # Scan history table with search/filter/pagination
│   ├── DashboardPage.jsx   # Stats overview (today is scans, pass rate, etc.)
│   ├── MasterDataPage.jsx  # Drug database CRUD + (placeholder) User/Role management
│   └── SetupPage.jsx       # Camera resolution, calibration, brightness setup
├── components/
│   ├── Sidebar.jsx         # Fixed left nav with page links + sign out
│   ├── ResultPopup.jsx     # Modal shown after each scan with matched/missing/extra
│   ├── Historydetailpopup.jsx  # Modal for viewing a past scan full detail
│   ├── CameraSection.jsx   # Live MJPEG camera feed component
│   ├── ExpectedMedicines.jsx   # Expected medicine list management on ScanPage
│   └── HowtoUse.jsx        # Help guide component
└── utils/
    └── calibration.json    # Shared calibration (read by both frontend and backend)
```

---

## 3. What Was Completed This Session

### UI / Frontend
- **Login page Enter-key navigation** — pressing Enter in username field moves focus to password field (useRef + onKeyDown). This fix was lost once due to linter revert and had to be re-applied — see gotchas.
- **History page color swap** — Missing is now red (text-red-500), Extra is now amber (text-amber-500)
- **History page Scanned By column** — replaced Summary column with username who performed the scan (avatar icon + username), pulled from user?.username in App.jsx
- **MasterData drug CRUD** — Add, Edit, Remove buttons now have real functionality via an inline modal; calls real backend API endpoints
- **API functions** — addDrug, updateDrug, deleteDrug properly implemented in api/index.js (replaced empty stubs)
- **History detail popup color swap** — Historydetailpopup.jsx STATUS_CONFIG updated so Missing = amber, Extra = red throughout (summary bar, section headers, row backgrounds)

### Backend
- **Drug CRUD endpoints** — Replaced 3 broken GET placeholder stubs in server.py with real POST /drug-database, PUT /drug-database/{id}, DELETE /drug-database/{id} endpoints
- **CSV helpers** — _read_drug_names(), _write_drug_names(), _names_to_response() added to server.py
- **Camera autofocus lock** — Added cap.set(cv2.CAP_PROP_AUTOFOCUS, 0) to both _open_master() and _open_slave() in camera.py

---

## 4. Current State

### Working
- Full 4-layer scan pipeline (YOLO -> QR -> OCR -> Vision)
- Dual camera stitching with brightness equalization offset
- Live MJPEG camera feed in browser
- Expected medicine list management (add/remove/quantity)
- Scan result popup with matched/missing/extra/unknown breakdown
- History table (in-memory only — lost on refresh)
- Drug database CRUD (Add/Edit/Remove against CSV file)
- Perspective/straightening calibration on detected crops (Layer 1)
- Camera resolution and calibration setup page

### Known Issues / Broken
- **History is not persistent** — stored only in React useState, wiped on page refresh or backend restart
- **Auth is fake** — admin / 1234 hardcoded in LoginPage.jsx, no backend validation
- **Camera autofocus fix not yet committed** — fix was applied this session but camera.py is uncommitted. Commit immediately or it will be lost.
- **Ambient light sensitivity** — internal lighting (~40-50 mean) too weak vs office lights (120+ mean). Software offset partially compensates but hardware lighting needs improvement.
- **Dashboard stats are static/placeholder** — not pulling real data
- **Auto-logout logic** — UI exists but idle timer not wired up
- **User management / Role management in MasterData** — Coming soon placeholders only

---

## 5. Active Decisions

### Drug IDs are 1-based CSV row indices
No real primary key. Backend uses row number (1-based) as the id. Fragile — deleting row 3 shifts row 4 to row 3. Frontend always re-fetches after mutations so UI stays in sync. Must be replaced when moving to SQL.

### Color convention: Missing = red, Extra = amber
Missing medicine is clinically more dangerous, so it gets the more alarming red. This was explicitly swapped from the original implementation which had the colors backwards.

### History capped at 50 entries in memory
setHistory(prev => [...].slice(0, 50)) — oldest entries silently dropped. Arbitrary limit that only exists because there is no real persistence yet.

### SQLite chosen over PostgreSQL for next phase
Single-workstation internship project. SQLite means no server to install, file-based, full SQL, Python built-in. No access to hospital production database is needed — project is fully self-contained. Can migrate to PostgreSQL later if multi-station deployment is required.

### History scanned_by field
App.jsx injects user?.username into every history entry at save time. Currently always "admin" since auth is hardcoded.

---

## 6. Next Steps (Priority Order)

### IMMEDIATE — commit the autofocus fix before anything else
```
git add backend/camera.py
git commit -m "Lock autofocus on both cameras at open"
```

### HIGH — SQLite Phase 1: replace drug CSV with a real database
Low risk. Drug endpoints already have the right shape — just swap CSV helpers for SQL queries.

Files to change:
- backend/server.py — replace _read_drug_names/_write_drug_names with sqlite3 queries
- Add backend/database.py — DB init, connection, table definitions
- One-time migration: read CSV rows -> INSERT INTO drugs

Schema:
```sql
CREATE TABLE drugs (
  id    INTEGER PRIMARY KEY AUTOINCREMENT,
  name  TEXT NOT NULL UNIQUE COLLATE NOCASE
);
```

### HIGH — SQLite Phase 2: persistent scan history
Backend: add scan_sessions + scan_results tables. New endpoints: POST /history, GET /history.
Frontend: App.jsx handleCloseAndReview and handleComplete must await saveHistory(entry).
On mount, useEffect fetches GET /history to populate state instead of starting empty.

Schema:
```sql
CREATE TABLE scan_sessions (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  timestamp  TEXT NOT NULL,
  scanned_by TEXT,
  matched    INTEGER DEFAULT 0,
  missing    INTEGER DEFAULT 0,
  extra      INTEGER DEFAULT 0,
  review     INTEGER DEFAULT 0,
  unknown    INTEGER DEFAULT 0,
  annotated  TEXT
);
CREATE TABLE scan_results (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  session_id  INTEGER REFERENCES scan_sessions(id),
  box_id      TEXT,
  final_name  TEXT,
  scan_status TEXT,
  confidence  TEXT,
  ocr_raw     TEXT,
  qr_name     TEXT
);
```

### MEDIUM — Real authentication
Add users table with bcrypt hashed passwords. POST /auth/login returns JWT. Frontend stores token in localStorage, sends as Authorization: Bearer header. Backend validates on protected routes.

### LOW — remaining features
- History export to Excel (.xlsx download)
- Dashboard real stats from DB
- Auto-logout idle timer (UI exists, logic not wired)
- Batch number / expiry date extraction from OCR
- Stronger internal camera lighting (hardware)

---

## 7. Important Context & Gotchas

### Uncommitted edits get lost — this has happened multiple times
When Claude edits a file in a chat session, it is written to disk but NOT committed to git. The next time that file is edited in a new session it can be overwritten with no recovery. Always commit after any fix you want to keep.

Currently uncommitted important changes (run git status to verify):
- backend/camera.py — autofocus lock fix
- backend/server.py — real drug CRUD endpoints
- frontend/src/App.jsx — scanned_by field in history entries
- frontend/src/api/index.js — real addDrug/updateDrug/deleteDrug
- frontend/src/components/Historydetailpopup.jsx — color swap
- frontend/src/pages/HistoryPage.jsx — color swap + Scanned By column
- frontend/src/pages/LoginPage.jsx — Enter key navigation
- frontend/src/pages/MasterDataPage.jsx — modal CRUD UI

### Camera autofocus DirectShow caveat
Some webcam drivers on Windows silently ignore CAP_PROP_AUTOFOCUS. If the camera still autofocuses after the fix, pin the focus value explicitly:
```python
cap.set(cv2.CAP_PROP_AUTOFOCUS, 0)
cap.set(cv2.CAP_PROP_FOCUS, cap.get(cv2.CAP_PROP_FOCUS))  # pin at current value
```

### Drug IDs shift on delete (CSV limitation)
PUT /drug-database/{id} and DELETE /drug-database/{id} use 1-based row index as ID. Deleting row 3 makes old row 4 become row 3. Safe only because frontend re-fetches the full list after every mutation. Fixed when SQLite AUTOINCREMENT IDs are introduced.

### calibration.json is shared between frontend and backend
frontend/src/utils/calibration.json is read by both React (for display) and backend/camera.py (for stitch parameters, polled every 2 seconds). Do not move this file.

### History scanned_by always shows "admin" until real auth is built
App.jsx reads user?.username from login state. Since login is hardcoded to admin/1234, it will always show "admin" until JWT auth is implemented.

### No hospital database access needed
This project does not connect to the hospital systems at all. All data is self-contained. A local SQLite file is the correct approach for the internship deliverable. Hospital IT integration is out of scope until formal deployment.
