# AI-Patient-Case Collaboration System

AI-Patient-Case Collaboration System is a FastAPI-based collaboration platform for doctor-to-doctor case discussion, document sharing, and AI-assisted patient case analysis. The project now includes a real web frontend served directly by FastAPI, so the backend and UI can be run together with a single local workflow.

## Frontend Strategy

The frontend is intentionally implemented with FastAPI `templates/` and `static/` instead of introducing a separate SPA toolchain.

- It fits the current backend-first architecture.
- It keeps the local setup simple: one Python server, one port, same-origin API calls.
- It mirrors the lightweight structure and simplicity of the `lab9/LLM-Chatbot` reference repo.

## Features

- Login and signup pages backed by `/auth/login`, `/auth/signup`, and `/auth/me`
- Messenger-style case chat shell with sidebar, active thread, and case detail panel
- Searchable case list with last-message preview, patient code, timestamps, and document counts
- Real-time case chat using the existing websocket endpoint, with polling fallback
- Shared document list and upload flow using the existing document endpoints
- AI case helper panel backed by the existing `/ai/query` route
- Case creation modal using the existing `/cases` endpoint
- Responsive layout for desktop, tablet, and mobile

## Project Structure

```text
AI-Patient-Case-Collaboration-System/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── db.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── security.py
│   │   ├── ai/
│   │   ├── routers/
│   │   │   ├── auth.py
│   │   │   ├── cases.py
│   │   │   ├── chat.py
│   │   │   ├── documents.py
│   │   │   ├── ai.py
│   │   │   └── frontend.py
│   │   ├── static/
│   │   │   ├── css/styles.css
│   │   │   └── js/
│   │   │       ├── api.js
│   │   │       ├── app.js
│   │   │       ├── auth.js
│   │   │       ├── config.js
│   │   │       ├── storage.js
│   │   │       └── utils.js
│   │   └── templates/
│   │       ├── app.html
│   │       ├── base.html
│   │       ├── login.html
│   │       └── signup.html
│   └── requirements.txt
├── sql/
├── uploads/
├── testchat.html
└── README.md
```

## How To Run

### 1. Create and activate a virtual environment

```bash
python -m venv venv
source venv/bin/activate
```

On Windows:

```bash
venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r backend/requirements.txt
```

### 3. Configure environment variables

Set these values in the project root `.env` file:

```env
DATABASE_URL=mysql+aiomysql://<user>:<password>@<host>:3306/<db_name>
JWT_SECRET=<your_jwt_secret>
OPENAI_API_KEY=<optional_for_ai_features>
```

Optional:

```env
FRONTEND_API_BASE_URL=
```

`FRONTEND_API_BASE_URL` is not required for standard local development because the frontend is served by the same FastAPI app. Leave it blank unless you intentionally want the browser UI to target a different API origin.

### 4. Start the server

Run from the `backend/` directory:

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### 5. Open the app

- Frontend UI: [http://127.0.0.1:8000/app](http://127.0.0.1:8000/app)
- Login page: [http://127.0.0.1:8000/login](http://127.0.0.1:8000/login)
- Signup page: [http://127.0.0.1:8000/signup](http://127.0.0.1:8000/signup)
- Swagger docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## Frontend Notes

- Authentication state is stored in `localStorage` for local development convenience.
- Unauthenticated users visiting `/app` are redirected to `/login`.
- The UI uses the existing backend routes wherever possible and adds a small amount of read-only case metadata support for the sidebar and member panel.

## Useful API Flows

### Create example users

```json
{ "full_name": "Admin One", "email": "admin@test.com", "password": "admin123", "role": "admin" }
{ "full_name": "Dr. Alice", "email": "alice@test.com", "password": "alice123", "role": "doctor" }
```

### Create a case

```json
POST /cases
{ "patient_code": "P1001", "case_title": "Cardiology Review" }
```

### Add a member

```json
POST /cases/{case_id}/members
{ "user_id": 2, "member_role": "doctor" }
```

### Send a chat message

```json
POST /cases/{case_id}/messages
{ "content": "Patient is stable. Please review labs", "message_type": "text" }
```

### Trigger AI inside chat

```text
@ai summarize this report
```

## Real-Time Chat

The frontend connects to the existing websocket endpoint:

```text
/cases/ws/cases/{case_id}?token=<jwt>
```

If the websocket is unavailable, the UI falls back to periodic message polling for the active case.

## Existing Test Page

The original `testchat.html` is still present for low-level websocket testing if you want a minimal manual check outside the new frontend.
