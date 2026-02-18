from cost_estimator_agent import PROCEDURES
for p in PROCEDURES:
    if "wisdom" in p["name"].lower() or "extract" in p["name"].lower():
        print(p["name"])