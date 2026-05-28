# MedVerify — Project Context (updated May 25 2026)

Thai hospital pharmacy medicine verification system.  
**Intern**: 67011638@kmitl.ac.th | **6 weeks left** (ends ~Jun 26)

---

## Stack

| Layer | Tech |
|-------|------|
| Backend | Python 3 + FastAPI, `uvicorn server:app` from `backend/` |
| Frontend | React + Tailwind CSS + Vite, `npm run dev` on port 3000 |
| Detection | YOLO OBB `best.pt` → zxingcpp QR → EasyOCR → YOLO vision `med_box.pt` |
| Fuzzy DB | `data/medicine_db.csv` (col: `name`), thresholds in `config.py` |
| QR DB | `Medicine_name_db.xlsx` (cols: `item`, `ชื่อยา`) |

---

## Frontend Architecture (current — fully restructured)

**No react-router-dom.** Single `currentPage` state in `App.jsx` drives all navigation.

### Layout
```
<Sidebar w-56 fixed left />         ← src/components/Sidebar.jsx
<div ml-56 flex flex-col>
  <header h-14 sticky topbar />
  <main overflow-y-auto>
    {currentPage === "dashboard" && <DashboardPage />}
    {currentPage === "scan"      && <ScanPage />}
    {currentPage === "history"   && <HistoryPage />}
    {currentPage === "master"    && <MasterDataPage />}
    {currentPage === "setup"     && <SetupPage />}
  </main>
</div>
<ResultPopup />       ← rendered outside page flow
<HistoryDetailPopup />
```

### Sidebar nav structure (`src/components/Sidebar.jsx`)
- Logo: `medsure.jpg` asset top-left
- Section (none): Dashboard
- Section VERIFY: Scan, History (shows blue badge with history count)
- Section MANAGE: Master Data, Setup
- Active item: `border-l-2 border-blue-600 bg-blue-50 text-blue-600`
- Footer: "MedVerify v3.0 · Drug Verification System"

### Pages

**`src/pages/ScanPage.jsx`**
- Layout: `p-6 flex flex-col gap-5` (full width, no max-w constraint)
- Order: page header → `<ExpectedMedicines />` → `<CameraSection />` → Complete button → `<HowToUse />`
- Complete button only shows when `expected.length > 0 || scanResults.length > 0`
- Note: a linter added `<div className="max-w-3x1">` around CameraSection (typo: "3x1" not "3xl" — has no effect, but it's there)

**`src/pages/HistoryPage.jsx`**
- Stats row: Scans Today, All Passed, Had Errors, Medicines Matched (today only)
- Search input + filter tabs: All / Passed / Partial / Failed
- Table: #, Date/Time, Summary, Matched, Missing, Extra, Unknown, Status, View
- Paginated 10/page with prev/next + numbered pages + ellipsis
- Click row or "View" → opens `<HistoryDetailPopup>`
- Status logic: `missing > 0` = error (red); `extra/unknown/review > 0` = partial (amber); else = ok (green)

**`src/pages/DashboardPage.jsx`**
- 4 stat cards: Total Scans Today, All Passed, Had Errors, Accuracy
- Recent activity list (last 8 items): dot, summary, timestamp, matched/missing/extra counts, status badge
- Quick action cards: Start Scanning → scan, View History → history, Master Data → master
- "New Scan" button in header navigates to scan

**`src/pages/MasterDataPage.jsx`**
- Tabs: Drug Database 💊, Users 👤, Roles 🛡️
- Drug tab: search + status filter (all/active/inactive) + Add Drug button + table with Edit/Deactivate per row
- Currently uses `SAMPLE_DRUGS` mock array (7 drugs) — **needs real API**
- Users tab: "Coming soon" placeholder
- Roles tab: hardcoded Administrator / Pharmacist / Viewer with permission checkmarks

**`src/pages/SetupPage.jsx`**
- Tabs: General ⚙️, Camera 📷, Database 🗄️
- General: Auto Logout (idle secs, warn secs, toggle), Hospital Name + Code
- Camera: 2 cameras, each with Device ID, Resolution dropdown, FPS
- Database: Host, Port, DB Name, Username, Password + "Test Connection" button (animated)
- Save button: turns green "Saved" for 2.5s

### Key Components
- **`src/components/ExpectedMedicines.jsx`**: Input row (name + qty + Add + Import .txt F9 + Clear F10) → when list not empty: medicine list (max-h-48 scroll) side-by-side with 2×2 summary grid (Matched/Missing/Extra/Unknown)
- **`src/components/CameraSection.jsx`**: Camera feeds, Scan button (F4), annotated image output
- **`src/components/ResultPopup.jsx`**: Post-scan popup: Continue Scan vs Close & Review
- **`src/components/HistoryDetailPopup.jsx`**: Full detail view of a history item (file: `Historydetailpopup.jsx`)

### App.jsx State (all scan state lives here)
```js
currentPage       // navigation
scanResults       // array | null
summary           // { matched, missing, extra, review, unknown }
expected          // [{ name: string, quantity: number }]
isScanning        // bool
annotatedImg      // base64 string | null
showPopup         // bool
popupData         // { success, missing[], extra[], review[], unknown[], summary, rawData }
history           // array, max 50, in-memory only
historyDetail     // item | null (currently unused in App — HistoryPage manages its own detail)
sessionResults    // useRef([])
sessionStart      // useRef(null)
sessionAnnotated  // useRef(null)
```

### Keyboard shortcuts
- F4 — Scan (handled in CameraSection)
- F5 — Complete & Save (handled in App.jsx)
- F9 — Import .txt (handled in ExpectedMedicines)
- F10 — Clear all (handled in ExpectedMedicines)

---

## Backend Architecture

### Pipeline (4 layers)
1. **Layer 1 — YOLO OBB** (`best.pt`): Detects bounding boxes on stitched frame. `imgsz=1920`.  
2. **Layer 2 — QR** (`zxingcpp`): Reads QR/barcode from L1 crop. Always wins if found.  
3. **Layer 3 — OCR** (`EasyOCR`, `['en', 'th']`): Reads text from L1 crop. Fuzzy matches against `medicine_db.csv`.  
4. **Layer 4 — YOLO Vision** (`med_box.pt`): Visual classification. Only runs if no QR AND OCR < HIGH threshold.

### Stitching (`server.py`)
- cam0: ROTATE_90_COUNTERCLOCKWISE (-90°)
- cam1: ROTATE_90_CLOCKWISE (+90°)
- `hconcat` → output: **2160×1920** (stale comment in code says "3840×1080" — wrong, ignore it)
- All 4 layers operate on this single stitched frame

### Trust Hierarchy (`consensus.py`)
1. QR/Barcode → HIGH (always wins)
2. OCR DB score ≥ 92 → HIGH
3. OCR < 92 + L4 found → HIGH/MEDIUM/LOW by L4 DB score
4. OCR 88–91, no L4 → MEDIUM / PENDING_REVIEW
5. OCR not in DB + no L4 → UNKNOWN
6. All failed → UNKNOWN

### Config thresholds (`config.py`)
```python
DB_HIGH_THRESHOLD = 92.0
DB_LOW_THRESHOLD  = 88.0
L4_CONF_MIN       = 0.45   # raise to 0.65 after retraining with 20 classes
L4_CONF_RUN       = 0.25
L1_CONF_QR        = 0.50
L1_CONF_OTHER     = 0.4    # open question: verify if 0.70 is better
L1_PAD_QR         = 40
L1_PAD_OTHER      = 10
```

### Key Bug Fixed (layer3_ocr.py)
`correct_orientation()` previously returned `(best_crop, best_texts)`.  
Caller unpacked as `(best_score, texts)` → `best_score` held the image array → `_to_float(ndarray)` read first pixel value ≈ **244** (the persistent score bug).

**Fix**: `correct_orientation()` now returns `(best_crop, best_score, best_texts)` (3-tuple).  
Caller: `best_crop, best_score, texts = correct_orientation(crop, medicine_db)`

Also: OCR fallback score capped at 5.0 to prevent sum-of-confidences overflow:
```python
fallback = min(sum(_to_float(c) for _, _, c in results if _to_float(c) > OCR_CONF_KEEP) * 0.1, 5.0)
```

### Camera notes
- cam1 opens first, cam0 opens 1s later (cam0 needs last slot on USB hub for full 1920×1080)
- Frontend sends PNG frames (not JPEG) — critical for deterministic QR decode

---

## Session accumulation logic (App.jsx)
- `useRef` (not state) to avoid re-renders during multi-scan
- Each box: `session_box_id = "${scanStamp}-${box_id}"` prevents collisions
- MATCHED/EXTRA re-derived after each scan append
- MISSING = one entry per missing unit (3 missing Sefloc = 3 rows)

---

## Current YOLO Training Status
- `med_box.pt`: 7 classes, ~200 imgs/class
- Target: 20 classes
- Known confusion: Pregabalin Sandoz 75 ↔ Bilastine 20 (similar blue chevron back face)

---

## What's Done vs Still Needed

### ✅ Done
- Full 4-layer detection pipeline running
- Dual-camera stitching + coordinate system
- QR decode working
- OCR fuzzy match with DB
- L4 YOLO vision (7 classes)
- Frontend sidebar navigation (Dashboard, Scan, History, Master Data, Setup)
- Scan page: expected medicines + camera feed + result popup
- History page: searchable/filterable table with pagination
- Dashboard page: stats + recent activity
- Session accumulation across multiple scans
- Multi-unit quantity tracking (MATCHED/EXTRA/MISSING per unit)
- layer3=244 score bug fixed

### ❌ Still Needed (for full system per design doc)
- **Login / Authentication** (JWT, role-based: Admin / Pharmacist / Viewer)
- **PostgreSQL database** (persistent history, medicine DB, users)
- **Master Data real API** (currently mock SAMPLE_DRUGS)
- **Prescription integration** (load expected list from HIS/prescription system)
- **Export to Excel** (history page)
- **Persistent history** (currently in-memory, lost on refresh)
- **More YOLO classes** (20 target, currently 7)
- **Retrain at imgsz=1280** for final deployment
- **Hospital-scale testing** (50+ scans)
- **Remove all debug prints** from backend

---

## 6-Week Plan (May 18 – Jun 26)
| Week | Dates | Focus |
|------|-------|-------|
| 1 | May 18–23 | Fix & stabilise — **DONE** |
| 2 | May 26–30 | Data collection sprint 1 (Pregabalin, Prenolol, 3-4 new meds) |
| 3 | Jun 2–6 | Data sprint 2 + retrain at imgsz=640, 12-13 classes |
| 4 | Jun 9–13 | Final data collection + UI polish (all 20 classes) |
| 5 | Jun 16–20 | Final retrain imgsz=1280, hospital testing 50+ scans |
| 6 | Jun 23–26 | Bug fixes, remove debug prints, final submission |

---

## File Map (key files)
```
backend/
  server.py              — FastAPI app, scan endpoint, stitching
  pipeline/
    layer3_ocr.py        — EasyOCR + correct_orientation (3-tuple return — fixed)
    layer4_vision.py     — YOLO vision, two-pass scan
    consensus.py         — trust hierarchy, final_name resolution
  config.py              — ALL thresholds (never hardcode elsewhere)
  data/
    medicine_db.csv      — fuzzy match DB (col: name)
    Medicine_name_db.xlsx — QR lookup (cols: item, ชื่อยา)

frontend/src/
  App.jsx                — all state, navigation, scan logic
  components/
    Sidebar.jsx          — fixed left nav
    CameraSection.jsx    — camera feeds + scan button
    ExpectedMedicines.jsx — expected list + summary tiles
    ResultPopup.jsx      — post-scan popup
    Historydetailpopup.jsx — history item detail modal
    HowtoUse.jsx         — keyboard shortcut guide
  pages/
    ScanPage.jsx         — full-width scan layout
    HistoryPage.jsx      — searchable history table
    DashboardPage.jsx    — stats + recent activity
    MasterDataPage.jsx   — drug/user/role management (mock data)
    SetupPage.jsx        — system configuration
  api/index.js           — API call helpers
  hooks/useCamera.js     — camera stream hook
```
