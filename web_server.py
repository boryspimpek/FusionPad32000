# web_server.py - HTTP server for web configuration interface
import socket
import time
import uos

def handle_request(client_socket):
    """Handle HTTP requests including file upload"""
    try:
        print("New client connected")
        # Receive request data
        try:
            request_data = client_socket.recv(4096)
            request = request_data.decode('utf-8')
        except:
            # Fallback for encoding issues
            request_data = client_socket.recv(4096)
            request = request_data.decode('utf-8', errors='ignore')
            
        if not request:
            print("No data received")
            return
        
        print(f"Request received: {len(request)} bytes")
        print(f"First line: {request.split(chr(10))[0]}")
        
        # Parse first line to get method and path
        lines = request.split('\r\n')
        if not lines:
            print("No lines in request")
            return
            
        first_line = lines[0]
        parts = first_line.split(' ')
        if len(parts) < 2:
            print(f"Invalid first line: {first_line}")
            return
            
        method = parts[0]
        path = parts[1]
        
        print(f"HTTP {method} {path}")
        
        if method == 'GET' and path == '/':
            # Serve basic info page
            response = "HTTP/1.1 200 OK\r\n"
            response += "Content-Type: text/html\r\n"
            response += "Connection: close\r\n\r\n"
            response += """<html><body>
                <h1>FusionPad Config Server</h1>
                <p>Send JSON files to /upload endpoint</p>
                </body></html>"""
            client_socket.send(response.encode('utf-8'))
            print("GET response sent")
            return
            
        elif method == 'OPTIONS' and path == '/upload':
            # Handle CORS preflight
            response = "HTTP/1.1 200 OK\r\n"
            response += "Access-Control-Allow-Origin: *\r\n"
            response += "Access-Control-Allow-Methods: POST, OPTIONS\r\n"
            response += "Access-Control-Allow-Headers: Content-Type\r\n"
            response += "Connection: close\r\n\r\n"
            client_socket.send(response.encode('utf-8'))
            print("CORS preflight response sent")
            return
            
        elif method == 'POST' and path == '/upload':
            # Handle file upload
            print("Starting POST upload handling")
            content_length = 0
            content_type = ""
            
            # Parse headers
            print(f"Parsing {len(lines)} headers")
            for line in lines[1:]:
                if line.lower().startswith('content-length:'):
                    content_length = int(line.split(':')[1].strip())
                    print(f"Content-Length: {content_length}")
                elif line.lower().startswith('content-type:'):
                    content_type = line.split(':')[1].strip()
                    print(f"Content-Type: {content_type}")
            
            if content_length == 0:
                print("Missing Content-Length header")
                send_error_response(client_socket, "Missing Content-Length")
                return
                
            # Read remaining data
            remaining_data = request.split('\r\n\r\n', 1)
            if len(remaining_data) > 1:
                body = remaining_data[1]
                print(f"Body found in initial request: {len(body)} bytes")
            else:
                # Need to read more data
                print("Need to read more data from socket")
                body = ""
                bytes_received = len(request.split('\r\n\r\n')[0]) + 4
                while len(body) < content_length:
                    chunk = client_socket.recv(1024).decode('utf-8', errors='ignore')
                    if not chunk:
                        break
                    body += chunk
                print(f"Body after reading: {len(body)} bytes")
            
            # Handle different content types
            print(f"Processing content type: {content_type}")
            if 'application/json' in content_type:
                # Direct JSON upload
                print("Processing direct JSON upload")
                success = save_json_file(body, "robot_config.json")
                if success:
                    send_success_response(client_socket, "JSON file saved successfully")
                    return
                else:
                    send_error_response(client_socket, "Failed to save JSON file")
                    return
                    
            elif 'multipart/form-data' in content_type:
                # Multipart form data
                print("Processing multipart form data")
                print(f"Full content-type: {content_type}")
                if 'boundary=' in content_type:
                    boundary = content_type.split('boundary=')[1]
                    print(f"Boundary: {boundary}")
                    success = parse_multipart_and_save(body, boundary)
                    if success:
                        send_success_response(client_socket, "File uploaded successfully")
                        return
                    else:
                        send_error_response(client_socket, "Failed to process upload")
                        return
                else:
                    print("No boundary found in content-type")
                    send_error_response(client_socket, "No boundary in multipart")
                    return
            else:
                print(f"Unsupported content type: {content_type}")
                send_error_response(client_socket, "Unsupported content type")
                return
                
        else:
            send_error_response(client_socket, "Not Found", 404)
            return
            
    except Exception as e:
        print(f"Error handling request: {e}")
        print(f"Exception type: {type(e)}")
        try:
            send_error_response(client_socket, "Internal Server Error", 500)
        except:
            print("Failed to send error response")
    finally:
        try:
            client_socket.close()
            print("Client socket closed")
        except:
            print("Failed to close client socket")

def send_success_response(client_socket, message):
    """Send HTTP success response"""
    response = "HTTP/1.1 200 OK\r\n"
    response += "Content-Type: application/json\r\n"
    response += "Access-Control-Allow-Origin: *\r\n"
    response += "Connection: close\r\n\r\n"
    response += f'{{"status": "success", "message": "{message}"}}'
    client_socket.send(response.encode('utf-8'))

def send_error_response(client_socket, message, code=400):
    """Send HTTP error response"""
    response = f"HTTP/1.1 {code} Error\r\n"
    response += "Content-Type: application/json\r\n"
    response += "Access-Control-Allow-Origin: *\r\n"
    response += "Connection: close\r\n\r\n"
    response += f'{{"status": "error", "message": "{message}"}}'
    client_socket.send(response.encode('utf-8'))

def save_json_file(json_content, filename):
    """Save JSON content to file"""
    try:
        with open(filename, 'w') as f:
            f.write(json_content)
        print(f"File saved: {filename}")
        return True
    except Exception as e:
        print(f"Error saving file: {e}")
        return False

def parse_multipart_and_save(body, boundary):
    """Parse multipart form data and extract JSON file"""
    try:
        parts = body.split(f'--{boundary}')
        
        for part in parts:
            if 'Content-Disposition:' in part and 'filename=' in part:
                # Extract content between headers and next boundary
                content_start = part.find('\r\n\r\n')
                if content_start != -1:
                    content = part[content_start + 4:]
                    # Remove trailing boundary if present
                    content = content.split(f'--{boundary}')[0].strip()
                    
                    if content:
                        return save_json_file(content, "robot_config.json")
        
        return False
    except Exception as e:
        print(f"Error parsing multipart: {e}")
        return False

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

def check_client_connections(server_socket, last_check_time):
    """Check for and handle client connections"""
    current_time = time.ticks_ms()
    
    if time.ticks_diff(current_time, last_check_time) > 100:
        try:
            client_socket, client_addr = server_socket.accept()
            print(f"Client connected from {client_addr}")
            handle_request(client_socket)
            return current_time
        except:
            pass  # No client waiting
    
    return last_check_time
