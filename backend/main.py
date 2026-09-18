from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor
import jwt
import json

app = FastAPI(title="Darukaa Earth API")

# Allow your frontend to talk to this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Replace with your URI from the Supabase modal (insert your actual password)
DB_URI = "postgresql://postgres:YOUR_ACTUAL_PASSWORD@db.mrwdvoutpgipnfycsvdc.supabase.co:5432/postgres"
SECRET_KEY = "darukaa_secret_key"

def get_db():
    return psycopg2.connect(DB_URI, cursor_factory=RealDictCursor)

class UserAuth(BaseModel):
    email: str
    password: str

class ProjectCreate(BaseModel):
    name: str
    description: str

class SiteCreate(BaseModel):
    project_id: int
    name: str
    geometry: dict

# 1. Authentication
@app.post("/auth/register")
def register(user: UserAuth):
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO users (email, hashed_password) VALUES (%s, %s) RETURNING id;", (user.email, user.password))
        conn.commit()
        return {"message": "User registered successfully"}
    except Exception:
        conn.rollback()
        raise HTTPException(status_code=400, detail="Registration failed or email exists")

@app.post("/auth/login")
def login(user: UserAuth):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE email = %s AND hashed_password = %s;", (user.email, user.password))
    user_record = cur.fetchone()
    if not user_record:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = jwt.encode({"sub": user.email}, SECRET_KEY, algorithm="HS256")
    return {"access_token": token, "token_type": "bearer"}

# 2. Projects
@app.get("/projects")
def get_projects():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM projects ORDER BY id DESC;")
    return cur.fetchall()

@app.post("/projects")
def add_project(proj: ProjectCreate):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO projects (name, description) VALUES (%s, %s) RETURNING *;", (proj.name, proj.description))
    created = cur.fetchone()
    conn.commit()
    return created

# 3. Sites & Geospatial Polygons
@app.get("/projects/{project_id}/sites")
def get_sites(project_id: int):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, project_id, name, geometry FROM sites WHERE project_id = %s;", (project_id,))
    return cur.fetchall()

@app.post("/sites")
def add_site(site: SiteCreate):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO sites (project_id, name, geometry) VALUES (%s, %s, %s) RETURNING *;",
                (site.project_id, site.name, json.dumps(site.geometry)))
    created = cur.fetchone()
    conn.commit()
    return created

# 4. Analytics Data (Mocked for Charts)
@app.get("/sites/{site_id}/analytics")
def get_site_analytics(site_id: int):
    return {
        "site_id": site_id,
        "labels": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
        "carbon_tons": [120, 160, 200, 250, 310, 390],
        "biodiversity_score": [65, 68, 72, 75, 80, 84]
    }