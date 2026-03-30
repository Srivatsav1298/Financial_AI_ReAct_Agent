# API Reference
Norfain ReAct Agent - REST API Documentation

## Base URL

```
Production: https://your-domain.com
Development: http://localhost:5050
```

## Authentication

Currently, the API is open (no authentication required). For production deployments, implement:

- Bearer tokens (`Authorization: Bearer <token>`)
- API keys (`X-API-Key: <key>`)
- OAuth2 for user-specific endpoints

## Rate Limits

| Endpoint | Limit | Window |
|----------|-------|--------|
| `/api/ask` | 30 | minute |
| `/api/ssb-data` | 60 | minute |
| `/api/admin/*` | 10 | minute |
| All API | 100 | hour |

Rate limit headers returned:
```
X-RateLimit-Limit: 30
X-RateLimit-Remaining: 29
X-RateLimit-Reset: 1648699200
```

When exceeded: `429 Too Many Requests` with `Retry-After` header.

## Endpoints

### Health Check

```
GET /health
```

**Response** (200 OK):
```json
{
  "status": "healthy",
  "timestamp": "2025-03-30T17:01:02.654506Z",
  "components": {
    "app": "healthy",
    "agents": "loaded",
    "baseline_agent": "healthy",
    "react_agent": "healthy",
    "ssb_api": "connected",
    "cache": "enabled"
  },
  "metrics": {
    "requests": 150,
    "errors": 2,
    "error_rate": 0.0133,
    "avg_response_time": 2.34,
    "p95_response_time": 8.12,
    "cache_hits": 120,
    "cache_misses": 30,
    "cache_hit_rate": 0.8
  },
  "response_time_ms": 12
}
```

### Metrics (Prometheus)

```
GET /api/metrics
```

**Response** (200 OK, `text/plain`):
```
# HELP norfain_requests_total Total number of requests processed
# TYPE norfain_requests_total counter
norfain_requests_total 150

# HELP norfain_errors_total Total number of error responses
# TYPE norfain_errors_total counter
norfain_errors_total 2

# HELP norfain_response_time_seconds Average response time in seconds
# TYPE norfain_response_time_seconds gauge
norfain_response_time_seconds 2.34

# HELP norfain_cache_hits_total Number of cache hits
# TYPE norfain_cache_hits_total counter
norfain_cache_hits_total 120

# HELP norfain_uptime_seconds Application uptime in seconds
# TYPE norfain_uptime_seconds gauge
norfain_uptime_seconds 3600
```

---

### Ask Question (Compare Agents)

```
POST /api/ask
Content-Type: application/json
```

**Request Body:**
```json
{
  "question": "How much do Norwegian families spend on housing?",
  "language": "en",
  "persona": "analyst",
  "agent_type": "react"
}
```

**Parameters:**
- `question` (required, string, max 1000 chars): The financial question to ask
- `language` (optional, "en"|"no", default "en"): Response language
- `persona` (optional, string, default "analyst"): Agent persona style
- `agent_type` (optional, "baseline"|"react", default null): Specific agent to use. Omit for both

**Response** (200 OK):
```json
{
  "baseline": {
    "answer": "Based on SSB data, average housing costs...",
    "model": "baseline (llama3.2:latest)",
    "time": 3.45,
    "tool_used": false,
    "reasoning_steps": []
  },
  "react": {
    "answer": "To answer this question, I need to...",
    "model": "react_simple (llama3.2:latest)",
    "time": 8.23,
    "iterations": 2,
    "reasoning_steps": [
      {
        "thought": "I need to find average housing costs from SSB",
        "action": "get_average_spending_by_category('Housing')",
        "observation": "SSB data shows NOK 8,500/month average"
      },
      {
        "thought": "Adjust for location and family size",
        "action": "get_oslo_adjustment_factor()",
        "observation": "Oslo premium: 1.2x"
      }
    ],
    "tool_result": null,
    "conversation_history": []
  },
  "comparison": {
    "time_difference": 4.78,
    "time_ratio": 2.38,
    "reasoning_available": true
  },
  "question": "How much do Norwegian families spend on housing?",
  "language": "en",
  "server_time_ms": 8500
}
```

---

### SSB Data Endpoint

```
GET /api/ssb-data
```

**Query Parameters:**
- `year` (optional, YYYY, default "2022"): Data year (2000-2030)
- `nowcast` (optional, true|false, default true): Apply inflation adjustment to present

**Response** (200 OK):
```json
{
  "data": [
    {
      "category": "Food and non-alcoholic beverages",
      "category_code": "01",
      "value": 8452.50,
      "year": "2022 (Nowcast)",
      "raw_value": 7350.00,
      "inflation_factor": 1.15,
      "unit": "NOK per year"
    },
    {
      "category": "Housing, water, electricity, gas",
      "category_code": "04",
      "value": 18952.80,
      "year": "2022 (Nowcast)",
      "raw_value": 16920.00,
      "inflation_factor": 1.12,
      "unit": "NOK per year"
    }
  ],
  "metadata": {
    "year": "2022",
    "nowcast": true,
    "source": "SSB (Statistics Norway)",
    "count": 12
  }
}
```

---

### CPI Inflation Data

```
GET /api/cpi
```

**Response** (200 OK):
```json
{
  "multipliers": {
    "TOTAL": 1.134,
    "01": 1.152,
    "02": 1.129,
    "03": 1.085,
    "04": 1.126,
    "05": 1.098,
    "06": 1.142,
    "07": 1.118,
    "08": 1.095,
    "09": 1.107,
    "10": 1.123,
    "11": 1.138,
    "12": 1.114
  },
  "source": "SSB Table 03013",
  "description": "CPI multipliers from 2022 to present",
  "base_year": "2022"
}
```

---

### Agent Information

```
GET /api/agent/info
```

**Response** (200 OK):
```json
{
  "baseline": {
    "name": "Baseline Agent",
    "description": "Fast, direct prompting without explicit reasoning",
    "model": "llama3.2:latest",
    "typical_time": "6-8 seconds"
  },
  "react": {
    "name": "ReAct Agent",
    "description": "Explicit reasoning with Thought→Action→Observation loop",
    "model": "llama3.2:latest",
    "typical_time": "10-14 seconds"
  }
}
```

---

### Savings Goals API

#### List Goals
```
GET /api/goals
```

**Response** (200 OK):
```json
{
  "goals": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Emergency Fund",
      "target_amount": 50000.0,
      "current_amount": 15000.0,
      "deadline": "2025-12-31",
      "created_at": "2025-03-30T12:34:56.789Z",
      "inflation_adjusted": true
    }
  ]
}
```

#### Create Goal
```
POST /api/goals
Content-Type: application/json
```

**Request Body:**
```json
{
  "name": "Vacation Fund",
  "target_amount": 25000,
  "deadline": "2025-08-15",
  "current_amount": 5000,
  "inflation_adjusted": true
}
```

**Response** (201 Created):
```json
{
  "goal": {
    "id": "new-uuid-here",
    "name": "Vacation Fund",
    ...
  }
}
```

#### Update Goal
```
PUT /api/goals/<goal_id>
Content-Type: application/json
```

**Response** (200 OK):
```json
{
  "goal": { /* updated goal object */ }
}
```

#### Delete Goal
```
DELETE /api/goals/<goal_id>
```

**Response** (200 OK):
```json
{
  "message": "Goal deleted"
}
```

#### Contribute to Goal
```
POST /api/goals/<goal_id>/contribute
Content-Type: application/json
```

**Request Body:**
```json
{
  "amount": 2500
}
```

**Response** (200 OK):
```json
{
  "goal": { /* updated goal with new current_amount */ },
  "contribution": 2500,
  "message": "Added 2500 to goal"
}
```

---

### Admin: Clear Cache

```
POST /api/admin/cache/clear
X-Admin-Token: <admin-token>
```

**Response** (200 OK):
```json
{
  "message": "Cache cleared successfully",
  "timestamp": "2025-03-30T17:15:00.123Z"
}
```

---

## Error Responses

Standard error format:

```json
{
  "error": "Error Type",
  "message": "Human-readable description",
  "status_code": 400,
  "field": "question" // optional, for validation errors
}
```

**HTTP Status Codes:**
- `200` - Success
- `400` - Bad Request (validation error)
- `401` - Unauthorized (missing/invalid auth)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found
- `429` - Rate Limit Exceeded
- `500` - Internal Server Error
- `503` - Service Unavailable

## SSL/TLS

Production deployments **must** use HTTPS:

```nginx
# Nginx reverse proxy with SSL
ssl_certificate /path/to/cert.pem;
ssl_certificate_key /path/to/key.pem;
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
```

## Webhooks

*Coming soon: Webhook notifications for completed agent queries.*

---

For additional support, see [PRODUCTION.md](./PRODUCTION.md)
