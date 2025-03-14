# import asyncio
# import json
# import logging
# import os
# import platform
# import shutil
# import sqlite3
# from pathlib import Path
#
# import jwt
# import requests
#

#
# class Cursor:
#     def __init__(self, log_level=logging.INFO):
#         """Initialize the Cursor class with optional log level configuration."""
#         logging.basicConfig(level=log_level)
#         self.logger = logging.getLogger("Cursor")
#         self.api_base_url = "https://cursor.com"
#
#     def log(self, message, is_error=False):
#         """Log messages with appropriate level."""
#         if is_error:
#             self.logger.error(message)
#         else:
#             self.logger.debug(message)
#
#     def get_windows_username(self):
#         """Get Windows username when running in WSL environment."""
#         try:
#             import subprocess
#
#             result = subprocess.run(["cmd.exe", "/c", "echo", "%USERNAME%"], capture_output=True, text=True)
#             return result.stdout.strip()
#         except Exception as e:
#             self.log(f"Error getting Windows username: {e}", True)
#             return None
#
#     def is_installed(self):
#         """Check if Cursor is installed on the system.
#
#         Returns:
#             bool: True if installed, False otherwise
#         """
#         # Check if the database path exists
#         db_path = self.get_cursor_db_path()
#         if not os.path.exists(db_path):
#             self.log("Cursor database not found", True)
#             return False
#
#         # Check if the Cursor binary is installed
#         binary_path = self._get_binary_path()
#         if binary_path and not binary_path.exists():
#             self.log("Cursor binary not found", True)
#             return False
#
#         return True
#
#     def _get_binary_path(self):
#         """Get the path to the Cursor binary based on platform."""
#         try:
#             app_name = os.environ.get("VSCODE_APP_NAME", "")
#             folder_name = "Cursor Nightly" if app_name == "Cursor Nightly" else "Cursor"
#
#             if platform.system() == "Windows":
#                 # Check in Program Files
#                 program_files = os.environ.get("ProgramFiles", "C:\\Program Files")
#                 path = Path(program_files) / folder_name / "Cursor.exe"
#                 if path.exists():
#                     return path
#
#                 # Check in PATH
#                 cursor_path = shutil.which("cursor.exe")
#                 if cursor_path:
#                     return Path(cursor_path)
#
#             elif platform.system() == "Darwin":  # macOS
#                 # Check in Applications
#                 path = Path(f"/Applications/{folder_name}.app/Contents/MacOS/Cursor")
#                 if path.exists():
#                     return path
#
#                 # Check in PATH
#                 cursor_path = shutil.which("cursor")
#                 if cursor_path:
#                     return Path(cursor_path)
#
#             else:  # Linux and others
#                 # Check in common locations
#                 paths = [Path(f"/usr/bin/{folder_name.lower()}"), Path(f"/usr/local/bin/{folder_name.lower()}"), Path(os.path.expanduser(f"~/.local/bin/{folder_name.lower()}"))]
#
#                 for path in paths:
#                     if path.exists():
#                         return path
#
#                 # Check in PATH
#                 cursor_path = shutil.which(folder_name.lower())
#                 if cursor_path:
#                     return Path(cursor_path)
#
#             return None
#         except Exception as error:
#             self.log(f"Error finding Cursor binary: {error}", True)
#             return None
#
#     def get_cursor_db_path(self):
#         """Determine the path to the Cursor database based on the current platform."""
#         app_name = os.environ.get("VSCODE_APP_NAME", "")
#         folder_name = "Cursor Nightly" if app_name == "Cursor Nightly" else "Cursor"
#
#         if platform.system() == "Windows":
#             return os.path.join(os.environ.get("APPDATA", ""), folder_name, "User", "globalStorage", "state.vscdb")
#         elif platform.system() == "Linux":
#             is_wsl = os.environ.get("VSCODE_REMOTE_NAME") == "wsl"
#             if is_wsl:
#                 windows_username = self.get_windows_username()
#                 if windows_username:
#                     return os.path.join("/mnt/c/Users", windows_username, "AppData/Roaming", folder_name, "User/globalStorage/state.vscdb")
#             return os.path.join(os.path.expanduser("~"), ".config", folder_name, "User", "globalStorage", "state.vscdb")
#         elif platform.system() == "Darwin":  # macOS
#             return os.path.join(os.path.expanduser("~"), "Library", "Application Support", folder_name, "User", "globalStorage", "state.vscdb")
#
#         # Default fallback
#         return os.path.join(os.path.expanduser("~"), ".config", folder_name, "User", "globalStorage", "state.vscdb")
#
#     async def read_auth_token(self):
#         """Retrieve and process the Cursor authentication token from the database."""
#         try:
#             db_path = self.get_cursor_db_path()
#
#             self.log(f"Platform: {platform.system()}")
#             self.log(f"Home directory: {os.path.expanduser('~')}")
#             self.log(f"Attempting to open database at: {db_path}")
#             self.log(f"Database path exists: {os.path.exists(db_path)}")
#
#             if not os.path.exists(db_path):
#                 self.log("Database file does not exist", True)
#                 return None
#
#             # Connect to SQLite database
#             conn = sqlite3.connect(db_path)
#             cursor = conn.cursor()
#
#             self.log("Successfully opened database connection")
#             self.log("Executing SQL query for token...")
#
#             cursor.execute("SELECT value FROM ItemTable WHERE key = 'cursorAuth/accessToken'")
#             result = cursor.fetchone()
#
#             if not result:
#                 self.log("No token found in database")
#                 conn.close()
#                 return None
#
#             token = result[0]
#             self.log(f"Token length: {len(token)}")
#             self.log(f"Token starts with: {token[:20]}...")
#
#             try:
#                 decoded = jwt.decode(token, options={"verify_signature": False})
#                 self.log(f"JWT decoded successfully: {bool(decoded)}")
#                 self.log(f"JWT payload exists: {bool(decoded)}")
#                 self.log(f"JWT sub exists: {bool(decoded and 'sub' in decoded)}")
#
#                 if not decoded or "sub" not in decoded:
#                     self.log(f"Invalid JWT structure: {decoded}", True)
#                     conn.close()
#                     return None
#
#                 sub = str(decoded["sub"])
#                 self.log(f"Sub value: {sub}")
#                 user_id = sub.split("|")[1]
#                 self.log(f"Extracted userId: {user_id}")
#                 session_token = f"{user_id}%3A%3A{token}"
#                 self.log(f"Created session token, length: {len(session_token)}")
#                 conn.close()
#                 return session_token
#             except Exception as error:
#                 self.log(f"Error processing token: {error}", True)
#                 self.log(f"Error details: {error.__class__.__name__}, {error!s}", True)
#                 conn.close()
#                 return None
#         except Exception as error:
#             self.log(f"Error opening database: {error}", True)
#             self.log(f"Database error details: {error!s}", True)
#             return None
#
#     async def get_user_info(self):
#         """Get user information using the auth token.
#
#         Returns:
#             dict: User information if successful, None otherwise
#         """
#         token = await self.read_auth_token()
#         if not token:
#             self.log("No auth token available", True)
#             return None
#
#         try:
#             headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
#
#             response = requests.get(f"{self.api_base_url}/api/v1/user", headers=headers)
#
#             if response.status_code == 200:
#                 user_data = response.json()
#                 self.log(f"Successfully retrieved user info: {user_data}")
#                 return user_data
#             else:
#                 self.log(f"Failed to get user info: {response.status_code}", True)
#                 self.log(f"Response: {response.text}", True)
#                 return None
#
#         except Exception as error:
#             self.log(f"Error getting user info: {error}", True)
#             self.log(f"Error details: {error.__class__.__name__}, {error!s}", True)
#             return None
#
#     async def validate_token(self):
#         """Validate if the current token is valid."""
#         user_info = await self.get_user_info()
#         return user_info is not None
#
#     def get_cursor_storage_path(self):
#         """Determine the path to the Cursor storage directory based on the current platform."""
#         app_name = os.environ.get("VSCODE_APP_NAME", "")
#         folder_name = "Cursor Nightly" if app_name == "Cursor Nightly" else "Cursor"
#
#         if platform.system() == "Windows":
#             return os.path.join(os.environ.get("APPDATA", ""), folder_name, "User", "workspaceStorage")
#         elif platform.system() == "Linux":
#             is_wsl = os.environ.get("VSCODE_REMOTE_NAME") == "wsl"
#             if is_wsl:
#                 windows_username = self.get_windows_username()
#                 if windows_username:
#                     return os.path.join("/mnt/c/Users", windows_username, "AppData/Roaming", folder_name, "User/workspaceStorage")
#             return os.path.join(os.path.expanduser("~"), ".config", folder_name, "User", "workspaceStorage")
#         elif platform.system() == "Darwin":  # macOS
#             return os.path.join(os.path.expanduser("~"), "Library", "Application Support", folder_name, "User", "workspaceStorage")
#
#         # Default fallback
#         return os.path.join(os.path.expanduser("~"), ".config", folder_name, "User", "workspaceStorage")
#
#     def get_global_storage_path(self):
#         """Determine the path to the Cursor global storage directory."""
#         app_name = os.environ.get("VSCODE_APP_NAME", "")
#         folder_name = "Cursor Nightly" if app_name == "Cursor Nightly" else "Cursor"
#
#         if platform.system() == "Windows":
#             return os.path.join(os.environ.get("APPDATA", ""), folder_name, "User", "globalStorage", "state.vscdb")
#         elif platform.system() == "Linux":
#             is_wsl = os.environ.get("VSCODE_REMOTE_NAME") == "wsl"
#             if is_wsl:
#                 windows_username = self.get_windows_username()
#                 if windows_username:
#                     return os.path.join("/mnt/c/Users", windows_username, "AppData/Roaming", folder_name, "User/globalStorage/state.vscdb")
#             return os.path.join(os.path.expanduser("~"), ".config", folder_name, "User", "globalStorage", "state.vscdb")
#         elif platform.system() == "Darwin":  # macOS
#             return os.path.join(os.path.expanduser("~"), "Library", "Application Support", folder_name, "User", "globalStorage", "state.vscdb")
#
#         # Default fallback
#         return os.path.join(os.path.expanduser("~"), ".config", folder_name, "User", "globalStorage", "state.vscdb")
#
#     async def get_workspaces(self):
#         """Get all workspaces from the Cursor storage directory."""
#         try:
#             workspace_path = self.get_cursor_storage_path()
#             self.log(f"Looking for workspaces in: {workspace_path}")
#
#             workspaces = []
#             workspace_dir = Path(workspace_path)
#
#             if not workspace_dir.exists():
#                 self.log(f"Workspace directory does not exist: {workspace_path}", True)
#                 return []
#
#             for entry in workspace_dir.iterdir():
#                 if entry.is_dir():
#                     db_path = entry.joinpath("state.vscdb")
#                     workspace_json_path = entry.joinpath("workspace.json")
#
#                     # Skip if state.vscdb doesn't exist
#                     if not db_path.exists():
#                         self.log(f"Skipping {entry.name}: no state.vscdb found")
#                         continue
#
#                     workspace_info = {"id": entry.name, "path": str(entry), "dbPath": str(db_path)}
#
#                     # Try to get workspace name from workspace.json if it exists
#                     if workspace_json_path.exists():
#                         try:
#                             workspace_data = json.loads(workspace_json_path.read_text())
#                             if "folder" in workspace_data:
#                                 workspace_info["name"] = Path(workspace_data["folder"]).name
#                         except Exception as e:
#                             self.log(f"Error reading workspace.json: {e}", True)
#
#                     if "name" not in workspace_info:
#                         workspace_info["name"] = entry.name
#
#                     workspaces.append(workspace_info)
#
#             return workspaces
#
#         except Exception as e:
#             self.log(f"Failed to get workspaces: {e}", True)
#             return []
#
#     async def get_workspace_chat_data(self, workspace_id: str):
#         """Get chat data for a specific workspace."""
#         try:
#             workspace_path = self.get_cursor_storage_path()
#             db_path = os.path.join(workspace_path, workspace_id, "state.vscdb")
#
#             if not os.path.exists(db_path):
#                 self.log(f"Database does not exist: {db_path}", True)
#                 return None
#
#             # Connect to SQLite database
#             conn = sqlite3.connect(db_path)
#             conn.row_factory = sqlite3.Row  # This allows accessing columns by name
#             cursor = conn.cursor()
#
#             # First, check what tables exist in the database
#             cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
#             tables = [table[0] for table in cursor.fetchall()]
#             self.log(f"Tables in database: {tables}")
#
#             response = {}
#
#             # Determine the correct table name (ItemTable or Item)
#             item_table = "ItemTable" if "ItemTable" in tables else "Item"
#
#             # Get chat data
#             try:
#                 # Look for chat data with different possible key patterns
#                 chat_keys = ["workbench.panel.aichat.view.aichat.chatdata", "workbench.panel.chat.view.chat.chatdata", "workbench.view.chat.chatdata"]
#
#                 chat_result = None
#                 for chat_key in chat_keys:
#                     cursor.execute(f"SELECT value FROM {item_table} WHERE key = ?", (chat_key,))
#                     chat_result = cursor.fetchone()
#                     if chat_result:
#                         self.log(f"Found chat data with key: {chat_key}")
#                         break
#
#                 # Look for composer data
#                 composer_keys = ["composer.composerData", "cursor.composerData"]
#
#                 composer_result = None
#                 for composer_key in composer_keys:
#                     cursor.execute(f"SELECT value FROM {item_table} WHERE key = ?", (composer_key,))
#                     composer_result = cursor.fetchone()
#                     if composer_result:
#                         self.log(f"Found composer data with key: {composer_key}")
#                         break
#             except Exception as e:
#                 self.log(f"Error querying database: {e}", True)
#                 chat_result = None
#                 composer_result = None
#
#             conn.close()
#
#             # Process chat data
#             if chat_result:
#                 try:
#                     chat_data = json.loads(chat_result["value"])
#                     response["chats"] = chat_data
#                     self.log(f"Successfully parsed chat data with {len(chat_data.get('tabs', []))} tabs")
#                 except json.JSONDecodeError as e:
#                     self.log(f"Error parsing chat data: {e}", True)
#             else:
#                 self.log("No chat data found in database")
#
#             # Process composer data
#             if composer_result:
#                 try:
#                     composers = json.loads(composer_result["value"])
#                     self.log(f"Found {len(composers.get('allComposers', []))} composers")
#                     response["composers"] = composers
#                 except json.JSONDecodeError as e:
#                     self.log(f"Error parsing composer data: {e}", True)
#             else:
#                 self.log("No composer data found in database")
#
#             return response
#
#         except Exception as e:
#             self.log(f"Failed to get workspace data: {e}", True)
#             import traceback
#
#             self.log(traceback.format_exc(), True)
#             return None
#
#     async def search_chat_history(self, query: str, search_type: str = "all"):
#         """Search across all workspaces for chat history matching the query.
#
#         Args:
#             query: The search term to look for
#             search_type: Type of logs to search - 'all', 'chat', or 'composer'
#
#         Returns:
#             list: List of search results with matching content
#         """
#         try:
#             if not query:
#                 self.log("No search query provided", True)
#                 return []
#
#             results = []
#             workspaces = await self.get_workspaces()
#
#             for workspace in workspaces:
#                 workspace_id = workspace["id"]
#
#                 try:
#                     workspace_data = await self.get_workspace_chat_data(workspace_id)
#                     if not workspace_data:
#                         continue
#
#                     # Search in chat data
#                     if search_type in ["all", "chat"] and "chats" in workspace_data:
#                         chat_data = workspace_data["chats"]
#                         for tab in chat_data.get("tabs", []):
#                             has_match = False
#                             matching_text = ""
#
#                             # Search in chat title
#                             if tab.get("chatTitle", "").lower().find(query.lower()) != -1:
#                                 has_match = True
#                                 matching_text = tab.get("chatTitle", "")
#
#                             # Search in bubbles/messages
#                             if not has_match:
#                                 for bubble in tab.get("bubbles", []):
#                                     if bubble.get("text", "").lower().find(query.lower()) != -1:
#                                         has_match = True
#                                         matching_text = bubble.get("text", "")
#                                         break
#
#                             if has_match:
#                                 results.append(
#                                     {
#                                         "workspaceId": workspace_id,
#                                         "workspaceName": workspace.get("name", workspace_id),
#                                         "chatId": tab.get("tabId", ""),
#                                         "chatTitle": tab.get("chatTitle", f"Chat {tab.get('tabId', '')[:8]}"),
#                                         "timestamp": tab.get("lastSendTime", ""),
#                                         "matchingText": matching_text,
#                                         "type": "chat",
#                                     }
#                                 )
#
#                     # Search in composer data
#                     if search_type in ["all", "composer"] and "composers" in workspace_data:
#                         composer_data = workspace_data["composers"]
#                         for composer in composer_data.get("allComposers", []):
#                             has_match = False
#                             matching_text = ""
#
#                             # Search in composer text/title
#                             if composer.get("text", "").lower().find(query.lower()) != -1:
#                                 has_match = True
#                                 matching_text = composer.get("text", "")
#
#                             # Search in conversation
#                             if not has_match and "conversation" in composer:
#                                 for message in composer.get("conversation", []):
#                                     if message.get("text", "").lower().find(query.lower()) != -1:
#                                         has_match = True
#                                         matching_text = message.get("text", "")
#                                         break
#
#                             if has_match:
#                                 results.append(
#                                     {
#                                         "workspaceId": workspace_id,
#                                         "workspaceName": workspace.get("name", workspace_id),
#                                         "chatId": composer.get("composerId", ""),
#                                         "chatTitle": composer.get("text", f"Composer {composer.get('composerId', '')[:8]}"),
#                                         "timestamp": composer.get("lastUpdatedAt", composer.get("createdAt", "")),
#                                         "matchingText": matching_text,
#                                         "type": "composer",
#                                     }
#                                 )
#
#                 except Exception as e:
#                     self.log(f"Error searching workspace {workspace_id}: {e}", True)
#
#             # Sort results by timestamp, newest first
#             results.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
#             return results
#
#         except Exception as e:
#             self.log(f"Failed to search chat history: {e}", True)
#             return []
#
#
# async def main():
#     cursor = Cursor(log_level=logging.DEBUG)
#
#     # Check if Cursor is installed
#     if not cursor.is_installed():
#         print("Cursor is not installed or not properly configured")
#         return
#
#     token = await cursor.read_auth_token()
#     print(f"Token: {token}")
#
#     # Get all workspaces
#     workspaces = await cursor.get_workspaces()
#     print(f"Found {len(workspaces)} workspaces:")
#     for workspace in workspaces:
#         print(f"  - {workspace['name']} ({workspace['id']})")
#
#     # If workspaces were found, get chat data for the first one
#     if workspaces:
#         for workspace in workspaces:
#             workspace_id = workspace["id"]
#             print(f"\nGetting chat data for workspace: {workspace['name']}")
#
#             chat_data = await cursor.get_workspace_chat_data(workspace_id)
#
#             if chat_data:
#                 # Print summary of chat data
#                 if "chats" in chat_data:
#                     chats = chat_data["chats"]
#                     print(f"\nFound {len(chats.get('tabs', []))} chat tabs")
#
#                     for i, tab in enumerate(chats.get("tabs", [])):
#                         bubbles = tab.get("bubbles", [])
#                         print(f"  - Tab {i + 1}: {tab.get('chatTitle', 'Untitled')} ({len(bubbles)} messages)")
#
#                         # Print a sample of messages from this chat
#                         if bubbles:
#                             print("    Sample messages:")
#                             for j, bubble in enumerate(bubbles[:3]):  # Show first 3 messages
#                                 msg_type = "AI" if bubble.get("type") == "ai" else "User"
#                                 text = bubble.get("text", "")
#                                 # Truncate long messages
#                                 if len(text) > 100:
#                                     text = text[:97] + "..."
#                                 print(f"      {msg_type}: {text}")
#                             if len(bubbles) > 3:
#                                 print(f"      ... and {len(bubbles) - 3} more messages")
#
#                 # Print summary of composer data
#                 if "composers" in chat_data:
#                     composers = chat_data["composers"]
#                     print(f"\nFound {len(composers.get('allComposers', []))} composers")
#
#                     for i, composer in enumerate(composers.get("allComposers", [])):
#                         conversation = composer.get("conversation", [])
#                         print(f"  - Composer {i + 1}: {composer.get('text', 'Untitled')} ({len(conversation)} messages)")
#
#                         # Print a sample of messages from this composer
#                         if conversation:
#                             print("    Sample messages:")
#                             for j, message in enumerate(conversation[:3]):  # Show first 3 messages
#                                 msg_type = "AI" if message.get("type") == 2 else "User"
#                                 text = message.get("text", "")
#                                 # Truncate long messages
#                                 if len(text) > 100:
#                                     text = text[:97] + "..."
#                                 print(f"      {msg_type}: {text}")
#                             if len(conversation) > 3:
#                                 print(f"      ... and {len(conversation) - 3} more messages")
#             else:
#                 print("No chat data found for this workspace")
#     else:
#         print("No workspaces found")
#
#     # Search for chat history
#     search_query = "def"  # Example search term
#     print(f"\nSearching chat history for '{search_query}'...")
#     search_results = await cursor.search_chat_history(search_query)
#
#     if search_results:
#         print(f"Found {len(search_results)} results:")
#         for i, result in enumerate(search_results[:10]):  # Show first 10 results
#             print(f"  {i + 1}. [{result['type']}] {result['chatTitle']} ({result['workspaceName']})")
#             # Show a snippet of the matching text
#             matching_text = result["matchingText"]
#             if len(matching_text) > 100:
#                 matching_text = matching_text[:97] + "..."
#             print(f"     Match: {matching_text}")
#     else:
#         print("No search results found")
#
#
# if __name__ == "__main__":
#     # For testing - lets pull prompts and responses from local cursor db
#     asyncio.run(main())
