"""
Runway ML Video Generator Module
--------------------------------
Handles video generation using Runway ML API.
"""

import os
import base64
import json
import logging
import time
from typing import Dict, Any, Optional, Tuple, Union
from pathlib import Path

from .api_handler import RunwayAPIHandler

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RunwayVideoGenerator:
    """
    Generator for creating videos using Runway ML API.
    """
    
    def __init__(self, api_handler: Optional[RunwayAPIHandler] = None, api_key: Optional[str] = None):
        """
        Initialize the video generator.
        
        Args:
            api_handler: Existing RunwayAPIHandler instance (optional)
            api_key: The Runway ML API key (optional, used only if api_handler not provided)
        """
        self.api_handler = api_handler or RunwayAPIHandler(api_key)
        logger.info("RunwayVideoGenerator initialized")
    
    def encode_image_to_base64(self, image_path: Union[str, Path]) -> str:
        """
        Encode an image to base64 string.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Base64 encoded string with data URI prefix
        """
        image_path = Path(image_path)
        
        if not image_path.exists():
            raise FileNotFoundError(f"Image file not found: {image_path}")
            
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
            
        # Determine image format from extension
        img_format = image_path.suffix.lower().lstrip('.')
        if img_format in ('jpg', 'jpeg'):
            mime_type = 'image/jpeg'
        elif img_format == 'png':
            mime_type = 'image/png'
        else:
            raise ValueError(f"Unsupported image format: {img_format}. Use JPG or PNG.")
            
        # Format as data URI
        return f"data:{mime_type};base64,{encoded_string}"
    
    def create_video_from_image(
        self,
        image_path: Union[str, Path],
        prompt_text: str,
        duration: int = 5,
        ratio: str = "1280:720",
        model: str = "gen4_turbo",
        seed: Optional[int] = None,
        watermark: bool = False,
    ) -> Dict[str, Any]:
        """
        Create a video from an image using Runway ML API.
        
        Args:
            image_path: Path to the image file
            prompt_text: Text prompt describing the desired motion
            duration: Video duration in seconds (5 or 10)
            ratio: Aspect ratio (e.g., "1280:720", "720:1280", etc.)
            model: Model to use (default: "gen4_turbo")
            seed: Optional seed for reproducibility
            watermark: Whether to include the Runway watermark
            
        Returns:
            Response data containing task ID
            
        Raises:
            ValueError: If parameters are invalid
            requests.exceptions.RequestException: If API request fails
        """
        # Validate parameters
        if duration not in (5, 10):
            raise ValueError("Duration must be either 5 or 10 seconds")
            
        valid_ratios = ["1280:720", "720:1280", "1104:832", "832:1104", "960:960", "1584:672"]
        if ratio not in valid_ratios:
            raise ValueError(f"Invalid ratio. Must be one of: {', '.join(valid_ratios)}")
        
        # Encode the image to base64
        encoded_image = self.encode_image_to_base64(image_path)
        
        # Prepare the payload
        payload = {
            "model": model,
            "prompt_image": encoded_image,
            "prompt_text": prompt_text,
            "duration": duration,
            "ratio": ratio,
            "watermark": watermark,
        }
        
        # Add optional seed if provided
        if seed is not None:
            payload["seed"] = seed
        
        # Create the video generation task
        logger.info(f"Creating video with {model} model, {duration}s duration, {ratio} ratio")
        response = self.api_handler.make_request("POST", "/image-to-video", payload)
        
        logger.info(f"Video generation task created: {response.get('id', 'Unknown ID')}")
        return response
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        Get the status of a video generation task.
        
        Args:
            task_id: The task ID returned from create_video_from_image
            
        Returns:
            Status data
        """
        return self.api_handler.make_request("GET", f"/tasks/{task_id}")
    
    def wait_for_completion(
        self, 
        task_id: str, 
        polling_interval: float = 5.0,
        timeout: float = 300.0
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Wait for a task to complete.
        
        Args:
            task_id: The task ID
            polling_interval: How often to check status (seconds)
            timeout: Maximum time to wait (seconds)
            
        Returns:
            Tuple of (success, response_data)
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            status_data = self.get_task_status(task_id)
            
            status = status_data.get("status")
            logger.info(f"Task {task_id}: Status = {status}")
            
            if status == "completed":
                logger.info(f"Task {task_id} completed successfully")
                return True, status_data
            elif status in ("failed", "canceled"):
                logger.error(f"Task {task_id} {status}: {status_data.get('error', 'Unknown error')}")
                return False, status_data
            
            # Still processing, wait and check again
            logger.debug(f"Task still processing. Waiting {polling_interval}s before next check.")
            time.sleep(polling_interval)
        
        # If we get here, we timed out
        logger.warning(f"Timeout waiting for task {task_id} to complete")
        return False, {"status": "timeout"}
