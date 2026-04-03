# BizRealms Backend Architecture

## Current Structure

```
/app/backend/
├── server.py          # Main app entry + all route handlers (~5000 lines)
├── config.py          # Shared configuration (DB, JWT, Stripe, Apple)
├── database.py        # MongoDB connection (db, client)
├── models.py          # All Pydantic models (User, Job, Course, etc.)
├── utils.py           # Shared utilities (auth, hashing, JWT)
├── requirements.txt   # Python dependencies
├── .env               # Environment variables (NEVER commit)
├── routes/            # Route modules (for gradual migration)
│   └── __init__.py
└── README.md          # This file
```

## Module Responsibilities

| Module | Purpose |
|--------|---------|
| `config.py` | Environment variables, JWT config, Stripe key |
| `database.py` | MongoDB connection (`db`, `client`) |
| `models.py` | All Pydantic request/response models |
| `utils.py` | Auth helpers (hash, verify, JWT, get_current_user) |
| `server.py` | FastAPI app, middleware, all route handlers |

## Server.py Sections (in order)

1. **Rate Limiting** - IP-based rate limiting middleware
2. **Legal Pages** - Public HTML pages for Terms & Privacy Policy
3. **Models** - (being migrated to models.py)
4. **Helper Functions** - (being migrated to utils.py)
5. **Auth Routes** - Login, Register, Email Verification, Password Recovery
6. **Social Auth** - Google & Apple Sign-In with token verification
7. **User Routes** - Profile, Stats, Character creation, Personal data
8. **Game Routes** - Jobs, Education, Courses, Work
9. **Investment System** - Portfolio, buy/sell investments
10. **Companies System** - Map, create/manage companies, franchises
11. **Assets System** - Real estate, vehicles, luxury items
12. **Rankings** - Weekly/monthly player rankings
13. **Real Money Rewards** - PIX-based payouts to top players
14. **Daily Free Money** - Ad watching boost system
15. **Franchise System** - Franchise operations
16. **Market Events** - Dynamic market events
17. **Banco Online** - Virtual banking (transfers, loans)
18. **AI Coaching** - OpenAI-powered game coaching
19. **Stripe Payments** - Real money checkout sessions
20. **Achievements** - Player badges/achievements
21. **Notifications** - In-app + Push notifications

## API Routes

All API routes are prefixed with `/api/`.
Legal pages are served at `/legal/terms` and `/legal/privacy` (also `/api/legal/*`).

## Environment Variables

```env
MONGO_URL=mongodb://localhost:27017
DB_NAME=bizrealms
JWT_SECRET=your-secret-key
STRIPE_SECRET_KEY=sk_live_...
APPLE_BUNDLE_ID=com.bizrealms.game
EMERGENT_LLM_KEY=your-key  # For AI Coaching
```

## Gradual Migration Plan

Routes can be extracted from server.py into `/routes/` files:
1. Import `APIRouter` from fastapi
2. Create a router: `router = APIRouter(prefix="/api")`
3. Move route handlers to the new file
4. Import shared modules: `from database import db`, `from utils import get_current_user`, etc.
5. Include the router in server.py: `app.include_router(router)`

Priority order for extraction:
1. Auth routes → `routes/auth.py`
2. Payment routes → `routes/payments.py`
3. Game routes → `routes/game.py`
4. Continue as needed
