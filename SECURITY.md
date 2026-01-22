# Security Considerations

## Current Authentication

The server uses API key authentication passed either via URL parameter or Authorization header.

### URL Parameter (current default)
```
https://your-server.ngrok-free.app/sse?api_key=YOUR_KEY
```

### Authorization Header (recommended)
```
Authorization: Bearer YOUR_KEY
```

## ⚠️ Known Limitations

### API Key in URL
When using URL parameter authentication, the API key is visible in:
- ngrok request logs
- Server access logs
- Browser history (if accessed directly)
- Any proxy or CDN logs

**Mitigation:** Use a strong, unique API key and rotate it periodically.

### No Rate Limiting
The server currently has no rate limiting. A malicious actor with your API key could flood the server with requests.

### CORS Configuration
Currently set to `Access-Control-Allow-Origin: *` to allow claude.ai connections from various subdomains. This is acceptable because all endpoints require API key authentication.

### Unencrypted Database
SQLite database is stored in plaintext. Anyone with access to the server filesystem can read all notes.

**Mitigation:** Ensure proper filesystem permissions and server access controls.

## 🔐 Recommended Improvements

### 1. OAuth 2.0 Flow (Recommended)

Claude.ai supports OAuth Client ID/Secret in Advanced settings. Implementing OAuth would:
- Eliminate API key from URLs
- Provide token-based authentication with expiration
- Enable proper token refresh flow

**Implementation outline:**
```python
# Required endpoints:
# GET  /oauth/authorize - Authorization endpoint
# POST /oauth/token     - Token endpoint
# POST /oauth/refresh   - Token refresh

# OAuth config in claude.ai:
# - OAuth Client ID: your-client-id
# - OAuth Client Secret: your-client-secret
```

### 2. Header-Only Authentication

Modify `verify_auth()` to reject URL parameter authentication:

```python
def verify_auth(request):
    # Only accept Authorization header
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header[7:]
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        return hmac.compare_digest(token_hash, API_KEY_HASH)
    return False
```

### 3. Rate Limiting

Add rate limiting using Flask-Limiter:

```python
from flask_limiter import Limiter

limiter = Limiter(key_func=lambda: request.headers.get('Authorization', ''))

@app.route('/sse')
@limiter.limit("100/minute")
def mcp_sse():
    ...
```

### 4. Request Validation

Add input validation for content length:

```python
MAX_CONTENT_LENGTH = 10000  # characters

def add_note(content, category):
    if len(content) > MAX_CONTENT_LENGTH:
        return {'error': {'code': -32602, 'message': 'Content too long'}}
    ...
```

## 🛡️ Best Practices

1. **Use strong API key** — minimum 32 characters, random
2. **Change default key** — never use `change_me_in_production`
3. **Restrict server access** — firewall rules, VPN if possible
4. **Monitor logs** — watch for unusual access patterns
5. **Regular backups** — protect against data loss
6. **Keep dependencies updated** — security patches

## Threat Model

| Threat | Risk | Mitigation |
|--------|------|------------|
| API key leak | Medium | Strong key, rotation, OAuth migration |
| Request flooding | Low | Rate limiting |
| Data theft (server access) | Low | Filesystem permissions, encryption |
| Man-in-the-middle | Low | HTTPS via ngrok |
| Injection attacks | Low | Parameterized SQL queries |

## Reporting Security Issues

If you discover a security vulnerability, please open a private issue or contact the maintainer directly.
