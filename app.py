import os, secrets, sqlite3
from functools import wraps
import joblib, pandas as pd
from flask import Flask, g, jsonify, redirect, render_template, request, session, url_for, flash, abort
from werkzeug.security import check_password_hash, generate_password_hash
from model import FEATURES, train

app = Flask(__name__)
app.config.update(SECRET_KEY=os.environ.get("SECRET_KEY", "dev-change-me"),
                  SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax")
DB, MODEL_PATH = os.environ.get("DB_PATH", "studypulse.db"), "model.joblib"
LIMITS = {"study_hours": (0, 16), "attendance": (0, 100), "sleep_hours": (0, 16), "previous_score": (0, 100)}

# ---------- Database (DBMS) ----------
def db():
    if "db" not in g:
        g.db = sqlite3.connect(DB); g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(_):
    d = g.pop("db", None)
    if d: d.close()

def init_db():
    with sqlite3.connect(DB) as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, email TEXT UNIQUE NOT NULL, pw TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS predictions(id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL,
          study_hours REAL, attendance REAL, sleep_hours REAL, previous_score REAL, predicted REAL,
          created TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(user_id) REFERENCES users(id));""")

# ---------- Security ----------
def login_required(f):
    @wraps(f)
    def w(*a, **k):
        return f(*a, **k) if "uid" in session else redirect(url_for("login"))
    return w

@app.before_request
def csrf_protect():
    if request.method == "POST" and request.form.get("_csrf") != session.get("_csrf"):
        abort(400, "Bad CSRF token")

@app.context_processor
def inject_csrf():
    session.setdefault("_csrf", secrets.token_hex(16))
    return {"csrf": session["_csrf"]}

@app.after_request
def headers(r):
    r.headers["X-Content-Type-Options"] = "nosniff"; r.headers["X-Frame-Options"] = "DENY"
    return r

# ---------- AI / GenAI ----------
_model = None
def model():
    global _model
    if _model is None:
        _model = joblib.load(MODEL_PATH) if os.path.exists(MODEL_PATH) else train(MODEL_PATH)[0]
    return _model

def study_tip(d, pred):
    """GenAI tip via Claude if ANTHROPIC_API_KEY is set; otherwise rule-based fallback."""
    if os.environ.get("ANTHROPIC_API_KEY"):
        try:
            import anthropic
            msg = anthropic.Anthropic().messages.create(
                model="claude-haiku-5-5", max_tokens=150,
                messages=[{"role": "user", "content": f"Student habits: {d}. Predicted score {pred:.0f}/100. "
                           "Give 2 short, practical, encouraging study tips."}])
            return msg.content[0].text
        except Exception:
            pass
    tips = []
    if d["sleep_hours"] < 6.5: tips.append("Aim for 7-8 hours of sleep; memory consolidation depends on it.")
    if d["attendance"] < 75: tips.append("Raise attendance above 75%; it is one of the strongest predictors here.")
    if d["study_hours"] < 2: tips.append("Try 2 focused hours a day in 25-minute Pomodoro blocks.")
    return " ".join(tips) or "Great habits. Keep your routine consistent and review weekly."

# ---------- Routes ----------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email, pw = request.form["email"].strip().lower(), request.form["password"]
        if "@" not in email or len(pw) < 8:
            flash("Valid email and a password of 8+ characters required.")
        else:
            try:
                db().execute("INSERT INTO users(email,pw) VALUES(?,?)", (email, generate_password_hash(pw))); db().commit()
                return redirect(url_for("login"))
            except sqlite3.IntegrityError:
                flash("Email already registered.")
    return render_template("auth.html", title="Register")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = db().execute("SELECT * FROM users WHERE email=?", (request.form["email"].strip().lower(),)).fetchone()
        if u and check_password_hash(u["pw"], request.form["password"]):
            session.clear(); session["uid"] = u["id"]; return redirect(url_for("home"))
        flash("Invalid credentials.")
    return render_template("auth.html", title="Login")

@app.route("/logout", methods=["POST"])
def logout():
    session.clear(); return redirect(url_for("login"))

@app.route("/", methods=["GET", "POST"])
@login_required
def home():
    result = None
    if request.method == "POST":
        try:
            d = {k: float(request.form[k]) for k in FEATURES}
            assert all(LIMITS[k][0] <= v <= LIMITS[k][1] for k, v in d.items())
        except (ValueError, KeyError, AssertionError):
            flash("Please enter valid numbers within range."); return redirect(url_for("home"))
        pred = float(model().predict(pd.DataFrame([d]))[0])
        db().execute("INSERT INTO predictions(user_id,study_hours,attendance,sleep_hours,previous_score,predicted) VALUES(?,?,?,?,?,?)",
                     (session["uid"], *d.values(), pred)); db().commit()
        result = {"score": round(pred, 1), "tip": study_tip(d, pred)}
    return render_template("home.html", result=result)

@app.route("/api/stats")
@login_required
def stats():  # Data analytics with pandas
    df = pd.read_sql_query("SELECT * FROM predictions WHERE user_id=? ORDER BY id", db(), params=(session["uid"],))
    if df.empty: return jsonify(history=[], avg=None, corr={})
    corr = df[FEATURES + ["predicted"]].corr()["predicted"].drop("predicted").round(2).to_dict() if len(df) > 2 else {}
    return jsonify(history=df.predicted.round(1).tolist(), avg=round(df.predicted.mean(), 1), best=round(df.predicted.max(), 1), corr=corr)

@app.route("/health")
def health(): return "ok"

init_db()
if __name__ == "__main__":
    app.run(debug=True)
