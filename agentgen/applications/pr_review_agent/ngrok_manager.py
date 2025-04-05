import logging
import os
import subprocess
import time
import json
import requests
from logging import getLogger
from typing import Optional, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = getLogger(__name__)

class NgrokManager:
    """
    Manages ngrok tunnels for exposing local services to the internet.
    This is useful for receiving GitHub webhooks on a local development machine.
    """
    
    def __init__(self, port: int, auth_token: Optional[str] = None):
        """
        Initialize the ngrok manager.
        
        Args:
            port: The local port to expose
            auth_token: Optional ngrok authentication token
        """
        self.port = port
        self.auth_token = auth_token
        self.process = None
        self.public_url = None
        logger.info(f"NgrokManager initialized for port {port}")
        logger.info(f"Auth token provided: {'Yes' if auth_token else 'No'}")
        
    def start_tunnel(self) -> Optional[str]:
        """
        Start an ngrok tunnel to expose the local server.
        
        Returns:
            The public URL of the tunnel, or None if failed
        """
        logger.info(f"Starting ngrok tunnel for port {self.port}")
        
        try:
            # Check if ngrok is installed
            try:
                result = subprocess.run(["ngrok", "--version"], check=True, capture_output=True, text=True)
                logger.info(f"ngrok version: {result.stdout.strip()}")
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                logger.error(f"ngrok is not installed or not in PATH: {e}")
                print("\n⚠️ ngrok is not installed or not in PATH.")
                print("Please install ngrok from https://ngrok.com/download")
                print("After installation, make sure it's in your PATH.")
                return None
            
            # Set auth token if provided
            if self.auth_token:
                logger.info("Setting ngrok auth token")
                try:
                    result = subprocess.run(["ngrok", "config", "add-authtoken", self.auth_token], check=True, capture_output=True, text=True)
                    logger.info(f"ngrok auth token set: {result.stdout.strip()}")
                except subprocess.CalledProcessError as e:
                    logger.error(f"Failed to set ngrok auth token: {e}")
                    logger.error(f"stdout: {e.stdout}, stderr: {e.stderr}")
                    print(f"\n⚠️ Failed to set ngrok auth token: {e}")
            
            # Start ngrok in the background
            logger.info(f"Starting ngrok http tunnel on port {self.port}")
            
            # Use non-blocking subprocess to start ngrok
            self.process = subprocess.Popen(
                ["ngrok", "http", str(self.port), "--log=stdout"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for ngrok to start and get the public URL
            logger.info("Waiting for ngrok to start...")
            max_retries = 15  # Increased retries
            retry_count = 0
            
            while retry_count < max_retries:
                try:
                    # Try to get tunnel info from ngrok API
                    response = requests.get("http://localhost:4040/api/tunnels")
                    if response.status_code == 200:
                        tunnels_data = response.json()
                        logger.info(f"ngrok API response: {json.dumps(tunnels_data, indent=2)}")
                        
                        tunnels = tunnels_data.get("tunnels", [])
                        if tunnels:
                            # Get the HTTPS URL
                            for tunnel in tunnels:
                                if tunnel["proto"] == "https":
                                    self.public_url = tunnel["public_url"]
                                    logger.info(f"ngrok tunnel started: {self.public_url}")
                                    print(f"\n🌐 ngrok tunnel started: {self.public_url}")
                                    
                                    # Construct webhook URL
                                    webhook_url = f"{self.public_url}/webhook"
                                    logger.info(f"Webhook URL: {webhook_url}")
                                    print(f"Webhook URL: {webhook_url}")
                                    return webhook_url
                        else:
                            logger.warning(f"No tunnels found in ngrok API response (retry {retry_count+1}/{max_retries})")
                    else:
                        logger.warning(f"ngrok API returned status code {response.status_code} (retry {retry_count+1}/{max_retries})")
                    
                    # If we get here, either no tunnels or no HTTPS tunnel
                    retry_count += 1
                    time.sleep(1)
                except requests.RequestException as e:
                    # API not available yet
                    logger.warning(f"ngrok API not available yet: {e} (retry {retry_count+1}/{max_retries})")
                    retry_count += 1
                    time.sleep(1)
            
            # Check if process is still running
            if self.process.poll() is not None:
                stdout, stderr = self.process.communicate()
                logger.error(f"ngrok process exited with code {self.process.returncode}")
                logger.error(f"stdout: {stdout}")
                logger.error(f"stderr: {stderr}")
            
            logger.error("Failed to get ngrok tunnel URL after multiple retries")
            print("\n⚠️ Failed to get ngrok tunnel URL after multiple retries.")
            return None
            
        except Exception as e:
            logger.error(f"Error starting ngrok tunnel: {e}", exc_info=True)
            print(f"\n⚠️ Error starting ngrok tunnel: {e}")
            return None
    
    def stop_tunnel(self) -> bool:
        """
        Stop the ngrok tunnel.
        
        Returns:
            True if successful, False otherwise
        """
        if self.process:
            logger.info("Stopping ngrok tunnel")
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
                self.process = None
                self.public_url = None
                logger.info("ngrok tunnel stopped")
                return True
            except Exception as e:
                logger.error(f"Error stopping ngrok tunnel: {e}", exc_info=True)
                return False
        return True
    
    def get_tunnel_info(self) -> Dict[str, Any]:
        """
        Get information about the current ngrok tunnel.
        
        Returns:
            Dictionary with tunnel information
        """
        if not self.public_url:
            logger.info("get_tunnel_info: No public URL available")
            return {"status": "not_running"}
        
        try:
            response = requests.get("http://localhost:4040/api/tunnels")
            if response.status_code == 200:
                tunnel_info = response.json()
                logger.info(f"Tunnel info: {json.dumps(tunnel_info, indent=2)}")
                return tunnel_info
            else:
                logger.warning(f"Failed to get tunnel info: {response.status_code}")
                return {"status": "error", "message": f"Failed to get tunnel info: {response.status_code}"}
        except requests.RequestException as e:
            logger.warning(f"Failed to get tunnel info: {e}")
            return {"status": "error", "message": f"Failed to get tunnel info: {e}"}
            
    def get_public_url(self) -> Optional[str]:
        """
        Get the current public URL of the ngrok tunnel.
        
        Returns:
            The public URL of the tunnel, or None if not running
        """
        if self.public_url:
            logger.info(f"Using cached public URL: {self.public_url}")
            return self.public_url
            
        try:
            # Try to get tunnel info from ngrok API
            logger.info("Fetching public URL from ngrok API")
            response = requests.get("http://localhost:4040/api/tunnels")
            if response.status_code == 200:
                tunnels_data = response.json()
                tunnels = tunnels_data.get("tunnels", [])
                if tunnels:
                    # Get the HTTPS URL
                    for tunnel in tunnels:
                        if tunnel["proto"] == "https":
                            self.public_url = tunnel["public_url"]
                            logger.info(f"Found public URL: {self.public_url}")
                            return self.public_url
                logger.warning("No HTTPS tunnels found in ngrok API response")
            else:
                logger.warning(f"ngrok API returned status code {response.status_code}")
        except requests.RequestException as e:
            logger.warning(f"Failed to get public URL: {e}")
            
        return None