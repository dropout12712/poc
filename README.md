# Secure Storage Worker for Encrypted Data

This Cloudflare Worker implements a secure storage system for encrypted data, ensuring that no plaintext is ever visible to the server. The system is designed for use with a Minecraft mod client but can be adapted for other use cases.

## Security Model

### Server-Side Security
- Server NEVER sees plaintext data
- All data is encrypted client-side before transmission
- Server validates write access using a `POST_SECRET` header
- Session tokens are validated with an external auth service
- Rate limiting and payload size restrictions are enforced

### Client-Side Security Requirements
- Use Argon2id (preferred) or PBKDF2-HMAC-SHA256 (≥200k iterations) for key derivation
- Use AES-256-GCM with 12-byte random IV and 128-bit tag
- Generate new random salt (≥16 bytes) per record
- Store password in memory transiently, zero after use
- Never send plaintext password to server

⚠️ **CRITICAL SECURITY WARNINGS**
1. **NO PASSWORD RECOVERY**: Lost passwords are UNRECOVERABLE. There is NO way to decrypt data if the password is lost.
2. **Static Secret Risk**: The `POST_SECRET` header is a basic security measure. Consider:
   - Rotating secrets regularly
   - Using HMAC signatures with timestamps
   - Implementing per-client API keys
3. **Client Security**: Never store the `POST_SECRET` in client-side code in production.
4. **Password Requirements**:
   - Minimum 12 characters
   - Mix of uppercase, lowercase, numbers, symbols
   - Higher entropy = better security
   - Consider using a password manager

## API Endpoints

### POST /store
Stores an encrypted payload.

Required Header:
```
X-Post-Secret: <secret>
```

Request Body (JSON):
```json
{
  "uuid": "player-uuid",
  "username": "PlayerName",
  "session_token": "opaque-session-token",
  "algorithm": "AES-GCM-256",
  "kdf": "PBKDF2-HMAC-SHA256",
  "kdf_params": {
    "salt": "<base64>",
    "iterations": 200000
  },
  "iv": "<base64>",
  "ciphertext": "<base64>",
  "tables_count": 5,
  "ts": "2025-11-01T12:00:00Z"
}
```

Responses:
- 200: `{ "ok": true, "key": "<storage-key>" }`
- 401: Unauthorized (invalid secret/session)
- 400: Bad Request (invalid JSON/missing fields)
- 429: Too Many Requests
- 500: Internal Error

### GET /fetch?key=<storage-key>
Retrieves an encrypted payload.

Required Header:
```
Authorization: <session-token>
```

Responses:
- 200: Encrypted payload JSON
- 401: Unauthorized
- 404: Not Found
- 500: Internal Error

## Configuration

### Worker Environment Variables
- `POST_SECRET`: Secret key for validating write access
- `AUTH_ENDPOINT`: URL of authentication service

### Storage Configuration
- KV Namespace: `ENCRYPTED_KV` for small records
- R2 Bucket: `ENCRYPTED_R2` for large blobs

## Rotating POST_SECRET

1. Create new secret in Worker environment:
   ```bash
   wrangler secret put NEW_POST_SECRET
   ```

2. Update client configurations with new secret

3. Remove old secret:
   ```bash
   wrangler secret delete POST_SECRET
   ```

4. Rename new secret:
   ```bash
   wrangler secret put POST_SECRET --value "$(wrangler secret get NEW_POST_SECRET)"
   wrangler secret delete NEW_POST_SECRET
   ```

## Development Setup

1. Install dependencies:
   ```bash
   npm install
   ```

2. Configure environment:
   - Copy `wrangler.toml.example` to `wrangler.toml`
   - Add your KV namespace and R2 bucket IDs
   - Set your `POST_SECRET` and `AUTH_ENDPOINT`

3. Local development:
   ```bash
   wrangler dev
   ```

4. Deploy:
   ```bash
   wrangler deploy
   ```

## Testing

Test with provided client implementation or using curl:

```bash
# Store encrypted data
curl -X POST https://<worker>/store \
  -H "X-Post-Secret: your-secret" \
  -H "Content-Type: application/json" \
  -d @payload.json

# Fetch encrypted data
curl https://<worker>/fetch?key=enc:uuid:timestamp \
  -H "Authorization: session-token"
```

⚠️ Remember: Use secure methods to distribute the `POST_SECRET` to clients in production.