"""Desktop app (Tkinter). Usage: python desktop_app.py"""
import json, tkinter as tk, urllib.request
from tkinter import messagebox

FIELDS = ["study_hours", "attendance", "sleep_hours", "previous_score"]
root = tk.Tk(); root.title("StudyPulse Desktop")
entries = {}
for i, name in enumerate(["Server URL", "API key"] + FIELDS):
    tk.Label(root, text=name).grid(row=i, column=0, sticky="w", padx=8, pady=3)
    e = tk.Entry(root, width=42); e.grid(row=i, column=1, padx=8); entries[name] = e
entries["Server URL"].insert(0, "http://127.0.0.1:5000")
out = tk.Label(root, text="", wraplength=380, justify="left", font=("Segoe UI", 11)); out.grid(row=8, columnspan=2, pady=8)

def predict():
    try:
        body = {k: float(entries[k].get()) for k in FIELDS}
        req = urllib.request.Request(entries["Server URL"].get().rstrip("/") + "/api/predict", json.dumps(body).encode(),
                                     {"Content-Type": "application/json", "X-API-Key": entries["API key"].get().strip()})
        r = json.loads(urllib.request.urlopen(req, timeout=60).read())
        out.config(text=f"Predicted score: {r['predicted']}\n{r['tip']}")
    except Exception as ex:
        messagebox.showerror("Error", str(ex))

tk.Button(root, text="Predict", command=predict).grid(row=7, columnspan=2, pady=6)
root.mainloop()
