#!/usr/bin/env python3
"""
Web server for Raspberry Pi temperature monitoring system.
"""

import json
import sqlite3
import os
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import logging

class TemperatureServer:
    def __init__(self, config_path="config/config.json"):
        self.config = self.load_config(config_path)
        self.db_path = self.config["storage"]["database_file"]
        self.setup_logging()
    
    def load_config(self, config_path):
        """Load configuration from JSON file."""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logging.error(f"Config file not found: {config_path}")
            raise
        except json.JSONDecodeError:
            logging.error(f"Invalid JSON in config file: {config_path}")
            raise
    
    def setup_logging(self):
        """Setup logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('data/server.log'),
                logging.StreamHandler()
            ]
        )
    
    def get_temperature_data(self, hours=24):
        """Get temperature data from database for the specified time range."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            start_time = datetime.now() - timedelta(hours=hours)
            
            # Get basic temperature data (CPU, GPU)
            cursor.execute('''
                SELECT timestamp, cpu_temp, gpu_temp
                FROM temperature_readings
                WHERE timestamp >= ?
                ORDER BY timestamp ASC
            ''', (start_time.isoformat(),))
            
            basic_rows = cursor.fetchall()
            
            # Get storage temperature data
            cursor.execute('''
                SELECT timestamp, device_path, device_name, temperature
                FROM storage_temperatures
                WHERE timestamp >= ?
                ORDER BY timestamp ASC
            ''', (start_time.isoformat(),))
            
            storage_rows = cursor.fetchall()
            
            # Get external sensor data
            cursor.execute('''
                SELECT timestamp, sensor_name, sensor_type, temperature
                FROM external_temperatures
                WHERE timestamp >= ?
                ORDER BY timestamp ASC
            ''', (start_time.isoformat(),))
            
            external_rows = cursor.fetchall()
            
            conn.close()
            
            # Organize data by timestamp
            data_by_time = {}
            
            # Add basic readings
            for row in basic_rows:
                timestamp = row[0]
                if timestamp not in data_by_time:
                    data_by_time[timestamp] = {'timestamp': timestamp}
                data_by_time[timestamp]['cpu_temp'] = row[1]
                data_by_time[timestamp]['gpu_temp'] = row[2]
            
            # Add storage readings
            for row in storage_rows:
                timestamp = row[0]
                if timestamp not in data_by_time:
                    data_by_time[timestamp] = {'timestamp': timestamp}
                    
                device_key = f"storage_{row[1].replace('/', '_')}"  # /dev/nvme0n1 -> storage__dev_nvme0n1
                data_by_time[timestamp][device_key] = {
                    'temperature': row[3],
                    'device_name': row[2],
                    'device_path': row[1]
                }
            
            # Add external sensor readings
            for row in external_rows:
                timestamp = row[0]
                if timestamp not in data_by_time:
                    data_by_time[timestamp] = {'timestamp': timestamp}
                    
                sensor_key = f"external_{row[1]}"
                data_by_time[timestamp][sensor_key] = {
                    'temperature': row[3],
                    'sensor_type': row[2],
                    'sensor_name': row[1]
                }
            
            # Convert to list and sort by timestamp
            result = list(data_by_time.values())
            result.sort(key=lambda x: x['timestamp'])
            
            return result
        except Exception as e:
            logging.error(f"Error fetching temperature data: {e}")
            return []
    
    def get_latest_readings(self):
        """Get the latest temperature readings."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            result = {'timestamp': None}
            
            # Get latest basic readings
            cursor.execute('''
                SELECT timestamp, cpu_temp, gpu_temp
                FROM temperature_readings
                ORDER BY timestamp DESC
                LIMIT 1
            ''')
            
            basic_row = cursor.fetchone()
            if basic_row:
                result['timestamp'] = basic_row[0]
                result['cpu_temp'] = basic_row[1]
                result['gpu_temp'] = basic_row[2]
            
            # Get latest storage readings
            cursor.execute('''
                SELECT device_path, device_name, temperature, timestamp
                FROM storage_temperatures
                WHERE timestamp = (SELECT MAX(timestamp) FROM storage_temperatures)
            ''')
            
            storage_rows = cursor.fetchall()
            result['storage_devices'] = []
            for row in storage_rows:
                result['storage_devices'].append({
                    'device_path': row[0],
                    'device_name': row[1],
                    'temperature': row[2],
                    'timestamp': row[3]
                })
            
            # Get latest external sensor readings
            cursor.execute('''
                SELECT sensor_name, sensor_type, temperature, timestamp
                FROM external_temperatures
                WHERE timestamp = (SELECT MAX(timestamp) FROM external_temperatures)
            ''')
            
            external_rows = cursor.fetchall()
            result['external_sensors'] = []
            for row in external_rows:
                result['external_sensors'].append({
                    'sensor_name': row[0],
                    'sensor_type': row[1],
                    'temperature': row[2],
                    'timestamp': row[3]
                })
            
            conn.close()
            
            return result if result['timestamp'] else None
        except Exception as e:
            logging.error(f"Error fetching latest readings: {e}")
            return None

class RequestHandler(BaseHTTPRequestHandler):
    def __init__(self, temperature_server, *args, **kwargs):
        self.temperature_server = temperature_server
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET requests."""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        query_params = parse_qs(parsed_path.query)
        
        if path == '/':
            self.serve_main_page()
        elif path == '/api/data':
            hours = int(query_params.get('hours', [24])[0])
            self.serve_temperature_data(hours)
        elif path == '/api/latest':
            self.serve_latest_readings()
        elif path == '/api/config':
            self.serve_config()
        else:
            self.send_error(404, "Not Found")
    
    def serve_main_page(self):
        """Serve the main HTML page."""
        html_content = self.generate_html_page()
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html_content.encode())
    
    def serve_temperature_data(self, hours):
        """Serve temperature data as JSON."""
        data = self.temperature_server.get_temperature_data(hours)
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def serve_latest_readings(self):
        """Serve latest temperature readings as JSON."""
        data = self.temperature_server.get_latest_readings()
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def serve_config(self):
        """Serve sensor configuration as JSON."""
        config = self.temperature_server.config["collection"]["sensors"]
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(config).encode())
    
    def generate_html_page(self):
        """Generate the main HTML page with embedded JavaScript."""
        return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Raspberry Pi Temperature Monitor</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        h1 {
            text-align: center;
            color: #333;
            margin-bottom: 30px;
        }
        .current-temps {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }
        .temp-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }
        .temp-card h3 {
            margin: 0 0 10px 0;
            font-size: 1.1em;
            line-height: 1.2;
        }
        .temp-card h3 small {
            font-size: 0.8em;
            opacity: 0.8;
            display: block;
            font-weight: normal;
        }
        .temp-value {
            font-size: 2em;
            font-weight: bold;
            margin: 0;
        }
        .controls {
            margin-bottom: 20px;
            text-align: center;
        }
        .time-selector {
            margin: 0 10px;
            padding: 8px 15px;
            border: 1px solid #ddd;
            border-radius: 4px;
            background: white;
            cursor: pointer;
        }
        .time-selector.active {
            background: #667eea;
            color: white;
        }
        .chart-container {
            position: relative;
            height: 400px;
            margin-bottom: 20px;
        }
        .last-update {
            text-align: center;
            color: #666;
            font-style: italic;
        }
        .loading {
            text-align: center;
            color: #666;
            margin: 20px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🌡️ Raspberry Pi Temperature Monitor</h1>
        
        <div class="current-temps" id="currentTemps">
            <div class="loading">Loading current temperatures...</div>
        </div>
        
        <div class="controls">
            <button class="time-selector active" onclick="selectTimeRange(1)">1 Hour</button>
            <button class="time-selector" onclick="selectTimeRange(6)">6 Hours</button>
            <button class="time-selector" onclick="selectTimeRange(24)">24 Hours</button>
            <button class="time-selector" onclick="selectTimeRange(72)">3 Days</button>
            <button class="time-selector" onclick="selectTimeRange(168)">1 Week</button>
        </div>
        
        <div class="chart-container">
            <canvas id="temperatureChart"></canvas>
        </div>
        
        <div class="last-update" id="lastUpdate"></div>
    </div>

    <script>
        let chart;
        let config = {};
        const colors = ['#ff6384', '#36a2eb', '#ffce56', '#4bc0c0', '#9966ff', '#ff9f40', '#ff6384', '#c9cbcf'];
        
        async function loadConfig() {
            try {
                const response = await fetch('/api/config');
                config = await response.json();
            } catch (error) {
                console.error('Error loading config:', error);
            }
        }
        
        async function loadCurrentTemperatures() {
            try {
                const response = await fetch('/api/latest');
                const data = await response.json();
                
                if (data) {
                    displayCurrentTemperatures(data);
                    document.getElementById('lastUpdate').textContent = 
                        `Last updated: ${new Date(data.timestamp).toLocaleString()}`;
                }
            } catch (error) {
                console.error('Error loading current temperatures:', error);
                document.getElementById('currentTemps').innerHTML = 
                    '<div class="loading">Error loading temperatures</div>';
            }
        }
        
        function displayCurrentTemperatures(data) {
            const container = document.getElementById('currentTemps');
            container.innerHTML = '';
            
            // CPU Temperature
            if (data.cpu_temp !== null && data.cpu_temp !== undefined) {
                addTemperatureCard(container, 'CPU', data.cpu_temp, '#ff6384');
            }
            
            // GPU Temperature
            if (data.gpu_temp !== null && data.gpu_temp !== undefined) {
                addTemperatureCard(container, 'GPU', data.gpu_temp, '#36a2eb');
            }
            
            // Storage devices
            if (data.storage_devices && data.storage_devices.length > 0) {
                data.storage_devices.forEach((device, index) => {
                    const name = device.device_name || device.device_path;
                    const shortName = name.length > 20 ? name.substring(0, 20) + '...' : name;
                    addTemperatureCard(container, shortName, device.temperature, '#ffce56', device.device_name);
                });
            }
            
            // External sensors
            if (data.external_sensors && data.external_sensors.length > 0) {
                data.external_sensors.forEach((sensor, index) => {
                    const colorIndex = (index + 3) % colors.length; // Start after CPU, GPU, SSD colors
                    addTemperatureCard(container, sensor.sensor_name, sensor.temperature, colors[colorIndex], sensor.sensor_type);
                });
            }
        }
        
        function addTemperatureCard(container, name, temperature, color, subtitle = null) {
            const card = document.createElement('div');
            card.className = 'temp-card';
            card.style.background = `linear-gradient(135deg, ${color} 0%, ${adjustBrightness(color, -20)} 100%)`;
            
            const title = subtitle ? `${name}<br><small>${subtitle}</small>` : name;
            
            card.innerHTML = `
                <h3>${title}</h3>
                <p class="temp-value">${temperature.toFixed(1)}°C</p>
            `;
            container.appendChild(card);
        }
        
        function adjustBrightness(color, percent) {
            // Simple color brightness adjustment
            const num = parseInt(color.replace("#",""), 16);
            const amt = Math.round(2.55 * percent);
            const R = (num >> 16) + amt;
            const B = (num >> 8 & 0x00FF) + amt;
            const G = (num & 0x0000FF) + amt;
            return "#" + (0x1000000 + (R<255?R<1?0:R:255)*0x10000 + (B<255?B<1?0:B:255)*0x100 + (G<255?G<1?0:G:255)).toString(16).slice(1);
        }
        
        async function loadTemperatureData(hours = 24) {
            try {
                const response = await fetch(`/api/data?hours=${hours}`);
                const data = await response.json();
                updateChart(data);
            } catch (error) {
                console.error('Error loading temperature data:', error);
            }
        }
        
        function updateChart(data) {
            const ctx = document.getElementById('temperatureChart').getContext('2d');
            
            if (chart) {
                chart.destroy();
            }
            
            const labels = data.map(d => new Date(d.timestamp).toLocaleTimeString());
            const datasets = [];
            const colors = ['#ff6384', '#36a2eb', '#ffce56', '#4bc0c0', '#9966ff', '#ff9f40', '#ff6384', '#c9cbcf'];
            let colorIndex = 0;
            
            // CPU Temperature
            if (data.length > 0 && data[0].cpu_temp !== undefined) {
                datasets.push({
                    label: 'CPU Temperature',
                    data: data.map(d => d.cpu_temp),
                    borderColor: colors[colorIndex],
                    backgroundColor: colors[colorIndex] + '20',
                    fill: false,
                    tension: 0.1
                });
                colorIndex++;
            }
            
            // GPU Temperature
            if (data.length > 0 && data[0].gpu_temp !== undefined) {
                datasets.push({
                    label: 'GPU Temperature',
                    data: data.map(d => d.gpu_temp),
                    borderColor: colors[colorIndex],
                    backgroundColor: colors[colorIndex] + '20',
                    fill: false,
                    tension: 0.1
                });
                colorIndex++;
            }
            
            // Storage devices
            const storageDevices = new Set();
            data.forEach(d => {
                Object.keys(d).forEach(key => {
                    if (key.startsWith('storage_')) {
                        storageDevices.add(key);
                    }
                });
            });
            
            storageDevices.forEach(deviceKey => {
                const sampleDevice = data.find(d => d[deviceKey])
                if (sampleDevice && sampleDevice[deviceKey]) {
                    const deviceName = sampleDevice[deviceKey].device_name || deviceKey;
                    datasets.push({
                        label: deviceName,
                        data: data.map(d => d[deviceKey] ? d[deviceKey].temperature : null),
                        borderColor: colors[colorIndex % colors.length],
                        backgroundColor: colors[colorIndex % colors.length] + '20',
                        fill: false,
                        tension: 0.1
                    });
                    colorIndex++;
                }
            });
            
            // External sensors
            const externalSensors = new Set();
            data.forEach(d => {
                Object.keys(d).forEach(key => {
                    if (key.startsWith('external_')) {
                        externalSensors.add(key);
                    }
                });
            });
            
            externalSensors.forEach(sensorKey => {
                const sampleSensor = data.find(d => d[sensorKey]);
                if (sampleSensor && sampleSensor[sensorKey]) {
                    const sensorName = sampleSensor[sensorKey].sensor_name || sensorKey;
                    datasets.push({
                        label: sensorName,
                        data: data.map(d => d[sensorKey] ? d[sensorKey].temperature : null),
                        borderColor: colors[colorIndex % colors.length],
                        backgroundColor: colors[colorIndex % colors.length] + '20',
                        fill: false,
                        tension: 0.1
                    });
                    colorIndex++;
                }
            });
            
            chart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: datasets
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: false,
                            title: {
                                display: true,
                                text: 'Temperature (°C)'
                            }
                        },
                        x: {
                            title: {
                                display: true,
                                text: 'Time'
                            }
                        }
                    },
                    plugins: {
                        legend: {
                            display: true,
                            position: 'top'
                        }
                    }
                }
            });
        }
        
        function selectTimeRange(hours) {
            // Update active button
            document.querySelectorAll('.time-selector').forEach(btn => {
                btn.classList.remove('active');
            });
            event.target.classList.add('active');
            
            // Load data for selected time range
            loadTemperatureData(hours);
        }
        
        // Initialize the page
        async function init() {
            await loadConfig();
            await loadCurrentTemperatures();
            await loadTemperatureData(24);
            
            // Refresh current temperatures every 30 seconds
            setInterval(loadCurrentTemperatures, 30000);
        }
        
        init();
    </script>
</body>
</html>'''
    
    def log_message(self, format, *args):
        """Override to use our logging configuration."""
        logging.info(f"{self.address_string()} - {format % args}")

def create_handler(temperature_server):
    """Create a request handler with the temperature server instance."""
    def handler(*args, **kwargs):
        RequestHandler(temperature_server, *args, **kwargs)
    return handler

def main():
    """Main function to run the server."""
    server = TemperatureServer()
    
    host = server.config["server"]["host"]
    port = server.config["server"]["port"]
    
    handler = create_handler(server)
    httpd = HTTPServer((host, port), handler)
    
    logging.info(f"Starting temperature monitoring server on http://{host}:{port}")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logging.info("Server stopped by user")
        httpd.shutdown()

if __name__ == "__main__":
    main()
