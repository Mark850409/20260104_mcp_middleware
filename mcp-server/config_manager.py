
import os
import json
import logging
import pymysql
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

class MCPConfigManager:
    def __init__(self, config_path="configs/mcp_servers.json"):
        self.config_path = config_path
        self.db_config = {
            'host': os.getenv('DB_HOST', 'db'),
            'port': int(os.getenv('DB_PORT', '3306')),
            'user': os.getenv('DB_USER', 'mcp_user'),
            'password': os.getenv('DB_PASSWORD', 'mcp_password'),
            'database': os.getenv('DB_NAME', 'mcp_platform'),
            'charset': 'utf8mb4',
            'cursorclass': pymysql.cursors.DictCursor
        }
        self.use_db = True  # Default to verify DB connection

    def _get_db_connection(self):
        try:
            return pymysql.connect(**self.db_config)
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return None

    def load_config(self):
        """
        Load configuration from database, fallback to JSON file if DB fails
        """
        config = {"mcpServers": {}}
        
        if self.use_db:
            conn = self._get_db_connection()
            if conn:
                try:
                    with conn.cursor() as cursor:
                        cursor.execute("SELECT name, description, command, args, env, type, enabled, url, headers FROM mcp_servers")
                        servers = cursor.fetchall()
                        
                        for server in servers:
                            config["mcpServers"][server['name']] = {
                                "command": server['command'],
                                "args": json.loads(server['args']) if isinstance(server['args'], str) else server['args'],
                                "env": json.loads(server['env']) if isinstance(server['env'], str) and server['env'] else {},
                                "type": server['type'],
                                "enabled": bool(server['enabled']),
                                "description": server['description'],
                                "url": server.get('url'),
                                "headers": json.loads(server['headers']) if isinstance(server.get('headers'), str) and server['headers'] else {}
                            }
                    logger.info(f"Loaded {len(config['mcpServers'])} servers from database")
                    return config
                except Exception as e:
                    logger.error(f"Failed to load from DB: {e}")
                finally:
                    conn.close()

        # Fallback to JSON file
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading config file: {e}")
        
        return config

    def save_config(self, config):
        """
        Save configuration to database (sync) and JSON file
        """
        # Save to JSON file as backup
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving to JSON file: {e}")

    def add_server(self, name, server_config):
        """
        Add a new server to the database
        """
        # Validate first
        self.validate_server_config(server_config)
        
        conn = self._get_db_connection()
        if conn:
            try:
                with conn.cursor() as cursor:
                    sql = """
                        INSERT INTO mcp_servers (name, description, command, args, env, type, enabled, url, headers)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    cursor.execute(sql, (
                        name,
                        server_config.get('description', ''),
                        server_config.get('command', ''),  # Default to empty string
                        json.dumps(server_config.get('args', [])),
                        json.dumps(server_config.get('env', {})),
                        server_config.get('type', 'python'),
                        server_config.get('enabled', True),
                        server_config.get('url', ''),
                        json.dumps(server_config.get('headers', {}))
                    ))
                conn.commit()
                logger.info(f"Added server '{name}' to database")
            except pymysql.err.IntegrityError as e:
                # 1062 is Duplicate entry code
                if e.args[0] == 1062:
                    logger.warning(f"Server '{name}' already exists")
                    raise ValueError(f"Server with name '{name}' already exists")
                logger.error(f"Database integrity error: {e}")
                raise
            except Exception as e:
                logger.error(f"Failed to add server to DB: {e}")
                raise
            finally:
                conn.close()
        
        # Sync with JSON
        try:
            current_config = self.load_config()
            self.save_config(current_config)
        except Exception as sync_error:
            logger.error(f"Syncing DB to JSON failed, but DB update was successful: {sync_error}")
            # Do not raise, DB update is the primary success
        # This technically re-saves what we just loaded, effectively syncing if load_config works. 
        # Actually load_config reads from DB, so save_config(load_config()) syncs DB -> JSON.

    def update_server(self, name, server_config):
        """
        Update an existing server in the database
        """
        self.validate_server_config(server_config)
        
        conn = self._get_db_connection()
        if conn:
            try:
                with conn.cursor() as cursor:
                    sql = """
                        UPDATE mcp_servers 
                        SET description=%s, command=%s, args=%s, env=%s, type=%s, enabled=%s, url=%s, headers=%s
                        WHERE name=%s
                    """
                    cursor.execute(sql, (
                        server_config.get('description', ''),
                        server_config.get('command', ''),
                        json.dumps(server_config.get('args', [])),
                        json.dumps(server_config.get('env', {})),
                        server_config.get('type', 'python'),
                        server_config.get('enabled', True),
                        server_config.get('url', ''),
                        json.dumps(server_config.get('headers', {})),
                        name
                    ))
                conn.commit()
                logger.info(f"Updated server '{name}' in database")
            except Exception as e:
                logger.error(f"Failed to update server in DB: {e}")
                raise
            finally:
                conn.close()
        
        # Sync
        try:
            self.save_config(self.load_config())
        except Exception as sync_error:
            logger.error(f"Syncing DB to JSON failed, but DB update was successful: {sync_error}")

    def delete_server(self, name):
        """
        Delete a server from the database
        """
        conn = self._get_db_connection()
        if conn:
            try:
                with conn.cursor() as cursor:
                    cursor.execute("DELETE FROM mcp_servers WHERE name=%s", (name,))
                conn.commit()
                logger.info(f"Deleted server '{name}' from database")
            except Exception as e:
                logger.error(f"Failed to delete server from DB: {e}")
                raise
            finally:
                conn.close()
        
        # Sync
        try:
            self.save_config(self.load_config())
        except Exception as sync_error:
            logger.error(f"Syncing DB to JSON failed, but DB update was successful: {sync_error}")
    
    def toggle_server(self, name, enabled):
        """
        Toggle server enabled status
        """
        conn = self._get_db_connection()
        if conn:
            try:
                with conn.cursor() as cursor:
                    cursor.execute("UPDATE mcp_servers SET enabled=%s WHERE name=%s", (enabled, name))
                conn.commit()
            except Exception as e:
                logger.error(f"Failed to toggle server in DB: {e}")
                raise
            finally:
                conn.close()
        # Sync
        try:
            self.save_config(self.load_config())
        except Exception as sync_error:
            logger.error(f"Syncing DB to JSON failed, but DB update was successful: {sync_error}")
        return True
        
    def validate_server_config(self, config):
        """
        Validate server configuration
        """
        if 'command' not in config:
            # Allow missing command for SSE/remote types
            if config.get('type') in ['sse', 'remote']:
                pass
            else:
                raise ValueError("Configuration must contain 'command'")
        if 'args' in config and not isinstance(config['args'], list):
            # If args is not a list, try to parse it if it's a JSON string, otherwise error
            if isinstance(config['args'], str):
                try:
                    config['args'] = json.loads(config['args'])
                except:
                    raise ValueError("'args' must be a list")
            else:
                raise ValueError("'args' must be a list")

    def export_config(self):
        """Export current configuration as dictionary"""
        return self.load_config()

    def import_config(self, config_data, overwrite=False):
        """
        Import configuration from dictionary
        """
        if "mcpServers" not in config_data:
            raise ValueError("Invalid config format: missing 'mcpServers' key")
            
        results = {"success": 0, "failed": 0, "skipped": 0, "errors": []}
        
        new_servers = config_data["mcpServers"]
        current_servers = self.load_config().get("mcpServers", {})
        
        for name, config in new_servers.items():
            try:
                exists = name in current_servers
                if exists and not overwrite:
                    results["skipped"] += 1
                    continue
                
                # Ensure type is set
                if "type" not in config:
                    # Auto-detect type
                    cmd = config.get("command", "")
                    if cmd in ["node", "npx"]:
                        config["type"] = "nodejs"
                    elif cmd in ["python", "python3", "uvx"]:
                        config["type"] = "python"
                    else:
                        config["type"] = "python" # Default
                
                if exists:
                    self.update_server(name, config)
                else:
                    self.add_server(name, config)
                
                results["success"] += 1
            except Exception as e:
                results["failed"] += 1
                results["errors"].append(f"{name}: {str(e)}")
                
        return results

    def list_servers(self):
        """List all servers"""
        return self.load_config()

    def get_server(self, server_name):
        """Get configuration for a specific server"""
        config = self.load_config()
        return config.get("mcpServers", {}).get(server_name)

    def get_enabled_servers(self):
        """
        Get all enabled servers as a list of dictionaries with 'name' field injected
        """
        config = self.load_config()
        enabled_servers = []
        for name, server_config in config.get("mcpServers", {}).items():
            if server_config.get("enabled", True):
                # Create a copy with name injected
                server_data = server_config.copy()
                server_data['name'] = name
                enabled_servers.append(server_data)
        return enabled_servers

# Initialize global config manager
config_manager = MCPConfigManager()
