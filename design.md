Here’s the design document rewritten in Markdown format for you:

# Design Document: LLM Fallbacks, Scaling, and Utilization

## 1. Overview

This system is designed to support **LLM service fallbacks, cold start scaling, zero-latency routing, and maximum utilization**. It includes traffic routing, session management, and monitoring for small and large LLM models.

### Key goals:
- Handle cold starts smoothly by over-provisioning.
- Minimize latency using automated routing.
- Maximize utilization across available models.

---

## 2. Tech Stack

| Component      | Purpose                              |
|---------------|-------------------------------------|
| Nomod E12     | Orchestration / container management |
| Redis         | Global + local caching and session store |
| Datadog       | Monitoring, observability, metrics collection |

---

## 3. System Architecture

### 3.1 High-level flow

[ App / Data Plane ]
|
[ Traffic Router ]
|
[ Redis Check → Local Cache -> during time on connection ]
|
[ Model Selection based on session id ]
|
[ LLM Pods (vLLM, Athena, etc.) ]

- **Redis global store**: Maintains session-to-model mapping.
- **Local cache on containers**: Reduces RTT and Redis load.
- **Per-call/session routing**: Ensures efficient model selection.
- **Fallbacks**: Automatically retry or downgrade if a model fails (locally caches it per session to swap models in the future).

### 3.2 Session lifecycle

1. Session initiated → assign session ID + 4-bit selector.
2. Selector + session ID stored in Redis.
3. Session id is used to determine model routing.
4. App pods forward to correct LLM pod.
5. Session winds down → Redis entry expires (longer TTL, no short TTL).

### 3.3 Traffic and scaling
eg.
- Support **100 TPM (transactions per minute)** baseline.
- Prioritize:
  - Small models (~10 min cold start).
  - Large models (~15 min cold start).
- Over-provision at peak to avoid cold start delays.
- Zero-latency goal supported by:
  - Pre-warming pods.
  - Automated scaling.
  - Smart fallback policies.

Have a separate system to monitor traffic (ideally) GPU utilization, if not number of requests, tokens used etc.

---

## 4. Solution Design


✅ Check Redis for session routing (adds slight latency during connection, but temporary).  
✅ Cache results locally in container to reduce future lookup time.
✅ Match session id to model at session start (not per request), eliminating RTT.  

---

## 5. Diagrams

### Diagram 1: Data Plane and Routing

```mermaid
graph TD
    A[App / Data Plane] --> B[Traffic Router]
    B --> C[Redis Check]
    C --> D[Local Cache]
    D --> E[Model Selector in session id]
    E --> initiate call

Diagram 2: Session Management Flow

sequenceDiagram
    participant Client
    participant App
    participant Model

    Client->>App: Start session
    App->>Redis: Check/Create session ID + selector
    App->>Model: Route based on selector
    Model-->>App: Processed response, if fail use a different inference endpoint as fallback and cache for future use (not in scope)
    App-->>Client: Return result


⸻

6. Scaling and Utilization

Load Level	Strategy
Low	Use small models, fewer pods active
Medium	Pre-warm additional pods
High	Use full capacity, mix small + large models, scale out
Failure	Trigger fallback to smaller model or alternative


⸻

7. Monitoring and Observability
	•	Use Datadog to track:
	•	Request latency
	•	Model utilization
	•	Cold start events
	•	Redis hit/miss rates

⸻

8. Key Decisions
	•	Per-session routing reduces per-call overhead.
	•	Global Redis + local cache combo balances consistency and speed.
    •   Session Id helps determine the right inference endpoint, model.
	•	Avoiding short TTLs in redis ensures clean session closure.
	•	Fallback logic ensures resilience during failures or cold starts.