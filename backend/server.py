"""BizRealms - Main Server (Modularized)"""
from fastapi import FastAPI, APIRouter
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, HTMLResponse
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from collections import defaultdict
import time as time_module

# Shared modules
from config import JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRATION_DAYS, APPLE_BUNDLE_ID
from database import db, client

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# ==================== APP SETUP ====================
app = FastAPI(title="BizRealms API")
api_router = APIRouter(prefix="/api")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== RATE LIMITING ====================
class RateLimiter:
    """Simple in-memory rate limiter per IP and per user."""
    def __init__(self):
        self.requests: dict[str, list[float]] = defaultdict(list)

    def is_limited(self, key: str, max_requests: int = 60, window_seconds: int = 60) -> bool:
        now = time_module.time()
        self.requests[key] = [t for t in self.requests[key] if now - t < window_seconds]
        if len(self.requests[key]) >= max_requests:
            return True
        self.requests[key].append(now)
        return False

rate_limiter = RateLimiter()

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.headers.get("x-forwarded-for", request.client.host if request.client else "unknown")
    path = request.url.path
    if path.startswith("/api/auth/"):
        if rate_limiter.is_limited(f"auth:{client_ip}", max_requests=10, window_seconds=60):
            return JSONResponse(status_code=429, content={"detail": "Too many requests. Please try again later."})
    elif request.method == "POST":
        if rate_limiter.is_limited(f"post:{client_ip}", max_requests=30, window_seconds=60):
            return JSONResponse(status_code=429, content={"detail": "Too many requests. Please slow down."})
    else:
        if rate_limiter.is_limited(f"get:{client_ip}", max_requests=120, window_seconds=60):
            return JSONResponse(status_code=429, content={"detail": "Too many requests."})
    response = await call_next(request)
    return response

# ==================== PUBLIC LEGAL PAGES ====================
LEGAL_HTML_STYLE = """
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #121212; color: #ccc; padding: 24px; max-width: 720px; margin: 0 auto; line-height: 1.7; }
  h1 { color: #4CAF50; font-size: 28px; margin-bottom: 8px; }
  .meta { color: #888; font-size: 13px; margin-bottom: 32px; }
  h2 { color: #4CAF50; font-size: 18px; margin: 28px 0 10px; }
  p { margin-bottom: 12px; font-size: 15px; }
  a { color: #4CAF50; }
  .logo { text-align: center; margin-bottom: 24px; }
  .logo span { font-size: 36px; font-weight: bold; color: #fff; }
  .footer { border-top: 1px solid #333; margin-top: 40px; padding-top: 20px; text-align: center; color: #666; font-size: 12px; }
</style>
"""

@app.get("/legal/terms", response_class=HTMLResponse)
@app.get("/api/legal/terms", response_class=HTMLResponse)
async def public_terms():
    return HTMLResponse(f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>BizRealms - Terms of Use</title>{LEGAL_HTML_STYLE}</head><body>
<div class="logo"><span>BizRealms</span></div>
<h1>Terms of Use</h1>
<p class="meta">Last updated: June 2025</p>
<h2>1. Acceptance of Terms</h2>
<p>By downloading, installing, or using BizRealms ("the App"), you agree to be bound by these Terms of Use. If you do not agree, do not use the App.</p>
<h2>2. Description of Service</h2>
<p>BizRealms is a business simulation game where players manage virtual companies, investments, jobs, and assets. The in-game currency and assets have no real-world monetary value unless explicitly stated in our rewards program.</p>
<h2>3. Account Registration</h2>
<p>You must provide accurate information when creating an account. You are responsible for maintaining the security of your account credentials. One account per person is allowed.</p>
<h2>4. In-App Purchases</h2>
<p>The App may offer in-app purchases processed via Stripe. All purchases are final and non-refundable, except as required by applicable law. Virtual items purchased have no real-world value.</p>
<h2>5. Real Money Rewards</h2>
<p>BizRealms may offer real money rewards to top-ranked players. Eligibility, amounts, and payment methods are determined by BizRealms at its sole discretion. Players must provide valid payment information (e.g., PayPal account) to receive rewards.</p>
<h2>6. Prohibited Conduct</h2>
<p>You may not: use cheats, exploits, or automation; create multiple accounts; harass other players; attempt to manipulate rankings; or reverse-engineer the App.</p>
<h2>7. Intellectual Property</h2>
<p>All content, graphics, logos, and software in BizRealms are owned by BizRealms or its licensors and are protected by intellectual property laws.</p>
<h2>8. Termination</h2>
<p>We may suspend or terminate your account at any time for violation of these terms or for any other reason at our discretion.</p>
<h2>9. Limitation of Liability</h2>
<p>BizRealms is provided "as is" without warranties. We are not liable for any indirect, incidental, or consequential damages arising from your use of the App.</p>
<h2>10. Changes to Terms</h2>
<p>We may update these terms at any time. Continued use of the App after changes constitutes acceptance of the new terms.</p>
<h2>11. Contact</h2>
<p>For questions about these Terms, contact us at: <a href="mailto:support@bizrealms.com">support@bizrealms.com</a></p>
<div class="footer">&copy; 2025 BizRealms. All rights reserved. | <a href="/legal/privacy">Privacy Policy</a></div>
</body></html>""")

@app.get("/legal/privacy", response_class=HTMLResponse)
@app.get("/api/legal/privacy", response_class=HTMLResponse)
async def public_privacy():
    return HTMLResponse(f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>BizRealms - Privacy Policy</title>{LEGAL_HTML_STYLE}</head><body>
<div class="logo"><span>BizRealms</span></div>
<h1>Privacy Policy</h1>
<p class="meta">Last updated: June 2025</p>
<h2>1. Information We Collect</h2>
<p>We collect information you provide directly: name, email address, and optional profile data (avatar, city). We also collect gameplay data (progress, transactions, rankings) and device information (OS, language, timezone).</p>
<h2>2. How We Use Your Information</h2>
<p>We use your information to: provide and improve the game experience; manage your account; process in-app purchases and rewards; maintain rankings; send notifications about game events; and prevent fraud and abuse.</p>
<h2>3. Information Sharing</h2>
<p>We do not sell your personal information. We may share limited data with: payment processors (Stripe, for purchases and rewards); analytics providers (aggregated, anonymized data); and law enforcement (when required by law).</p>
<h2>4. Data Security</h2>
<p>We implement industry-standard security measures including encryption, secure authentication (JWT), password hashing (bcrypt), and regular security audits to protect your data.</p>
<h2>5. Your Rights</h2>
<p>You have the right to: access your personal data; correct inaccurate data; delete your account and associated data; export your data; and opt-out of marketing communications.</p>
<h2>6. Cookies &amp; Tracking</h2>
<p>The App uses local storage for authentication tokens and user preferences. We do not use third-party tracking cookies.</p>
<h2>7. Children's Privacy</h2>
<p>BizRealms is not intended for children under 13 (or the minimum age in your jurisdiction). We do not knowingly collect data from children.</p>
<h2>8. International Data Transfers</h2>
<p>Your data may be processed in servers located outside your country. We ensure appropriate safeguards are in place for international transfers.</p>
<h2>9. Data Retention</h2>
<p>We retain your data for as long as your account is active. After account deletion, we may retain anonymized data for analytics purposes.</p>
<h2>10. Changes to This Policy</h2>
<p>We may update this policy from time to time. We will notify you of significant changes through the App.</p>
<h2>11. Contact Us</h2>
<p>For privacy-related questions or to exercise your rights, contact us at: <a href="mailto:privacy@bizrealms.com">privacy@bizrealms.com</a></p>
<div class="footer">&copy; 2025 BizRealms. All rights reserved. | <a href="/legal/terms">Terms of Use</a></div>
</body></html>""")

# ==================== ROOT ENDPOINT ====================
@api_router.get("/")
async def root():
    return {"message": "BizRealms API", "version": "2.0.0"}

# ==================== IMPORT & INCLUDE ROUTE MODULES ====================
from routes.auth import router as auth_router
from routes.user import router as user_router
from routes.jobs import router as jobs_router
from routes.investments import router as investments_router
from routes.companies import router as companies_router
from routes.assets import router as assets_router
from routes.rankings import router as rankings_router
from routes.store import router as store_router
from routes.bank import router as bank_router
from routes.market import router as market_router
from routes.notifications import router as notifications_router

api_router.include_router(auth_router)
api_router.include_router(user_router)
api_router.include_router(jobs_router)
api_router.include_router(investments_router)
api_router.include_router(companies_router)
api_router.include_router(assets_router)
api_router.include_router(rankings_router)
api_router.include_router(store_router)
api_router.include_router(bank_router)
api_router.include_router(market_router)
api_router.include_router(notifications_router)

# Include the api_router in the main app
app.include_router(api_router)

# ==================== STARTUP EVENTS ====================
from routes.investments import startup_investments
from routes.companies import startup_map, startup_companies
from routes.assets import startup_assets

@app.on_event("startup")
async def on_startup():
    """Run all startup seed functions."""
    await startup_investments()
    await startup_map()
    await startup_companies()
    await startup_assets()

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

# ==================== LOGGING ====================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
