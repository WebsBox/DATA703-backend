from flask_jwt_extended import get_jwt_identity, get_jwt


def get_current_user_id() -> int:
    """Return current user id from JWT identity (string)."""
    identity = get_jwt_identity()
    try:
        return int(identity)
    except (TypeError, ValueError):
        return 0


def get_current_user_role() -> str:
    """Return current user role from JWT claims."""
    claims = get_jwt()
    return claims.get('role', 'user')
