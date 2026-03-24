# web_server.py - HTTP server for web configuration interface
import socket
import ujson
import time
from .html_template import get_html_template
from ..robot_config import save_config_fixed

def handle_request(client_socket, config):
    """Handle HTTP requests"""
    try:
        request = client_socket.recv(1024).decode()
        
        if 'GET /api/config' in request:
            # Return JSON configuration
            response = ujson.dumps(config)
            client_socket.send('HTTP/1.1 200 OK\n')
            client_socket.send('Content-Type: application/json\n')
            client_socket.send('Access-Control-Allow-Origin: *\n')
            client_socket.send(f'Content-Length: {len(response)}\n\n')
            client_socket.send(response)
            
        elif 'POST /api/config' in request:
            # Handle configuration update
            try:
                # Parse POST data (handle multipart form data)
                body_start = request.find('\r\n\r\n') + 4
                if body_start > 3:
                    body = request[body_start:]
                    print(f"Received POST body: {body[:200]}...")  # Debug
                    
                    # Handle multipart form data - look for JSON content
                    json_start = body.find('{"')
                    if json_start != -1:
                        # Find the end of JSON properly - look for matching closing brace
                        brace_count = 0
                        json_end = json_start
                        
                        for i in range(json_start, len(body)):
                            char = body[i]
                            if char == '{':
                                brace_count += 1
                            elif char == '}':
                                brace_count -= 1
                                if brace_count == 0:
                                    json_end = i + 1
                                    break
                        
                        if json_end > json_start:
                            robots_json = body[json_start:json_end]
                            print(f"Parsed robots JSON: {robots_json}")  # Debug
                            
                            robots_data = ujson.loads(robots_json)
                            
                            # Validate MAC addresses and convert to bytes format
                            robot_names = {}
                            updated_robots_data = {}
                            
                            for mac_key, robot_info in robots_data.items():
                                if isinstance(robot_info, dict) and 'name' in robot_info:
                                    # New format with MAC address
                                    mac_from_form = robot_info.get('mac', '').replace(':', '')
                                    mac_bytes = bytes.fromhex(mac_from_form)
                                    robot_names[mac_bytes] = robot_info['name']
                                    # Update the key to match the MAC from form
                                    updated_robots_data[mac_from_form] = robot_info
                                elif isinstance(robot_info, str):
                                    # Backward compatibility - old format
                                    mac_bytes = bytes.fromhex(mac_key)
                                    robot_names[mac_bytes] = robot_info
                                    updated_robots_data[mac_key] = robot_info
                            
                            print(f"Saving robot names: {robot_names}")  # Debug
                            
                            if save_config_fixed(robot_names, updated_robots_data):
                                print("save_config_fixed called successfully!")  # Debug
                                # Update the config variable with new data
                                config['robots'] = {}
                                for mac_bytes, name in robot_names.items():
                                    mac_hex = mac_bytes.hex()
                                    # Use the original MAC from updated_robots_data
                                    original_mac = ':'.join([mac_hex[i:i+2] for i in range(0, len(mac_hex), 2)])
                                    for mac_key, robot_info in updated_robots_data.items():
                                        if mac_key == mac_hex:
                                            original_mac = robot_info.get('mac', original_mac)
                                            break
                                    config['robots'][mac_hex] = {
                                        'name': name,
                                        'mac': original_mac
                                    }
                                
                                response = ujson.dumps({"success": True})
                                print("Save successful")  # Debug
                            else:
                                response = ujson.dumps({"success": False, "error": "Save failed"})
                                print("Save failed")  # Debug
                        else:
                            response = ujson.dumps({"success": False, "error": "Invalid JSON format"})
                            print("Invalid JSON format - no end found")  # Debug
                    else:
                        response = ujson.dumps({"success": False, "error": "No JSON data found"})
                        print("No JSON data found in POST")  # Debug
                else:
                    response = ujson.dumps({"success": False, "error": "No data received"})
                    print("No data in POST request")  # Debug
                    
                client_socket.send('HTTP/1.1 200 OK\n')
                client_socket.send('Content-Type: application/json\n')
                client_socket.send('Access-Control-Allow-Origin: *\n')
                client_socket.send(f'Content-Length: {len(response)}\n\n')
                client_socket.send(response)
                
            except Exception as e:
                error_response = ujson.dumps({"success": False, "error": str(e)})
                client_socket.send('HTTP/1.1 400 Bad Request\n')
                client_socket.send('Content-Type: application/json\n')
                client_socket.send(f'Content-Length: {len(error_response)}\n\n')
                client_socket.send(error_response)
                
        else:
            # Serve HTML page
            html = get_html_template()
            client_socket.send('HTTP/1.1 200 OK\n')
            client_socket.send('Content-Type: text/html\n')
            client_socket.send(f'Content-Length: {len(html)}\n\n')
            client_socket.send(html)
            
    except Exception as e:
        print(f"Error handling request: {e}")
    finally:
        client_socket.close()

def setup_server_socket():
    """Setup and configure server socket"""
    addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
    server_socket = socket.socket()
    
    # Set socket options to allow reuse of address
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server_socket.bind(addr)
    except OSError as e:
        if e.errno == 112:  # EADDRINUSE
            print("Port 80 already in use, trying to close existing socket...")
            # Try to create a new socket with different approach
            server_socket.close()
            time.sleep(0.5)
            server_socket = socket.socket()
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind(addr)
        else:
            raise e
    
    server_socket.listen(1)
    server_socket.setblocking(False)
    
    return server_socket

def check_client_connections(server_socket, config, last_check_time):
    """Check for and handle client connections"""
    current_time = time.ticks_ms()
    
    if time.ticks_diff(current_time, last_check_time) > 100:
        try:
            client_socket, client_addr = server_socket.accept()
            print(f"Client connected from {client_addr}")
            handle_request(client_socket, config)
            return current_time
        except:
            pass  # No client waiting
    
    return last_check_time
