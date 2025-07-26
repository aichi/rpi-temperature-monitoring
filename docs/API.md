# API Documentation

The Raspberry Pi Temperature Monitor provides a REST API for accessing temperature data and system information.

## Base URL

When running locally: `http://localhost:8080`
When running on Pi: `http://[raspberry-pi-ip]:8080`

## Endpoints

### GET /

Returns the main web interface (HTML page).

**Response:** HTML page with temperature monitoring dashboard

---

### GET /api/latest

Get the most recent temperature readings from all sensors.

**Response:**
```json
{
  "timestamp": "2025-07-26T10:30:00",
  "cpu_temp": 45.2,
  "gpu_temp": 46.8,
  "storage_devices": [
    {
      "device_path": "/dev/nvme0n1",
      "device_name": "Samsung SSD 980 PRO 1TB",
      "temperature": 42.0,
      "timestamp": "2025-07-26T10:30:00"
    }
  ],
  "external_sensors": [
    {
      "sensor_name": "outdoor_temp",
      "sensor_type": "DS18B20",
      "temperature": 23.5,
      "timestamp": "2025-07-26T10:30:00"
    }
  ]
}
```

---

### GET /api/data

Get historical temperature data for a specified time range.

**Parameters:**
- `hours` (optional): Number of hours of data to retrieve (default: 24)

**Example:** `/api/data?hours=6`

**Response:**
```json
[
  {
    "timestamp": "2025-07-26T10:00:00",
    "cpu_temp": 44.1,
    "gpu_temp": 45.3,
    "storage_/dev/nvme0n1": {
      "temperature": 41.5,
      "device_name": "Samsung SSD 980 PRO 1TB",
      "device_path": "/dev/nvme0n1"
    },
    "external_outdoor_temp": {
      "temperature": 22.8,
      "sensor_type": "DS18B20",
      "sensor_name": "outdoor_temp"
    }
  },
  {
    "timestamp": "2025-07-26T10:05:00",
    "cpu_temp": 45.2,
    "gpu_temp": 46.8,
    "storage_/dev/nvme0n1": {
      "temperature": 42.0,
      "device_name": "Samsung SSD 980 PRO 1TB",
      "device_path": "/dev/nvme0n1"
    },
    "external_outdoor_temp": {
      "temperature": 23.5,
      "sensor_type": "DS18B20",
      "sensor_name": "outdoor_temp"
    }
  }
]
```

**Notes:**
- Storage devices are keyed as `storage_<device_path>` with special characters replaced
- External sensors are keyed as `external_<sensor_name>`
- Missing values are null if sensor was unavailable at that time

---

### GET /api/config

Get the current sensor configuration.

**Response:**
```json
{
  "cpu_temp": true,
  "gpu_temp": true,
  "ssd_temp": true,
  "external_sensors": false
}
```

## Data Formats

### Temperature Values
- All temperatures are in Celsius
- Precision: 1-2 decimal places
- Range: Depends on sensor type
- Null value indicates sensor unavailable or reading failed

### Timestamps
- Format: ISO 8601 (`YYYY-MM-DDTHH:MM:SS`)
- Timezone: Local system timezone
- Resolution: Depends on collection interval (default: 5 minutes)

### Device Information
- `device_path`: Linux device path (e.g., `/dev/nvme0n1`)
- `device_name`: Human-readable device name from SMART data
- Fallback to device path if name unavailable

### Sensor Information
- `sensor_name`: User-defined sensor name from configuration
- `sensor_type`: Plugin type (DS18B20, DHT22, etc.)
- Additional fields may be present depending on sensor type

## Error Handling

### HTTP Status Codes
- `200 OK`: Request successful
- `404 Not Found`: Endpoint not found
- `500 Internal Server Error`: Server error

### Error Response Format
```json
{
  "error": "Error description",
  "timestamp": "2025-07-26T10:30:00"
}
```

## Rate Limiting

No rate limiting is currently implemented. The API is designed for:
- Web interface updates (every 30 seconds)
- External monitoring tools (every 1-5 minutes)
- Data export scripts (occasional use)

## Security Considerations

- **No Authentication**: Currently no authentication required
- **Local Network**: Designed for local network access
- **Read-Only**: All endpoints are read-only (no data modification)
- **CORS**: Cross-origin requests are allowed for flexibility

## Integration Examples

### Python Example
```python
import requests

# Get latest readings
response = requests.get('http://192.168.1.100:8080/api/latest')
data = response.json()
print(f"CPU Temperature: {data['cpu_temp']}°C")

# Get 6 hours of data
response = requests.get('http://192.168.1.100:8080/api/data?hours=6')
history = response.json()
print(f"Retrieved {len(history)} data points")
```

### JavaScript Example
```javascript
// Get latest readings
fetch('/api/latest')
  .then(response => response.json())
  .then(data => {
    console.log('CPU Temperature:', data.cpu_temp + '°C');
    console.log('Storage Devices:', data.storage_devices.length);
  });

// Get historical data
fetch('/api/data?hours=24')
  .then(response => response.json())
  .then(data => {
    console.log('24 hours of data:', data.length, 'points');
  });
```

### curl Examples
```bash
# Get latest readings
curl http://192.168.1.100:8080/api/latest

# Get 12 hours of data
curl "http://192.168.1.100:8080/api/data?hours=12"

# Get sensor configuration
curl http://192.168.1.100:8080/api/config
```

## Future API Enhancements

Planned additions for future versions:
- Authentication endpoints
- Data export formats (CSV, Excel)
- Real-time WebSocket updates
- Sensor control endpoints
- Alert/threshold management
- System information endpoints
