from app import create_app

app = create_app()

# --- DEBUG: print route map so we can see what's actually registered ---
print("\n[Flask] Registered routes:")
for rule in sorted(app.url_map.iter_rules(), key=lambda r: r.rule):
    print(f"  {rule.rule:30s}  methods={','.join(sorted(rule.methods))}")
print()

# --- DEBUG: a simple health endpoint to confirm we hit the right server ---
@app.get("/healthz")
def healthz():
    return "ok", 200

if __name__ == "__main__":
    app.run(debug=True)
