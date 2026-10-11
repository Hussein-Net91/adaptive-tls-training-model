"""Check that the exported deployment model in C reproduces the Python predictions.

The script re-runs the data-preparation cells of the notebook (sections 1 to 9), refits the
deployment configuration recorded in results.json, truncates it at the deployed round count,
compiles xgb_model.c with a small harness and compares the two sets of test-set classes.

Usage, from the repository root with the five captures in DATA_DIR:

    python tools/verify_c_export.py --data-dir . \
        --results results/results.json \
        --model results/models/deployment_depth4_r100

Requires gcc and the packages in requirements.txt.
"""
import argparse
import json
import os
import subprocess
import tempfile

import matplotlib

matplotlib.use("Agg")
import numpy as np  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

ap = argparse.ArgumentParser()
ap.add_argument("--notebook", default=os.path.join(ROOT, "xgb_ch5_model_selection_and_tuning.ipynb"))
ap.add_argument("--data-dir", default=ROOT)
ap.add_argument("--results", default=os.path.join(ROOT, "results", "results.json"))
ap.add_argument("--model", default=os.path.join(ROOT, "results", "models", "deployment_depth4_r100"))
args = ap.parse_args()

notebook = os.path.abspath(args.notebook)
data_dir = os.path.abspath(args.data_dir)
results = os.path.abspath(args.results)
model = os.path.abspath(args.model)

work = tempfile.mkdtemp(prefix="verify_c_")
os.chdir(work)
for f in os.listdir(data_dir):
    if f.startswith("client-") and f.endswith(".csv"):
        os.symlink(os.path.join(data_dir, f), f)

# Sections 1 to 9 of the notebook: loading, cleaning, labelling, split and scaling
nb = json.load(open(notebook))
ns = {"display": lambda *a, **k: None}
for cell in nb["cells"]:
    if cell["cell_type"] != "code":
        continue
    src = "".join(cell["source"])
    code = "\n".join(l for l in src.split("\n") if not l.strip().startswith(("!", "%")))
    exec(compile(code, "notebook", "exec"), ns)
    if src.lstrip().startswith("# 9) Split and scaling"):
        break

dep = json.load(open(results))["deployment"]
X, Xte, Str, Ste, ytr, yte, cols = (ns[k] for k in ("X", "Xte", "Str", "Ste", "ytr", "yte", "COLS"))
assert list(Xte.columns) == cols

m = X.XGBClassifier(objective="multi:softprob", num_class=3, n_estimators=dep["rounds"],
                    tree_method="hist", n_jobs=-1, random_state=ns["MODEL_SEED"],
                    eval_metric="mlogloss", verbosity=0, **dep["params"])
m.fit(Str, ytr)
py = m.get_booster().predict(X.DMatrix(Ste)).argmax(1)

np.savetxt("xte.csv", Xte.to_numpy(np.float32), fmt="%.9g", delimiter=",")
subprocess.run(["gcc", "-std=c99", "-O2", "-Wall", "-o", "harness",
                os.path.join(HERE, "harness.c"), os.path.join(model, "xgb_model.c"),
                f"-I{model}", "-lm"], check=True)
out = subprocess.run(["./harness", "xte.csv", str(len(cols))], check=True,
                     capture_output=True, text=True).stdout.split()
c_pred = np.array([int(v) for v in out])

print(f"test records:          {len(yte)}")
print(f"Python accuracy:       {(py == yte).mean():.4f}")
print(f"C accuracy:            {(c_pred == yte).mean():.4f}")
print(f"C and Python agree on: {(c_pred == py).sum()} / {len(py)}")
print(f"results.json reports:  {dep['hold_out']['accuracy']:.4f}")
