from datetime import datetime, timedelta
from typing import Optional, Union, Any
from jose import jwt, JWTError
from passlib.context import CryptContext
from google.oauth2 import id_token
from google.auth.transport import requests
import httpx
import os
import json
import time

from app.core.config import settings

# Setup password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ── Google Public Keys Cache (for Firebase token verification) ────────────────
# Firebase ID tokens are signed by Google. We fetch the public keys once and
# cache them. This avoids needing Firebase Admin SDK or Application Default
# Credentials entirely — works on any server (Render, Heroku, VPS, etc.)
_google_public_keys: dict = {}
_google_keys_expiry: float = 0

GOOGLE_CERTS_URL = "https://www.googleapis.com/robot/v1/metadata/x509/securetoken@system.gserviceaccount.com"
FIREBASE_ISSUER_PREFIX = "https://securetoken.google.com/"


def _refresh_google_public_keys() -> dict:
    """Fetch Google's public signing certificates for Firebase token verification."""
    global _google_public_keys, _google_keys_expiry

    # Return cached keys if still valid
    if _google_public_keys and time.time() < _google_keys_expiry:
        return _google_public_keys

    try:
        # Synchronous fetch (runs once at startup / every ~6 hours)
        import urllib.request
        req = urllib.request.Request(GOOGLE_CERTS_URL)
        with urllib.request.urlopen(req, timeout=10) as response:
            _google_public_keys = json.loads(response.read().decode())
            # Cache for 6 hours (Google rotates keys roughly every 6h)
            cache_control = response.headers.get("Cache-Control", "")
            max_age = 21600  # default 6 hours
            for part in cache_control.split(","):
                part = part.strip()
                if part.startswith("max-age="):
                    try:
                        max_age = int(part.split("=")[1])
                    except ValueError:
                        pass
            _google_keys_expiry = time.time() + max_age
            print(f"Firebase: Fetched {len(_google_public_keys)} Google public keys (cached for {max_age}s).")
            return _google_public_keys
    except Exception as e:
        print(f"Firebase: Failed to fetch Google public keys: {e}")
        return _google_public_keys  # return stale cache if available


# Pre-fetch keys at module load
_refresh_google_public_keys()
print(f"Firebase token verification ready (project: {settings.FIREBASE_PROJECT_ID}).")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    try:
        decoded_token = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return decoded_token
    except JWTError:
        return None


def verify_google_token(token: str) -> Optional[dict]:
    """
    Verifies a Google ID token and returns the user details.
    """
    try:
        request = requests.Request()
        id_info = id_token.verify_oauth2_token(token, request)
        
        if id_info['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            return None
            
        return {
            "email": id_info.get("email"),
            "full_name": id_info.get("name"),
            "google_id": id_info.get("sub")
        }
    except Exception as e:
        print(f"Google ID token verification failed: {e}")
        return None


def verify_firebase_token(token: str) -> Optional[dict]:
    """
    Verifies a Firebase Authentication ID token using Google's public keys.
    
    This is a MANUAL verification that does NOT require:
    - Firebase Admin SDK
    - Application Default Credentials (ADC)
    - A GCP service account
    
    It works by:
    1. Fetching Google's public X.509 certificates
    2. Decoding the JWT with RS256 signature verification
    3. Validating issuer, audience, and expiry claims
    
    This works on ANY hosting platform (Render, Heroku, AWS, VPS, etc.)
    """
    project_id = settings.FIREBASE_PROJECT_ID
    if not project_id:
        print("Firebase: FIREBASE_PROJECT_ID not set. Cannot verify tokens.")
        return None

    # Get the public keys
    public_keys = _refresh_google_public_keys()
    if not public_keys:
        print("Firebase: No Google public keys available for verification.")
        return None

    # Extract the key ID from the token header
    try:
        unverified_header = jwt.get_unverified_header(token)
    except JWTError as e:
        print(f"Firebase: Could not decode token header: {e}")
        return None

    kid = unverified_header.get("kid")
    if not kid or kid not in public_keys:
        print(f"Firebase: Token key ID '{kid}' not found in Google public keys.")
        return None

    # Get the matching public certificate
    public_cert = public_keys[kid]

    try:
        # Decode and verify the token
        decoded = jwt.decode(
            token,
            public_cert,
            algorithms=["RS256"],
            audience=project_id,
            issuer=f"{FIREBASE_ISSUER_PREFIX}{project_id}",
        )

        # Additional validation
        uid = decoded.get("sub") or decoded.get("user_id")
        email = decoded.get("email")

        if not uid:
            print("Firebase: Token missing 'sub' (user ID) claim.")
            return None

        print(f"Firebase: Token verified successfully for uid={uid}, email={email}")

        return {
            "email": email,
            "full_name": decoded.get("name"),
            "firebase_uid": uid,
        }

    except jwt.ExpiredSignatureError:
        print("Firebase: Token has expired.")
        return None
    except jwt.JWTClaimsError as e:
        print(f"Firebase: Token claims verification failed: {e}")
        return None
    except JWTError as e:
        print(f"Firebase: Token signature verification failed: {e}")
        return None
    except Exception as e:
        print(f"Firebase: Unexpected token verification error: {e}")
        return None
