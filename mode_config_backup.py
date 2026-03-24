# mode_config.py - WiFi Configuration Mode with Web Interface
import network # type: ignore
import socket
import ujson
import time
import machine # type: ignore
import buttons
import ST7735 # type: ignore
import glcdfont
from robot_mode.robot_config import load_config, save_config

# Import save_config directly and create a wrapper that fixes the path
def save_config_fixed(robot_names, robots_data=None):
    """Save robot configuration to JSON file with correct path and MAC addresses"""
    try:
        import ujson
        import os
        
        print(f"save_config_fixed called with: {robot_names}")  # Debug
        
        # Convert bytes MACs to hex strings for JSON serialization
        config_robots = {}
        robot_macs = []
        
        for mac_bytes, name in robot_names.items():
            mac_str = mac_bytes.hex()
            # Use the MAC address from the POST data, not reformatted
            # Look for the MAC in the original robots_data
            original_mac = ':'.join([mac_str[i:i+2] for i in range(0, len(mac_str), 2)])
            if robots_data:
                for mac_key, robot_info in robots_data.items():
                    if mac_key == mac_str:
                        original_mac = robot_info.get('mac', original_mac)
                        break
            
            config_robots[mac_str] = {
                "name": name,
                "mac": original_mac
            }
            robot_macs.append(mac_bytes)
        
        config = {'robots': config_robots}
        
        print(f"About to write config: {config}")  # Debug
        
        # Use correct path - mode_config.py is in root directory
        with open('robot_config.json', 'w') as f:
            ujson.dump(config, f)
            print("File written successfully")  # Debug
        
        # Verify file was written
        with open('robot_config.json', 'r') as f:
            content = f.read()
            print(f"File content after save: {content}")  # Debug
        
        return True
    except Exception as e:
        print(f"Save error details: {e}")  # Debug
        import sys
        print(f"Error type: {type(e)}")
        return False

# Font configuration
FONT = {"Width": 5, "Height": 7, "Start": 32, "End": 122, "Data": glcdfont.font}

# Colors
BLACK = ST7735.TFT.BLACK
WHITE = ST7735.TFT.WHITE
CYAN = ST7735.TFT.CYAN
GREEN = ST7735.TFT.GREEN
RED = ST7735.TFT.RED

def center_x(text, screen_w=160, char_w=6):
    return (screen_w - len(text) * char_w) // 2

def get_html_template():
    """Generate HTML template for configuration page"""
    return """<!DOCTYPE html>
<html>
<head>
    <title>FusionPad Configuration</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f0f0f0; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #333; text-align: center; }
        .robot-config { margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; background: #f9f9f9; }
        .robot-config h3 { margin-top: 0; color: #007bff; }
        .form-group { margin: 10px 0; }
        label { display: block; margin-bottom: 5px; font-weight: bold; }
        input[type="text"] { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; }
        input[type="text"].mac-input { font-family: monospace; }
        input.valid { border-color: #28a745; }
        input.invalid { border-color: #dc3545; background-color: #f8d7da; }
        .btn { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; margin: 5px; }
        .btn:hover { background: #0056b3; }
        .btn-danger { background: #dc3545; }
        .btn-danger:hover { background: #c82333; }
        .btn-success { background: #28a745; }
        .btn-success:hover { background: #218838; }
        .message { padding: 10px; margin: 10px 0; border-radius: 4px; }
        .success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        .robot-actions { text-align: right; margin-top: 10px; }
        .validation-error { color: #dc3545; font-size: 12px; margin-top: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>FusionPad Robot Configuration</h1>
        <div id="robots-container">
            <!-- Robot configurations will be inserted here -->
        </div>
        <div class="robot-actions">
            <button type="button" class="btn btn-success" onclick="addRobot()">Add New Robot</button>
        </div>
        <form id="configForm" style="display: none;">
            <button type="submit" class="btn">Save Configuration</button>
        </form>
        <div id="message"></div>
    </div>

    <script>
        // MAC address validation
        function validateMac(mac) {
            // Accept formats: "5c:01:3b:6c:1c:48" or "5c013b6c1c48"
            const cleanMac = mac.replace(/:/g, '').toLowerCase();
            if (cleanMac.length !== 12) return false;
            
            // Check if all characters are valid hex
            const hexRegex = /^[0-9a-f]+$/;
            return hexRegex.test(cleanMac);
        }

        function formatMac(mac) {
            const cleanMac = mac.replace(/:/g, '').toLowerCase();
            if (cleanMac.length !== 12) return mac;
            
            // Format as 5c:01:3b:6c:1c:48
            return cleanMac.match(/.{2}/g).join(':');
        }

        function validateMacInput(input) {
            const mac = input.value;
            if (validateMac(mac)) {
                input.classList.remove('invalid');
                input.classList.add('valid');
                input.value = formatMac(mac);
                return true;
            } else {
                input.classList.remove('valid');
                input.classList.add('invalid');
                return false;
            }
        }

        function addRobot() {
            const container = document.getElementById('robots-container');
            const robotCount = container.children.length;
            
            const robotDiv = document.createElement('div');
            robotDiv.className = 'robot-config';
            robotDiv.innerHTML = `
                <h3>Robot ${robotCount + 1}</h3>
                <div class="form-group">
                    <label>MAC Address:</label>
                    <input type="text" class="mac-input" name="mac_new_${robotCount}" 
                           placeholder="5c:01:3b:6c:1c:48" 
                           oninput="validateMacInput(this)">
                    <div class="validation-error">Invalid MAC address format</div>
                </div>
                <div class="form-group">
                    <label>Robot Name:</label>
                    <input type="text" name="name_new_${robotCount}" placeholder="Enter robot name">
                </div>
                <div class="robot-actions">
                    <button type="button" class="btn btn-danger" onclick="removeRobot(this)">Remove Robot</button>
                </div>
            `;
            container.appendChild(robotDiv);
        }

        function removeRobot(button) {
            if (confirm('Are you sure you want to remove this robot?')) {
                button.closest('.robot-config').remove();
                updateRobotNumbers();
            }
        }

        function updateRobotNumbers() {
            const container = document.getElementById('robots-container');
            const robots = container.querySelectorAll('.robot-config');
            robots.forEach((robot, index) => {
                const h3 = robot.querySelector('h3');
                if (h3) h3.textContent = `Robot ${index + 1}`;
            });
        }

        // Load current configuration
        fetch('/api/config')
            .then(response => response.json())
            .then(data => {
                const container = document.getElementById('robots-container');
                container.innerHTML = '';
                
                Object.entries(data.robots).forEach(([mac, robotData], index) => {
                    const name = typeof robotData === 'string' ? robotData : robotData.name;
                    const macFormatted = typeof robotData === 'string' ? mac : robotData.mac;
                    
                    const robotDiv = document.createElement('div');
                    robotDiv.className = 'robot-config';
                    robotDiv.innerHTML = `
                        <h3>Robot ${index + 1}</h3>
                        <div class="form-group">
                            <label>MAC Address:</label>
                            <input type="text" class="mac-input" name="mac_${mac}" value="${macFormatted}" 
                                   oninput="validateMacInput(this)">
                            <div class="validation-error">Invalid MAC address format</div>
                        </div>
                        <div class="form-group">
                            <label>Robot Name:</label>
                            <input type="text" name="name_${mac}" value="${name}" placeholder="Enter robot name">
                        </div>
                        <div class="robot-actions">
                            <button type="button" class="btn btn-danger" onclick="removeRobot(this)">Remove Robot</button>
                        </div>
                    `;
                    container.appendChild(robotDiv);
                });
            })
            .catch(error => {
                document.getElementById('message').innerHTML = '<div class="error">Error loading configuration</div>';
            });

        // Handle form submission
        document.getElementById('configForm').addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData();
            const robots = {};
            
            // Collect robot data
            document.querySelectorAll('input[name^="name_"]').forEach(input => {
                const macKey = input.name.replace('name_', '');
                const macInput = document.querySelector(`input[name="mac_${macKey}"]`);
                
                if (macInput && validateMacInput(macInput)) {
                    robots[macKey] = {
                        name: input.value,
                        mac: macInput.value
                    };
                }
            });
            
            formData.append('robots', JSON.stringify(robots));
            
            fetch('/api/config', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                const messageDiv = document.getElementById('message');
                if (data.success) {
                    messageDiv.innerHTML = '<div class="success">Configuration saved successfully!</div>';
                    setTimeout(() => location.reload(), 2000);
                } else {
                    messageDiv.innerHTML = '<div class="error">Error saving configuration</div>';
                }
            })
            .catch(error => {
                document.getElementById('message').innerHTML = '<div class="error">Error saving configuration</div>';
            });
        });

        // Show save button when any input changes
        document.addEventListener('input', function() {
            document.getElementById('configForm').style.display = 'block';
        });
    </script>
</body>
</html>"""

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

def run(tft):
    """Run configuration mode with WiFi AP and web server"""
    # Initialize WiFi AP
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    ap.config(essid='FusionPad-Config', password='')
    
    # Get IP address
    ip = ap.ifconfig()[0]
    
    # Load current configuration
    config = {'robots': {}}
    try:
        robot_names = load_config()
        for mac_bytes, name in robot_names.items():
            config['robots'][mac_bytes.hex()] = name
    except:
        pass
    
    # Setup server socket with error handling
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
    
    # Display connection info
    tft.fill(BLACK)
    tft.text((center_x("CONFIG MODE"), 10), "CONFIG MODE", CYAN, FONT, 1)
    tft.text((center_x("WiFi: FusionPad-Config"), 30), "WiFi: FusionPad-Config", WHITE, FONT, 1)
    tft.text((center_x(f"IP: {ip}"), 50), f"IP: {ip}", WHITE, FONT, 1)
    tft.text((center_x("Connect to configure"), 70), "Connect to configure", GREEN, FONT, 1)
    tft.text((center_x("Press sw1 to exit"), 90), "Press sw1 to exit", RED, FONT, 1)
    
    print(f"Configuration mode active. Connect to WiFi: FusionPad-Config, IP: {ip}")
    
    last_client_check = time.ticks_ms()
    
    while True:
        # Check for exit button
        btns = buttons.get_data()
        if btns['sw1']:
            # Wait for button release
            while buttons.get_data()['sw1']:
                time.sleep(0.01)
            break
        
        # Check for client connections (non-blocking)
        if time.ticks_diff(time.ticks_ms(), last_client_check) > 100:
            try:
                client_socket, client_addr = server_socket.accept()
                print(f"Client connected from {client_addr}")
                handle_request(client_socket, config)
                last_client_check = time.ticks_ms()
            except:
                pass  # No client waiting
        
        time.sleep(0.01)
    
    # Cleanup
    try:
        server_socket.close()
    except:
        pass
    
    try:
        ap.active(False)
    except:
        pass
    
    tft.fill(BLACK)
    tft.text((center_x("Exiting Config"), 40), "Exiting Config", WHITE, FONT, 1)
    time.sleep(1)
