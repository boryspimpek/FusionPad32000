# html_template.py - HTML template for web configuration interface

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
