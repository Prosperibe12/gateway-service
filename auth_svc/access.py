import os, requests
from decouple import config

def login(request):
    """
    Define access to Authentication Service Login Endpoint
    """ 
    # get authorization credentials
    auth = request.authorization 
    if not auth:
        return None, ("Missing Credentials", 401)
    
    # make connection to auth-service
    try:
        response = requests.post(
            f"http://{config('AUTH_SVC_ADDRESS')}/login/",
            auth=(auth.username, auth.password)
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return None, (str(e), 500)
    
    return response.json(), None
    