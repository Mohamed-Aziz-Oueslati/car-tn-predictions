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


# ── CORSStaticFiles ────────────────────────────────────────────────────────────
# FastAPI's CORSMiddleware does NOT cover mounted StaticFiles — they run as
# sub-applications and bypass the middleware stack entirely.
# This subclass injects all required headers on every static file response,
# including the ngrok bypass header so the browser never hits the interstitial.
class CORSStaticFiles(StaticFiles):
    CORS_HEADERS = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, HEAD, OPTIONS",
        "Access-Control-Allow-Headers": "*",
        # Fixes OpaqueResponseBlocking in Chrome
        "Cross-Origin-Resource-Policy": "cross-origin",
        # Bypasses ngrok's browser interstitial page
        "ngrok-skip-browser-warning": "true",
    }

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http" and scope["method"] == "OPTIONS":
            from starlette.responses import Response
            response = Response(status_code=204, headers=self.CORS_HEADERS)
            await response(scope, receive, send)
            return

        async def send_with_cors(message):
            if message["type"] == "http.response.start":
                headers = dict(message.get("headers", []))
                for k, v in self.CORS_HEADERS.items():
                    headers[k.lower().encode()] = v.encode()
                message = {**message, "headers": list(headers.items())}
            await send(message)

        await super().__call__(scope, receive, send_with_cors)


# ── App ────────────────────────────────────────────────────────────────────────
app = FastAPI(title="Car Price Prediction API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost",
        "http://localhost:80",
        "https://tricky-suspense-refurnish.ngrok-free.dev",
        "https://automarket-tekup.netlify.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

@app.middleware("http")
async def add_ngrok_headers(request: Request, call_next):
    response = await call_next(request)
    # Force UTF-8 on JSON responses
    if "application/json" in response.headers.get("content-type", ""):
        response.headers["content-type"] = "application/json; charset=utf-8"
    # Ensure ngrok bypass + CORP on all non-static responses too
    response.headers["ngrok-skip-browser-warning"] = "true"
    response.headers["Cross-Origin-Resource-Policy"] = "cross-origin"
    return response

# ── Directories ────────────────────────────────────────────────────────────────
os.makedirs("static/images", exist_ok=True)
os.makedirs(str(DOWNLOAD_DIR), exist_ok=True)

# ── Static mounts ──────────────────────────────────────────────────────────────
app.mount("/static", CORSStaticFiles(directory="static"), name="static")
app.mount("/3d_models", CORSStaticFiles(directory=str(DOWNLOAD_DIR)), name="3d_models")

# ── Routers ────────────────────────────────────────────────────────────────────
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