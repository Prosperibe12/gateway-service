import os
import requests

class AuthService:
    """
    A class to handles request to the authentication-service
    """
    def __init__(self, auth_service_addr):
        """
        Initialize the AuthService with the authentication service address.
        """
        self.auth_svc_address = auth_service_addr

    def login(self, request):
        """
        Authenticate a user by connecting to the Authentication Service Login Endpoint.

        Args:
            request: The request object containing authorization credentials.

        Returns:
            tuple: A tuple containing the response JSON and an error message (if any).
        """
        # Get authorization credentials
        auth = request.authorization
        if not auth:
            return None, ("Missing Credentials", 401)

        # Make connection to auth-service
        try:
            response = requests.post(
                f"http://{self.auth_svc_address}/login/",
                auth=(auth.username, auth.password),
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            return None, (str(e), 500)

        return response.json(), None

    def token(self, request):
        """
        Validate a user's access token by connecting to the Authentication Service Token Verification Endpoint.

        Args:
            request: The request object containing the authorization header.

        Returns:
            tuple: A tuple containing the response JSON and an error message (if any).
        """
        # Get authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return None, ("Missing Credentials", 401)

        # Validate the token
        try:
            response = requests.post(
                f"http://{self.auth_svc_address}/token-verify/",
                headers={"Authorization": auth_header},
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            return None, (str(e), 500)

        return response.json(), None