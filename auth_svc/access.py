import os,requests
from flask import jsonify

class AuthService:
    """
    A class to handles request to the authentication-service
    """
    def __init__(self, auth_service_addr):
        """
        Initialize the AuthService with the authentication service address.
        """
        self.auth_svc_address = auth_service_addr
        
    def register(self, request):
        """
        Accepts user request for registration and routes request to authentication service
        """
        try:
            # get auth details
            data = request.get_json(silent=True) or {}
            name, email, password = data.get("fullname"), data.get("email"), data.get("password")
            # validate details
            if not name or not email or not password:
                return None, ("Required details are Missing", 400)

            # Make connection to auth-service
            response = requests.post(
                f"{self.auth_svc_address}register/",
                json={"fullname": name,"email": email,"password": password},
            )
            response.raise_for_status()

            return response.json(), None
        except Exception as e:
            return None, (str(e), 500)

    def login(self, request):
        """
        Authenticate a user by connecting to the Authentication Service Login Endpoint.
        """
        try:
            data = request.get_json(silent=True) or {}
            email, password = data.get("email"), data.get("password")

            if not email or not password:
                return None, ("Missing email or password", 400)

            # Make connection to auth-service
            response = requests.post(
                f"{self.auth_svc_address}login/",
                json={"email": email, "password": password},
            )
            response.raise_for_status()

            return response.json(), None
        except Exception as e:
            return None, (str(e), 500)
        
    def verify_email_token(self, token):
        """
        Sends a request to the authentication service to verify the email token.
        """
        try:
            # Make request to authentication service
            response = requests.get(f"{self.auth_svc_address}verify-email/", params={"token": token})

            # Ensure we properly return the response JSON and status code
            return response.json(), response.status_code

        except requests.exceptions.RequestException as e:
            return {"error": "Failed to connect to authentication service", "details": str(e)}, 500

    def token(self, request):
        """
        Validate a user's access token by connecting to the Authentication Service Token Verification Endpoint.
        """
        # Get authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return None, ("Missing Credentials", 401)

        # Validate the token
        try:
            response = requests.post(
                f"{self.auth_svc_address}token-verify/",
                headers={"Authorization": auth_header},
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            return None, (str(e), 500)

        return response.json(), None