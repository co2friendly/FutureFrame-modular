"""
Runway ML API Handler Module
----------------------------
Handles authentication and basic API communication with RunwayML.
"""

import os
import requests
import logging
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RunwayAPIHandler:
    """
    Handler for Runway ML API interactions.
    """
    
    BASE_URL = "https://api.runwayml.com/v1"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Runway API handler.
        
        Args:
            api_key: The Runway ML API key (optional, will use env var if not provided)
        """
        self.api_key = api_key or os.environ.get("RUNWAYML_API_SECRET")
        
        if not self.api_key:
            raise ValueError(
                "No API key provided. Either pass api_key parameter or set RUNWAYML_API_SECRET environment variable."
            )
        
        logger.info("RunwayAPIHandler initialized")
        
    def get_headers(self) -> Dict[str, str]:
        """
        Get the necessary headers for API requests.
        
        Returns:
            Dict containing headers with authentication.
        """
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
    
    def make_request(self, method: str, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make a request to the Runway ML API.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (without base URL)
            data: Request data/payload (for POST/PUT requests)
            
        Returns:
            Response data as dictionary
            
        Raises:
            requests.exceptions.RequestException: If request fails
        """
        url = f"{self.BASE_URL}/{endpoint.lstrip('/')}"
        headers = self.get_headers()
        
        try:
            logger.info(f"Making {method} request to {endpoint}")
            
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, params=data)
            elif method.upper() == "POST":
                response = requests.post(url, headers=headers, json=data)
            elif method.upper() == "PUT":
                response = requests.put(url, headers=headers, json=data)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=headers, json=data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {str(e)}")
            
            # Try to get more details if available
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response body: {e.response.text}")
                
            raise
    
    def check_api_status(self) -> bool:
        """
        Check if the API is accessible and the key is valid.
        
        Returns:
            True if API is accessible, False otherwise
        """
        try:
            # This endpoint is based on common patterns, may need adjustment
            response = self.make_request("GET", "/organization")
            return True
        except Exception as e:
            logger.warning(f"API status check failed: {str(e)}")
            return False

