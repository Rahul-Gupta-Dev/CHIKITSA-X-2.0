import os
import sqlite3
import hashlib
import json

def generate_inventory():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    uploads_dir = os.path.join(base_dir, "uploads", "medical_records")
    db_file = os.path.join(base_dir, "chikitsax.db")
    
    # Read DB records
    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT id, patient_id, file_name, file_type, category, upload_date, created_at, file_path, is_verified_by_patient FROM medical_records")
    records = [dict(r) for r in cur.fetchall()]
    conn.close()
    
    db_by_filename = {}
    db_by_basepath = {}
    for r in records:
        if r.get("file_name"):
            db_by_filename[r["file_name"]] = r
        if r.get("file_path"):
            base = os.path.basename(r["file_path"].replace("\\", "/"))
            db_by_basepath[base] = r
            
    inventory = []
    
    for root, dirs, files in os.walk(uploads_dir):
        for f in sorted(files):
            fpath = os.path.join(root, f)
            rel_path = os.path.relpath(fpath, base_dir).replace("\\", "/")
            size = os.path.getsize(fpath)
            with open(fpath, "rb") as fh:
                sha256 = hashlib.sha256(fh.read()).hexdigest()
                
            db_match = db_by_basepath.get(f) or db_by_filename.get(f)
            
            entry = {
                "file_name": f,
                "relative_path": rel_path,
                "file_size": size,
                "sha256": sha256,
                "is_registered_in_db": bool(db_match),
                "record_id": db_match["id"] if db_match else None,
                "patient_id": db_match["patient_id"] if db_match else None,
                "category": db_match["category"] if db_match else None,
                "upload_date": db_match["upload_date"] if db_match else None,
                "is_verified": bool(db_match["is_verified_by_patient"]) if db_match else False
            }
            inventory.append(entry)
            
    out_json = os.path.join(base_dir, "medical_files_inventory.json")
    with open(out_json, "w", encoding="utf-8") as fh:
        json.dump(inventory, fh, indent=2)
        
    print(f"Generated inventory for {len(inventory)} files.")
    print(f"  - Registered in DB: {sum(1 for x in inventory if x['is_registered_in_db'])}")
    print(f"  - Standalone/historical files: {sum(1 for x in inventory if not x['is_registered_in_db'])}")
    print(f"Saved inventory to {out_json}")
    return inventory

if __name__ == "__main__":
    generate_inventory()
