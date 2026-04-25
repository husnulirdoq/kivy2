from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Wellbeing Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Wellbeing Backend API"}

@app.post("/login")
def login(email: str, password: str):
    return {"user_id": "temp_user", "token": "temp_token"}

@app.get("/tasks/{user_id}")
def get_tasks(user_id: str):
    return {"tasks": []}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
