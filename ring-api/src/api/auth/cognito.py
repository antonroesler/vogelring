import jwt
import requests
from jwt.algorithms import RSAAlgorithm
from aws_lambda_powertools import Logger
from typing import Optional, Dict, Any
from functools import lru_cache

logger = Logger()


@lru_cache(maxsize=10)
def fetch_cognito_public_keys(user_pool_id: str, region: str) -> Dict[str, Any]:
    """Fetch and cache Cognito public keys for JWT verification"""
    url = f"https://cognito-idp.{region}.amazonaws.com/{user_pool_id}/.well-known/jwks.json"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Failed to fetch Cognito public keys: {str(e)}")
        raise


def verify_jwt_token(token: str, user_pool_id: str, client_id: str, region: str) -> Optional[Dict[str, Any]]:
    """Verify JWT token and return claims if valid"""
    try:
        # Get the kid from token header
        header = jwt.get_unverified_header(token)
        kid = header.get("kid")

        if not kid:
            logger.error("Token header missing 'kid' field")
            return None

        # Get public keys
        jwks = fetch_cognito_public_keys(user_pool_id, region)

        # Find the correct key
        public_key = None
        for key in jwks.get("keys", []):
            if key.get("kid") == kid:
                public_key = RSAAlgorithm.from_jwk(key)
                break

        if not public_key:
            logger.error(f"Public key not found for kid: {kid}")
            return None

        # Verify and decode token
        payload = jwt.decode(token, public_key, algorithms=["RS256"], audience=client_id, options={"verify_exp": True})

        # Additional validation for Cognito tokens
        if payload.get("token_use") != "id":
            logger.error(f"Invalid token use: {payload.get('token_use')}")
            return None

        return payload
    except jwt.ExpiredSignatureError:
        logger.error("JWT token has expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.error(f"JWT token is invalid: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"JWT verification failed: {str(e)}")
        return None


def get_user_id_from_token(token: str, user_pool_id: str, client_id: str, region: str) -> Optional[str]:
    """Extract user ID from JWT token"""
    claims = verify_jwt_token(token, user_pool_id, client_id, region)
    if claims:
        return claims.get("sub")  # 'sub' is the user ID in Cognito
    return None


def get_user_context_from_token(token: str, user_pool_id: str, client_id: str, region: str) -> Optional[Dict[str, Any]]:
    """Extract full user context from JWT token"""
    claims = verify_jwt_token(token, user_pool_id, client_id, region)
    if claims:
        return {
            "user_id": claims.get("sub"),
            "email": claims.get("email"),
            "username": claims.get("cognito:username"),
            "email_verified": claims.get("email_verified", False),
            "token_use": claims.get("token_use"),
            "auth_time": claims.get("auth_time"),
            "iat": claims.get("iat"),
            "exp": claims.get("exp"),
        }
    return None
