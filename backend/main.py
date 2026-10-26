
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="CafeFlow API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)

menu = [
    {"id": 1, "name": "Veg Sandwich", "price": 60},
    {"id": 2, "name": "Masala Chai", "price": 20},
    {"id": 3, "name": "Cold Coffee", "price": 80},
]

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/menu")
def get_menu():
    return menu
