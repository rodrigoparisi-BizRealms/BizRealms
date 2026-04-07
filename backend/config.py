"""BizRealms - Shared configuration and constants."""
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).parent
env_path = ROOT_DIR / '.env'
if env_path.exists():
    load_dotenv(env_path)

# MongoDB
MONGO_URL = os.getenv('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.getenv('DB_NAME', 'bizrealms')

logger.info(f"Database: {DB_NAME} | Mongo URL configured: {'yes' if 'mongodb' in MONGO_URL else 'no'}")

# JWT
JWT_SECRET = os.getenv('JWT_SECRET', 'your-super-secret-jwt-key-change-in-production')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_DAYS = 30

# Stripe
import stripe
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

# Apple
APPLE_BUNDLE_ID = os.getenv('APPLE_BUNDLE_ID', 'com.bizrealms.app')
