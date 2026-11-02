def get_current_user() -> str:
    """Mock auth dependency returning an operator.

    Will be replaced with JWT token verification in US-7 (subtask 7.1).
    """
    return "operator"
