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

This forms the foundation for protected doctor‑only features in the healthcare system.

---

## Project Structure

```
AI-Patient-Case-Collaboration-System/
│
├── app/
│   ├── main.py
│   ├── db.py
│   ├── models.py
│   ├── security.py
│   ├── routers/
│   │     └── auth.py
│   └── schemas.py
│
├── requirements.txt
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

---

## Note:

### Update your `.env` file before running the server
- In `.env` file of the project root, add your database credentials and JWT settings:
  ```
  DATABASE_URL=mysql+aiomysql://<user>:<password>@<host>:3306/<db_name>
  JWT_SECRET=<your_jwt_secret>
  ```
- Replace `<user>`, `<password>`, `<host>`, and `<db_name>` with your actual MySQL details, and set a secure value for `JWT_SECRET`.
