import requests
from decouple import config

def token(request):
    """
    Function creates interface for validating user Access tokens
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return None, ("Missing Credentials", 401)
    
    try:
        response = requests.post(
            f"http://{config('AUTH_SVC_ADDRESS')}/token-verify/",
            headers={"Authorization": auth_header}
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return None, (str(e), 500)
    
    return response.json(), 200
    