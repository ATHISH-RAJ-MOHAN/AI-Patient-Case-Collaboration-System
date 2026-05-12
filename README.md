# AI-Patient-Case Collaboration System

AI-Patient-Case Collaboration System is a FastAPI-based collaboration platform for doctor-to-doctor case discussion, document sharing, and AI-assisted patient case analysis. The project includes a real web frontend served directly by FastAPI, so the backend and UI run together with a single local workflow. It also includes an Android Trusted Web Activity (TWA) wrapper for mobile use.

---

## Features

* Login and signup pages backed by `/auth/login`, `/auth/signup`, and `/auth/me`
* Messenger-style case chat shell with sidebar, active thread, and case detail panel
* Searchable case list with last-message preview, patient code, timestamps, and document counts
* Real-time case chat using the existing websocket endpoint, with polling fallback
* Shared document list and upload flow using the existing document endpoints
* AI case helper panel backed by the existing `/ai/query` route
* Case creation modal using the existing `/cases` endpoint
* Responsive layout for desktop, tablet, and mobile
* Android app wrapper using Trusted Web Activity

---

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
├── mobile_app/
├── sql/
├── uploads/
└── README.md
```

---

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

---

### 2. Install dependencies

```bash
pip install -r backend/requirements.txt
```

---

### 3. Configure environment variables

Create a `.env` file in the project root:

```env
DATABASE_URL=mysql+aiomysql://<user>:<password>@<host>:3306/<db_name>
JWT_SECRET=<your_jwt_secret>
OPENAI_API_KEY=<optional_for_ai_features>
```

---

### 4. Set up the database

Ensure MySQL is running.

Run the SQL setup files in order:

```bash
mysql -u <user> -p < sql/setup.sql
mysql -u <user> -p groupchat < sql/schema.sql
```
* setup.sql → creates database and user
* schema.sql → creates tables and schema

Make sure your .env file matches the database credentials created in setup.sql.

---

### 5. Start the server

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

---

### 5. Open the app

* Frontend UI: [http://127.0.0.1:8000/app](http://127.0.0.1:8000/app)
* Login page: [http://127.0.0.1:8000/login](http://127.0.0.1:8000/login)
* Signup page: [http://127.0.0.1:8000/signup](http://127.0.0.1:8000/signup)
* Swagger docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## Frontend Notes

* Authentication state is stored in `localStorage` for local development convenience.
* Unauthenticated users visiting `/app` are redirected to `/login`.
* The UI uses existing backend routes and adds minimal enhancements for usability.

---

## Android App

The Android project uses Trusted Web Activity (TWA) to wrap the hosted web app.

---

### 1. Open the Android project

Open the project in Android Studio:

```text
android/mobile_app
```

---

### 2. Set the web app URL

Update:

```xml
res/values/strings.xml
```

Set:

```xml
<string name="defaultUrl">https://YOUR_DOMAIN/app</string>
```

---

### 3. Update AndroidManifest.xml

Open:

```text
android/mobile_app/app/src/main/AndroidManifest.xml
```

Update the `<data>` tag:

```xml
<data
    android:scheme="https"
    android:host="YOUR_DOMAIN" />
```

#### Example (ngrok):

```xml
<data
    android:scheme="https"
    android:host="abcd1234.ngrok-free.dev" />
```

**Important:**

* Do NOT include `https://`
* Do NOT include `/app`
* Only include the domain name

---

### 4. Using ngrok (for local development)

Start ngrok:

```bash
ngrok http 8000
```

Example output:

```text
https://abcd1234.ngrok-free.dev
```

Update:

```xml
<string name="defaultUrl">https://abcd1234.ngrok-free.dev/app</string>
```

---

### 5. Update Digital Asset Links

In `strings.xml`:

```xml
"site": "https://abcd1234.ngrok-free.dev"
```

---

### 6. Build and run

* Connect a device or emulator
* Click **Run** in Android Studio

---

### 7. Full TWA experience

For full-screen mode, host:

```text
/.well-known/assetlinks.json
```

Must match:

* package name
* SHA-256 fingerprint
* domain

---

### Notes

* ngrok URLs change every run
* Update:

  * `strings.xml`
  * `AndroidManifest.xml`
  * then rebuild the app
* Backend must be running before launching the app
* Use a stable domain for production

---

## Useful Backend API Flows

### Create users

```json
{ "full_name": "Admin One", "email": "admin@test.com", "password": "admin123", "role": "admin" }
{ "full_name": "Dr. Alice", "email": "alice@test.com", "password": "alice123", "role": "doctor" }
```

---

### Create a case

```json
POST /cases
{ "patient_code": "P1001", "case_title": "Cardiology Review" }
```

---

### Add a member

```json
POST /cases/{case_id}/members
{ "user_id": 2, "member_role": "doctor" }
```

---

### Send a message

```json
POST /cases/{case_id}/messages
{ "content": "Patient is stable. Please review labs", "message_type": "text" }
```

---

### Upload a document

```json
POST /documents/upload
```

---

### Trigger AI

```text
@ai summarize this report
```

---

## Real-Time Chat

WebSocket endpoint:

```text
/cases/ws/cases/{case_id}?token=<jwt>
```

Fallback: polling if WebSocket fails.

---

## Android and Hosting Notes

* Web app and Android app must use the same HTTPS domain
* If domain changes, update `defaultUrl` and rebuild
* Avoid hardcoding ngrok URLs
* Use a stable deployment for production

---
## Team Members

- Athish Raj Mohan
- Aadarsh Sudhir Ghiya
- Neil Bai
---
