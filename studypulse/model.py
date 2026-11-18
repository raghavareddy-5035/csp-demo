"""ML layer: trains a RandomForest on synthetic student data (swap in a real CSV later)."""
import joblib, numpy as np, pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score

FEATURES = ["study_hours", "attendance", "sleep_hours", "previous_score"]

def make_data(n=1500, seed=42):
    r = np.random.default_rng(seed)
    df = pd.DataFrame({
        "study_hours": r.uniform(0, 8, n), "attendance": r.uniform(40, 100, n),
        "sleep_hours": r.uniform(4, 10, n), "previous_score": r.uniform(30, 100, n)})
    df["final_score"] = (0.35*df.previous_score + 4*df.study_hours + 0.25*df.attendance
        - 1.2*(df.sleep_hours-7.5)**2 + r.normal(0, 4, n) + 5).clip(0, 100)
    return df

def train(path="model.joblib"):
    df = make_data()
    Xtr, Xte, ytr, yte = train_test_split(df[FEATURES], df.final_score, test_size=0.2, random_state=1)
    m = RandomForestRegressor(n_estimators=150, random_state=1).fit(Xtr, ytr)
    joblib.dump(m, path)
    return m, r2_score(yte, m.predict(Xte))

if __name__ == "__main__":
    print("R2 on test set: %.3f" % train()[1])
