# Student Management System (Aim 3)

Full-stack CRUD app: **HTML/CSS/JavaScript** frontend (served with Node.js tooling) +
**Python Flask** REST API + **SQLite** database.

## Structure
```
student-management/
├── backend/
│   ├── app.py            # Flask API, validation, SQLite schema
│   ├── test_api.py       # 10 automated tests (functional + edge cases)
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── app.js            # Fetch API, client-side validation, dynamic rendering
└── package.json          # Node.js tooling (http-server)
```

## Run
**Terminal 1 – backend**
```
cd backend
pip install -r requirements.txt
python app.py              # http://127.0.0.1:5000  (creates students.db automatically)
```
**Terminal 2 – frontend**
```
npm install
npm start                  # http://127.0.0.1:3000
```
**Tests:** `cd backend && python -m unittest test_api -v`

## REST API
| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/students` | List all students |
| GET | `/api/students?q=text` | Search by name or roll number |
| GET | `/api/students/<id>` | Get one student |
| POST | `/api/students` | Add student (201; 400 invalid; 409 duplicate roll no) |
| PUT | `/api/students/<id>` | Update student (404 if missing) |
| DELETE | `/api/students/<id>` | Delete student (404 if missing) |

## Database schema (`students`)
`id` (PK) · `roll_no` (UNIQUE) · `name` · `class_name` · `marks` (CHECK 0–100) · `contact` · `email` · `created_at`

## Validation (client and server)
Required fields · unique roll number · name letters only · marks 0–100 ·
contact = 10-digit Indian mobile (starts 6–9) · optional email format.

## Edge cases covered
Searching a non-existent student (empty list + friendly message), updating/deleting a
non-existent record (404), duplicate roll number on add and edit (409), invalid contact/marks,
empty or malformed JSON body, backend offline (clear error toast).
