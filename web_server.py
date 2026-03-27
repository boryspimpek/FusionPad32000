# web_server.py - HTTP server for web configuration interface
import socket
import time

def handle_request(client_socket, config):
    """Handle HTTP requests"""

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
