"""
utils.py

This module handles the security and authentication utilities for the 
FastAPI project, including password hashing, password verification, 
and JWT token creation. It uses the secret key from the corresponding 
environment variable to configure settings for JWT token generation.

Functions:
    verify_password: Verifies a plain text password against a hashed password.
    get_password_hash: Hashes a plain text password using bcrypt.
    create_access_token: Creates a JWT token for authentication with 
    an expiration time.
"""

import os
from typing import Any
from datetime import (
    datetime,
    timedelta,
    timezone
)
from dotenv import load_dotenv
from jose import jwt
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

load_dotenv()
SECRET_KEY = os.environ.get("SECRET_KEY")
ALGORITHM = "HS256"

if SECRET_KEY is None:
    raise ValueError("SECRET_KEY not found in environment variables")


def verify_password(plain_password, hashed_password):
    """
    Verifies if the provided plain text password matches the hashed password.

    Args:
        plain_password (str): The plain text password to verify.
        hashed_password (str): The hashed password stored in the database.

    Returns:
        bool: True if the password matches, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    """
    Hashes a plain text password using the bcrypt algorithm.

    Args:
        password (str): The plain text password to hash.

    Returns:
        str: The hashed password.
    """
    return pwd_context.hash(password)


def create_access_token(
        data: dict[str, Any], expires_delta: timedelta | None = None
):
    """
    Creates a JWT token with an expiration time.

    The token is encoded using the HS256 algorithm and the secret key from 
    the environment variables.
    The expiration time can be customized by passing a `timedelta` object.
    If no expiration is provided, the token will expire in 15 minutes by default.

    Args:
        data (dict[str, Any]): The data to encode in the JWT token 
        (e.g., user ID or email).
        expires_delta (timedelta | None, optional): The time delta for 
        token expiration. Defaults to 15 minutes.

    Returns:
        str: The encoded JWT token.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt
