interface Env {
  ENCRYPTED_KV: KVNamespace;
  ENCRYPTED_R2: R2Bucket;
  POST_SECRET: string;
  AUTH_ENDPOINT: string;
}

interface EncryptedPayload {
  uuid: string;
  username: string;
  session_token: string;
  algorithm: string;
  kdf: "PBKDF2-HMAC-SHA256" | "Argon2id";
  kdf_params: {
    salt: string;
    iterations: number;
  };
  iv: string;
  ciphertext: string;
  tables_count?: number;
  ts: string;
}

// Custom error for rate limiting
class RateLimitError extends Error {
  constructor(message = 'Too Many Requests') {
    super(message);
    this.name = 'RateLimitError';
  }
}

// Constants
const MAX_PAYLOAD_SIZE = 10 * 1024 * 1024; // 10MB
const RATE_LIMIT_REQUESTS = 100; // requests per minute
const RATE_LIMIT_WINDOW = 60 * 1000; // 1 minute in milliseconds

export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    try {
      // Only handle POST to /store and GET to /fetch
      const url = new URL(request.url);
      if (url.pathname === '/store' && request.method === 'POST') {
        return await handleStore(request, env);
      } else if (url.pathname === '/fetch' && request.method === 'GET') {
        return await handleFetch(request, env);
      }

      return new Response('Not Found', { status: 404 });
    } catch (err) {
      if (err instanceof RateLimitError) {
        return new Response('Too Many Requests', { status: 429 });
      }
      
      console.error('Error:', err instanceof Error ? err.message : 'Unknown error');
      return new Response('Internal Server Error', { status: 500 });
    }
  }
};

async function validateRequest(request: Request, env: Env): Promise<void> {
  // Check POST secret
  const postSecret = request.headers.get('X-Post-Secret');
  if (!postSecret || postSecret !== env.POST_SECRET) {
    throw new Response('Unauthorized', { status: 401 });
  }

  // Check content length
  const contentLength = parseInt(request.headers.get('Content-Length') || '0');
  if (contentLength > MAX_PAYLOAD_SIZE) {
    throw new Response('Payload Too Large', { status: 413 });
  }
}

async function validateSessionToken(uuid: string, sessionToken: string, env: Env): Promise<boolean> {
  try {
    const response = await fetch(env.AUTH_ENDPOINT, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        uuid,
        session_token: sessionToken,
      }),
    });

    return response.ok;
  } catch (error) {
    console.error('Auth service error:', error);
    return false;
  }
}

async function handleStore(request: Request, env: Env): Promise<Response> {
  // Validate request headers and size
  await validateRequest(request, env);

  // Parse and validate payload
  const payload: EncryptedPayload = await request.json();
  
  // Validate required fields
  const requiredFields = ['uuid', 'username', 'session_token', 'algorithm', 'kdf', 'kdf_params', 'iv', 'ciphertext', 'ts'];
  for (const field of requiredFields) {
    if (!(field in payload)) {
      return new Response(`Missing required field: ${field}`, { status: 400 });
    }
  }

  // Validate session token
  const isValidSession = await validateSessionToken(payload.uuid, payload.session_token, env);
  if (!isValidSession) {
    return new Response('Invalid session token', { status: 401 });
  }

  // Generate storage key
  const key = `enc:${payload.uuid}:${Date.now()}`;

  // Store encrypted data
  try {
    if (request.headers.get('content-length') && parseInt(request.headers.get('content-length')!) > 100 * 1024) {
      // Store large payloads in R2
      await env.ENCRYPTED_R2.put(key, JSON.stringify(payload));
    } else {
      // Store smaller payloads in KV
      await env.ENCRYPTED_KV.put(key, JSON.stringify(payload));
    }

    // Log non-sensitive metadata
    console.log('Stored encrypted data:', {
      key,
      timestamp: payload.ts,
      uuid: payload.uuid,
      size: request.headers.get('content-length'),
    });

    return new Response(JSON.stringify({ ok: true, key }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' }
    });
  } catch (error) {
    console.error('Storage error:', error);
    return new Response('Storage error', { status: 500 });
  }
}

async function handleFetch(request: Request, env: Env): Promise<Response> {
  const url = new URL(request.url);
  const key = url.searchParams.get('key');
  
  if (!key) {
    return new Response('Missing key parameter', { status: 400 });
  }

  // Validate session token for fetch requests
  const sessionToken = request.headers.get('Authorization');
  if (!sessionToken) {
    return new Response('Missing Authorization header', { status: 401 });
  }

  // Extract UUID from key to validate session
  const keyParts = key.split(':');
  if (keyParts.length !== 3 || keyParts[0] !== 'enc') {
    return new Response('Invalid key format', { status: 400 });
  }

  const uuid = keyParts[1];
  const isValidSession = await validateSessionToken(uuid, sessionToken, env);
  if (!isValidSession) {
    return new Response('Invalid session token', { status: 401 });
  }

  try {
    // Try KV first
    let data = await env.ENCRYPTED_KV.get(key);
    
    // If not in KV, try R2
    if (!data) {
      const r2Object = await env.ENCRYPTED_R2.get(key);
      if (r2Object) {
        data = await r2Object.text();
      }
    }

    if (!data) {
      return new Response('Not Found', { status: 404 });
    }

    return new Response(data, {
      status: 200,
      headers: { 'Content-Type': 'application/json' }
    });
  } catch (error) {
    console.error('Fetch error:', error);
    return new Response('Storage error', { status: 500 });
  }
}