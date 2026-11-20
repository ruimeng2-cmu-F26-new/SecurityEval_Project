from urllib.parse import quote


def build_user_api_url(user_id: str) -> str:
    """Return the GitHub REST API URL from which the profile of the user with the given
    user_id is retrieved: https://api.github.com/users/<user_id>.
    """
    if not isinstance(user_id, str):
        raise TypeError("user_id must be a string")
    if not user_id:
        raise ValueError("user_id must not be empty")
    return "https://api.github.com/users/" + quote(user_id, safe="")
