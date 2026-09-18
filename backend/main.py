import os
import json
from datetime import datetime, timedelta

import psycopg2
from psycopg2.extras import RealDictCursor
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import jwt
from passlib.context import CryptContext

app = FastAPI(title="Darukaa Earth API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Config from env
DB_URI = os.environ.get("DATABASE_URL", "postgresql://postgres:YOUR_ACTUAL_PASSWORD@db.example:5432/postgres")
SECRET_KEY = os.environ.get("SECRET_KEY", "darukaa_secret_key")
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_db():
    return psycopg2.connect(DB_URI, cursor_factory=RealDictCursor)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(subject: str, expires_delta: int = ACCESS_TOKEN_EXPIRE_MINUTES) -> str:
    to_encode = {"sub": subject, "exp": datetime.utcnow() + timedelta(minutes=expires_delta)}
    return jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")


def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except Exception:
        return None


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


# Auth endpoints
@app.post("/auth/register")
def register(user: UserAuth):
    conn = get_db()
    cur = conn.cursor()
    try:
        hashed = hash_password(user.password)
        cur.execute(
            "INSERT INTO users (email, hashed_password) VALUES (%s, %s) RETURNING id;",
            (user.email, hashed),
        )
        conn.commit()
        return {"message": "User registered successfully"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=f"Registration failed: {e}")


@app.post("/auth/login")
def login(user: UserAuth):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE email = %s;", (user.email,))
    user_record = cur.fetchone()
    if not user_record:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not verify_password(user.password, user_record["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_access_token(user.email)
    return {"access_token": token, "token_type": "bearer"}


# Helper to get current user from Authorization header
def get_current_user(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid auth scheme")
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    return payload["sub"]


# Projects
@app.get("/projects")
def get_projects():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM projects ORDER BY id DESC;")
    return cur.fetchall()


@app.post("/projects")
def add_project(proj: ProjectCreate, current_user: str = Depends(get_current_user)):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO projects (name, description, created_by) VALUES (%s, %s, %s) RETURNING *;",
        (proj.name, proj.description, current_user),
    )
    created = cur.fetchone()
    conn.commit()
    return created


# Sites & Geospatial Polygons
@app.get("/projects/{project_id}/sites")
def get_sites(project_id: int):
    conn = get_db()
    cur = conn.cursor()
    # Return geometry as stored (assumed GeoJSON in `geometry` json column)
    cur.execute(
        "SELECT id, project_id, name, geometry FROM sites WHERE project_id = %s;",
        (project_id,),
    )
    return cur.fetchall()


@app.get("/sites")
def get_all_sites():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, project_id, name, geometry FROM sites;")
    return cur.fetchall()


@app.post("/sites")
def add_site(site: SiteCreate, current_user: str = Depends(get_current_user)):
    conn = get_db()
    cur = conn.cursor()
    try:
        geom_json = json.dumps(site.geometry)
        cur.execute(
            "INSERT INTO sites (project_id, name, geometry, created_by) VALUES (%s, %s, %s, %s) RETURNING *;",
            (site.project_id, site.name, geom_json, current_user),
        )
        created = cur.fetchone()
        conn.commit()
        return created
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to create site: {e}")


# Analytics Data (Mocked for Charts)
@app.get("/sites/{site_id}/analytics")
def get_site_analytics(site_id: int):
    return {
        "site_id": site_id,
        "labels": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
        "carbon_tons": [120, 160, 200, 250, 310, 390],
        "biodiversity_score": [65, 68, 72, 75, 80, 84],
    }
