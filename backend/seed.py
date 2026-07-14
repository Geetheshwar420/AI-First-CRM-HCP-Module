import os
import sys

# Ensure backend dir is in sys.path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

from database import engine, SessionLocal
import models
from datetime import datetime

# Rebuild Database
print("Rebuilding database schemas...")
models.Base.metadata.drop_all(bind=engine)
models.Base.metadata.create_all(bind=engine)
print("Database schemas created successfully.")

db = SessionLocal()
try:
    print("Seeding HCP Profiles...")
    profiles = [
        models.HCPProfile(name="Dr. Sarah Jenkins", specialty="Oncologist", preferred_brand="OncoBoost", sample_restrictions="", has_sample_restrictions=False),
        models.HCPProfile(name="Dr. Robert Smith", specialty="Oncologist", preferred_brand="OncoBoost", sample_restrictions="Strict no-sample policy", has_sample_restrictions=True),
        models.HCPProfile(name="Dr. Lee", specialty="General Practice", preferred_brand="Drug A and Drug C", sample_restrictions="", has_sample_restrictions=False)
    ]
    db.add_all(profiles)

    print("Seeding Products...")
    products = [
        models.Product(name="OncoBoost", monthly_sample_limit=5),
        models.Product(name="Drug A", monthly_sample_limit=10),
        models.Product(name="Drug C", monthly_sample_limit=15),
        models.Product(name="BrandX", monthly_sample_limit=5)
    ]
    db.add_all(products)
    
    db.commit()
    print("Seeding successful!")
except Exception as e:
    print(f"Error seeding data: {e}")
    db.rollback()
finally:
    db.close()
