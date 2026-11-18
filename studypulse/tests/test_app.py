import os, re, tempfile
os.environ["DB_PATH"] = os.path.join(tempfile.mkdtemp(), "t.db")
from app import app

def token(c, p): return re.search(r'name="_csrf" value="(\w+)"', c.get(p).get_data(as_text=True)).group(1)

def login(c):
    c.post("/register", data={"_csrf": token(c, "/register"), "email": "t@x.com", "password": "password1"})
    c.post("/login", data={"_csrf": token(c, "/login"), "email": "t@x.com", "password": "password1"})

def test_requires_login():
    assert app.test_client().get("/").status_code == 302

def test_csrf_blocks():
    assert app.test_client().post("/login", data={"email": "a", "password": "b"}).status_code == 400

def test_api_flow():
    c = app.test_client(); login(c)
    key = re.search(r"<code[^>]*>([^<]+)</code>", c.get("/").get_data(as_text=True)).group(1)
    h = {"X-API-Key": key}
    assert c.post("/api/predict", json={"study_hours": 4, "attendance": 85, "sleep_hours": 7, "previous_score": 70}, headers=h).json["predicted"] > 0
    assert c.post("/api/iot/sleep", json={"sleep_hours": 6.5}, headers=h).json["ok"]
    assert c.post("/api/predict", json={}, headers=h).status_code == 400
    assert c.post("/api/predict", json={}, headers={"X-API-Key": "bad"}).status_code == 401
    assert "predicted" in c.get("/export.csv").get_data(as_text=True)
