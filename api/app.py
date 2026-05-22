import sys
import os

sys.stdout.reconfigure(encoding='utf-8')

os.environ.pop('HTTP_PROXY', None)
os.environ.pop('HTTPS_PROXY', None)
os.environ.pop('http_proxy', None)
os.environ.pop('https_proxy', None)

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.routes import auth, cars, chat, dashboard, favorites, messages, misc, notifications, preferences, predict, three_d
from api.services.three_d import startup_3d_queue
from api.state import DOWNLOAD_DIR

app = FastAPI(title="Car Price Prediction API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost",
        "http://localhost:80",
        "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

@app.middleware("http")
async def force_utf8(request: Request, call_next):
    response = await call_next(request)
    if "application/json" in response.headers.get("content-type", ""):
        response.headers["content-type"] = "application/json; charset=utf-8"
    return response

os.makedirs("static/images", exist_ok=True)
os.makedirs(str(DOWNLOAD_DIR), exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/3d_models", StaticFiles(directory=str(DOWNLOAD_DIR)), name="3d_models")

app.include_router(misc.router)
app.include_router(chat.router)
app.include_router(predict.router)
app.include_router(cars.router)
app.include_router(auth.router)
app.include_router(messages.router)
app.include_router(dashboard.router)
app.include_router(favorites.router)
app.include_router(notifications.router)
app.include_router(preferences.router)
app.include_router(three_d.router)

app.add_event_handler("startup", startup_3d_queue)
