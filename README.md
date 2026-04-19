# AI‑Patient‑Case Collaboration System - Backend

This backend powers the AI‑Patient‑Case Collaboration System, a platform designed for secure doctor‑to‑doctor collaboration and AI‑assisted patient case analysis. The current version includes a complete authentication pipeline built with FastAPI, async SQLAlchemy, and JWT tokens.

---

##  Features Implemented

- User signup with hashed passwords  
- User login with JWT token generation  
- JWT authentication using HTTP Bearer  
- `/auth/me` endpoint to fetch the current authenticated user  
- Async SQLAlchemy models (User)  
- Secure token decoding and validation  
- Multi user group chat using websockets with http endpoints 
- simple html page for testing the multi user
- document sharing (reports, images, PDFs)
- AI-powered question answering using embeddings (RAG)


This forms the foundation for protected doctor‑only features in the healthcare system.

---

## Project Structure

```
AI-Patient-Case-Collaboration-System/
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── db.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── security.py
│   │   ├── ai/
│   │   │     ├── ai.py
│   │   │     ├── document_processor.py
│   │   │     ├── chunking.py
│   │   │     ├── embeddings.py
│   │   │     └── faiss_store.py
│   │   ├── routers/
│   │   │     ├── auth.py
│   │   │     ├── cases.py
│   │   │     ├── chat.py
│   │   │     ├── documents.py
│   │   │     └── ai.py
│   │
│   ├── requirements.txt
│
├── uploads/
├── faiss_indexes/
└── README.md

```

---

##  How to Run the Project

### 1. Clone the repository
```bash
git clone <your-repo-url>
cd AI-Patient-Case-Collaboration-System
```

### 2. Create and activate a virtual environment
```
python -m venv venv
source venv/bin/activate   # Mac/Linux
venv\Scripts\activate      # Windows
```

### 3. Install dependencies
```
pip install -r backend/requirements.txt
```

### 4. Run the FastAPI server (from the backend directory)
```
cd backend
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000 
```


### 5. Open API Docs - to test the backend
```
http://127.0.0.1:8000/docs
```

### Backend Testing Flow (Auth → Cases → Chat)
This guide walks through the full backend workflow: authentication, case management, and real‑time chat.

### Step 1: Create Users
Admin
{ "full_name": "Admin One", "email": "admin@test.com", "password": "admin123", "role": "admin" }
Doctor
{ "full_name": "Dr. Alice", "email": "alice@test.com", "password": "alice123", "role": "doctor" }

### Step 2: Login
POST /auth/login
Copy the returned JWT token.

### Step 3: Authorize in Swagger
Click Authorize and paste:
Bearer YOUR_TOKEN_HERE

### Step 4: Create a Case Room
POST /cases
Body: { "patient_code": "P1001", "case_title": "Cardiology Review" }

### Step 5: Add Member to Case
POST /cases/{case_id}/members
Body: { "user_id": 2, "member_role": "doctor" }

### Step 6: Verify Case Access
As Admin
GET /cases
As Doctor
Login as doctor → Authorize → GET /cases

### Chat (REST API)
Send Message
POST /cases/{case_id}/messages
Body: { "content": "Patient is stable. Please review labs", "message_type": "text" }
Get Messages
GET /cases/{case_id}/messages

### Real-Time Chat (WebSocket)
### 1. Open the test HTML file
test_chat.html
### 2. Enter values
Token → paste JWT (without "Bearer")
Case ID → e.g., 3
### 3. Connect
Click Connect
You should see:
Connected
### 4. Send a message
Type a message → Send Message
### 5. Multi‑User Chat Test
Open two browser tabs:
Tab 1 → Admin login
Tab 2 → Doctor login
Connect both to the same case_id.
Send a message from one tab.
Both tabs should receive the message instantly.
### 6. AI Test : 
#### AI responds in chat, Answer is based on uploaded document, Case isolation maintained
```
@ai summarize this report
```
---

## Note:

### Update your `.env` file before running the server
- In `.env` file of the project root, add your database credentials and JWT settings:
  ```
  DATABASE_URL=mysql+aiomysql://<user>:<password>@<host>:3306/<db_name>
  JWT_SECRET=<your_jwt_secret>
  ```
- Replace `<user>`, `<password>`, `<host>`, and `<db_name>` with your actual MySQL details, and set a secure value for `JWT_SECRET`.
