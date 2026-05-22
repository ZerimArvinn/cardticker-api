"""Authentication utilities for AWS Cognito."""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from typing import Optional
import requests
from functools import lru_cache

# AWS Cognito configuration
COGNITO_REGION = "us-east-1"
COGNITO_USER_POOL_ID = "us-east-1_L2VDHCfsm"
COGNITO_APP_CLIENT_ID = "18t3duef0f88leu6m9bmkmrf4"

# Cognito JWKS URL
COGNITO_JWKS_URL = f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{COGNITO_USER_POOL_ID}/.well-known/jwks.json"

security = HTTPBearer(auto_error=False)


@lru_cache()
def get_cognito_public_keys():
    """Fetch and cache Cognito public keys for JWT verification."""
    try:
        response = requests.get(COGNITO_JWKS_URL)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching Cognito public keys: {e}")
        return None


def verify_cognito_token(token: str) -> Optional[dict]:
    """
    Verify a Cognito JWT token and return the decoded payload.

    Returns:
        dict: Decoded token payload with user info
        None: If token is invalid
    """
    try:
        # Get the public keys
        jwks = get_cognito_public_keys()
        if not jwks:
            return None

        # Decode the token header to get the key ID
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")

        # Find the matching public key
        rsa_key = None
        for key in jwks.get("keys", []):
            if key.get("kid") == kid:
                rsa_key = {
                    "kty": key.get("kty"),
                    "kid": key.get("kid"),
                    "use": key.get("use"),
                    "n": key.get("n"),
                    "e": key.get("e")
                }
                break

        if not rsa_key:
            return None

        # Verify and decode the token
        # Note: python-jose expects the key in JWK format
        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=["RS256"],
            audience=COGNITO_APP_CLIENT_ID,
            options={"verify_exp": True}
        )

        return payload
    except JWTError as e:
        print(f"JWT verification error: {e}")
        return None
    except Exception as e:
        print(f"Token verification error: {e}")
        return None


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[dict]:
    """
    Dependency to get the current authenticated user from the JWT token.
    Returns None if no token or invalid token (for optional auth).
    """
    if not credentials:
        return None
    
    token = credentials.credentials
    payload = verify_cognito_token(token)
    
    if not payload:
        return None
    
    return {
        "sub": payload.get("sub"),  # Cognito user ID
        "email": payload.get("email"),
        "name": payload.get("name"),
        "email_verified": payload.get("email_verified", False),
    }


async def require_auth(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> dict:
    """
    Dependency to require authentication.
    Raises 401 if no valid token is provided.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    payload = verify_cognito_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return {
        "sub": payload.get("sub"),  # Cognito user ID
        "email": payload.get("email"),
        "name": payload.get("name"),
        "email_verified": payload.get("email_verified", False),
    }

