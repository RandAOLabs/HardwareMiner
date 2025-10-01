# Orange Pi RNG-Miner HTTP API Documentation

## Overview

This document describes the HTTP API endpoints available on the Orange Pi RNG-Miner device. The server runs on port 80 and provides both GET and POST endpoints for device configuration and monitoring.

**Base URL**: `http://<device-ip>`
**Default Ports**: 80, 8080, 8000 (app tries all three)
**CORS**: Enabled for all origins
**Content-Type**: `application/json`

---

## Health & Status Endpoints (GET)

### `GET /health`

Health check endpoint - verifies device is online and responsive.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-09-30T12:34:56.789Z",
  "device_id": "A1B2C3D4",
  "uptime": 3600
}
```

**Fields:**
- `status`: Always "healthy" if responding
- `timestamp`: ISO 8601 timestamp
- `device_id`: 8-character unique device identifier
- `uptime`: Server uptime in seconds

---

### `GET /device/info`

Get comprehensive device information including WiFi status, mining status, and configuration state.

**Response:**
```json
{
  "device_id": "A1B2C3D4",
  "model": "Orange Pi Zero 3",
  "wifi_state": "connected",
  "ip_address": "192.168.1.100",
  "ssid": "MyHomeNetwork",
  "mining_status": "configured",
  "uptime": 3600,
  "timestamp": "2025-09-30T12:34:56.789Z",
  "configuration_status": {
    "wifi_configured": true,
    "seed_phrase_set": true,
    "provider_id_set": true,
    "wallet_json_set": true,
    "mining_ready": true
  }
}
```

**Fields:**
- `wifi_state`: "connected" | "disconnected"
- `mining_status`: "configured" | "not_configured"
- `configuration_status`: Object showing what's been configured

---

### `GET /api/env-vars`

Get all environment variables and configuration values (matches old-bad-way API).

**Response:**
```json
{
  "SEED_PHRASE": "word1 word2 word3...",
  "PROVIDER_ID": "provider-123",
  "WALLET_JSON": "{\"address\":\"0x...\"}",
  "LOG_CONSOLE_LEVEL": "3",
  "NETWORK_IP": "192.168.1.100",
  "NETWORK_MODE": "bridge"
}
```

**Security Note:** This endpoint exposes sensitive data. Ensure only trusted networks can access the device.

---

### `GET /api/status`

Get boolean status of key configuration values (matches old-bad-way API).

**Response:**
```json
{
  "seedPhrase": true,
  "providerId": true,
  "walletJson": false
}
```

**Fields:** Boolean indicating whether each value is set (non-empty).

---

## Configuration Endpoints (POST)

### `POST /api/set-seed-phrase`

Set the BIP39 seed phrase for wallet generation.

**Request:**
```json
{
  "seed_phrase": "word1 word2 word3 word4 word5 word6 word7 word8 word9 word10 word11 word12"
}
```

**Response (Success):**
```json
{
  "success": true,
  "seed_phrase_set": true
}
```

**Response (Error):**
```json
{
  "error": "seed_phrase is required"
}
```

**Status Codes:**
- `200`: Success
- `400`: Invalid request (missing seed_phrase)
- `500`: Server error saving configuration

**Data Persistence:**
- Saved to: `/opt/device-software/config/device_config.json`
- Also written to: `/opt/mining/Randomness-Provider/docker-compose/.env` as `SEED_PHRASE`

---

### `POST /api/set-provider-id`

Set the provider ID for mining registration.

**Request:**
```json
{
  "provider_id": "provider-unique-id-123"
}
```

**Response (Success):**
```json
{
  "success": true,
  "provider_id": "provider-unique-id-123"
}
```

**Response (Error):**
```json
{
  "error": "provider_id is required"
}
```

**Data Persistence:**
- Saved to: `/opt/device-software/config/device_config.json`
- Also written to: `/opt/mining/Randomness-Provider/docker-compose/.env` as `PROVIDER_ID`

---

### `POST /api/set-wallet-json`

Set the wallet JSON Web Key (JWK) for Arweave transactions.

**Request:**
```json
{
  "wallet_json": "{\"kty\":\"RSA\",\"n\":\"...\",\"e\":\"AQAB\",\"d\":\"...\",\"p\":\"...\",\"q\":\"...\",\"dp\":\"...\",\"dq\":\"...\",\"qi\":\"...\"}"
}
```

Or as object:
```json
{
  "wallet_json": {
    "kty": "RSA",
    "n": "...",
    "e": "AQAB",
    "d": "...",
    "p": "...",
    "q": "...",
    "dp": "...",
    "dq": "...",
    "qi": "..."
  }
}
```

**Response (Success):**
```json
{
  "success": true,
  "wallet_json_set": true
}
```

**Response (Error):**
```json
{
  "error": "Invalid wallet_json format"
}
```

**Validation:**
- String values are validated as JSON
- Object values are automatically stringified
- Invalid JSON returns 400 error

**Data Persistence:**
- Saved to: `/opt/device-software/config/device_config.json`
- Also written to: `/opt/mining/Randomness-Provider/docker-compose/.env` as `WALLET_JSON`

---

### `POST /api/set-all-config`

Set multiple configuration values in a single atomic operation.

**Request:**
```json
{
  "seed_phrase": "word1 word2 word3...",
  "provider_id": "provider-123",
  "wallet_json": "{\"kty\":\"RSA\",...}"
}
```

**Notes:**
- All fields are optional
- Only provided fields are updated
- Empty strings are ignored
- Existing values are preserved if not included

**Response (Success):**
```json
{
  "success": true,
  "seed_phrase_set": true,
  "provider_id_set": true,
  "wallet_json_set": true
}
```

**Response (Error):**
```json
{
  "error": "Invalid wallet_json format"
}
```

**Data Persistence:**
- All values saved atomically to: `/opt/device-software/config/device_config.json`
- Mining-related values also written to: `/opt/mining/Randomness-Provider/docker-compose/.env`

---

### `POST /setup/wifi`

Configure WiFi connection credentials.

**Request:**
```json
{
  "ssid": "MyHomeNetwork",
  "password": "my-secure-password"
}
```

**Response (Success):**
```json
{
  "success": true,
  "message": "WiFi configuration saved"
}
```

**Response (Error):**
```json
{
  "success": false,
  "error_code": "INVALID_SSID",
  "message": "SSID cannot be empty"
}
```

**Status Codes:**
- `200`: Success
- `400`: Invalid request (missing ssid or password)
- `500`: Server error

**Data Persistence:**
- Saved to: `/opt/device-software/config/wifi_config.json`

**Note:** Current implementation saves credentials but does not automatically connect. WiFi connection logic needs to be implemented.

---

## Error Handling

### Standard Error Response Format

```json
{
  "success": false,
  "error_code": "ERROR_TYPE",
  "message": "Human-readable error description",
  "timestamp": "2025-09-30T12:34:56.789Z"
}
```

### Common Error Codes

- `ENDPOINT_NOT_FOUND` (404): API endpoint does not exist
- `INVALID_REQUEST` (400): Missing required fields or invalid data
- `HEALTH_CHECK_FAILED` (500): Health check endpoint error
- `DEVICE_INFO_FAILED` (500): Failed to retrieve device information
- `CONFIGURATION_ERROR` (500): Failed to save configuration
- `SETUP_FAILED` (500): WiFi setup error
- `INTERNAL_SERVER_ERROR` (500): Unexpected server error

---

## Data Storage

### Configuration Files

1. **`/opt/device-software/config/device_config.json`**
   - Main device configuration
   - Stores: seed_phrase, provider_id, wallet_json, timestamps
   - Format: JSON

2. **`/opt/device-software/config/wifi_config.json`**
   - WiFi credentials
   - Stores: ssid, password, timestamp
   - Format: JSON

3. **`/opt/device-software/config/mining_config.json`**
   - Mining-specific configuration (future use)
   - Format: JSON

4. **`/opt/mining/Randomness-Provider/docker-compose/.env`**
   - Docker environment variables
   - Stores: SEED_PHRASE, PROVIDER_ID, WALLET_JSON, LOG_CONSOLE_LEVEL
   - Format: Shell environment file

5. **`/opt/device-software/data/device_id`**
   - Persistent device ID
   - Format: Plain text (8 characters)

### Device ID Generation

Device ID is an 8-character uppercase hex string generated from:
1. MAC address (primary network interface)
2. Machine ID (`/etc/machine-id`)
3. Hostname
4. Fallback: timestamp-based

Once generated, the device ID is persisted and never changes.

---

## Usage Examples

### TypeScript/JavaScript (React Native)

```typescript
import { DeviceApiClient } from '@/services/device-communication/DeviceApiClient';

// Create client
const client = new DeviceApiClient('192.168.4.1');

// GET requests
const healthResult = await client.getHealthStatus();
const deviceInfo = await client.getDeviceInfo();

// POST requests
const setSeedResult = await client.post('/api/set-seed-phrase', {
  seed_phrase: 'word1 word2 word3...'
});

const setProviderResult = await client.post('/api/set-provider-id', {
  provider_id: 'provider-123'
});

const setWifiResult = await client.post('/setup/wifi', {
  ssid: 'MyNetwork',
  password: 'password123'
});

// Atomic configuration
const setAllResult = await client.post('/api/set-all-config', {
  seed_phrase: 'word1 word2 word3...',
  provider_id: 'provider-123',
  wallet_json: JSON.stringify(walletJwk)
});
```

### Python

```python
import requests

device_ip = '192.168.4.1'

# GET request
response = requests.get(f'http://{device_ip}/device/info')
device_info = response.json()

# POST request
response = requests.post(
    f'http://{device_ip}/api/set-seed-phrase',
    json={'seed_phrase': 'word1 word2 word3...'}
)
result = response.json()
```

### cURL

```bash
# Health check
curl http://192.168.4.1/health

# Get device info
curl http://192.168.4.1/device/info

# Set seed phrase
curl -X POST http://192.168.4.1/api/set-seed-phrase \
  -H "Content-Type: application/json" \
  -d '{"seed_phrase":"word1 word2 word3..."}'

# Set all config
curl -X POST http://192.168.4.1/api/set-all-config \
  -H "Content-Type: application/json" \
  -d '{
    "seed_phrase":"word1 word2 word3...",
    "provider_id":"provider-123",
    "wallet_json":"{\"kty\":\"RSA\",...}"
  }'
```

---

## Security Considerations

1. **No Authentication**: Currently, the API has no authentication. Only use on trusted networks.

2. **Sensitive Data Exposure**: `/api/env-vars` exposes seed phrases and private keys. Restrict network access.

3. **HTTPS**: Currently HTTP-only. HTTPS should be implemented for production use.

4. **Input Validation**: Basic validation is performed. Additional validation recommended for production.

5. **Rate Limiting**: No rate limiting currently implemented.

---

## Development & Debugging

### Server Logs

Logs are written to: `/opt/device-software/logs/http-server.log`

All requests and responses are logged with:
- Client IP address
- Request method and path
- Response status code
- Timestamps

### CORS Headers

All responses include:
```
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
Access-Control-Allow-Headers: Content-Type, Authorization, Accept
```

### Server Info

On startup, the server logs all available endpoints:
```
🚀 Starting Enhanced Orange Pi HTTP Server on port 80
Device ID: A1B2C3D4
Available endpoints:
  - /health
  - /device/info
  - /api/env-vars
  - /api/status
  - /api/set-seed-phrase
  - /api/set-provider-id
  - /api/set-wallet-json
  - /api/set-all-config
  - /setup/wifi
```

---

## Version History

- **v1.0** (2025-09-30): Initial API documentation for enhanced server
