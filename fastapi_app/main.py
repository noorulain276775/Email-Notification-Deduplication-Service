from fastapi import FastAPI

app = FastAPI()

# Placeholder for database setup and API routes

@app.get("/")
def read_root():
    return {"message": "FastAPI Email Notification Deduplication Service"}
