# Stadium OS – Predictive Experience Engine

Stadium OS is a predictive, context-aware decision engine for large-scale stadium events. It is designed to help attendees make faster decisions about entry, food, and exit by combining intent detection, live contextual signals, and short-horizon prediction logic.

This is not a basic chatbot. Stadium OS behaves like a product system: it interprets user intent, evaluates current stadium conditions, predicts what is likely to change next, and returns an optimized recommendation with reasoning.

## Problem Statement

Stadium environments create repeated friction for attendees because conditions change quickly and local decisions are hard to make in real time. Common issues include crowd congestion at gates, long food queues during halftime, poor navigation across large venues, and delayed exits when thousands of people leave at once.

Most users do not need generic conversation. They need a system that can answer practical questions such as where to enter, where to get food quickly, and which exit will be least disruptive based on the current event phase and near-future crowd movement.

## Solution Overview

Stadium OS acts as a predictive decision engine for the stadium experience. It takes a user request, detects one or more intents, models the surrounding context, forecasts near-term crowd behavior, and returns a ranked recommendation.

The system is built to support decision-making across multiple stadium tasks in a single interaction. For example, a user can ask for food first and exit guidance second, and the engine will produce a step-by-step plan instead of forcing a single-answer response.

## Key Features

- Intent detection with multi-intent support so a single query can contain entry, food, and exit goals.
- Context modeling across crowd level, distance, and wait time.
- Predictive logic that estimates how conditions will shift in the next few minutes.
- Decision engine that scores options and returns an optimized recommendation.
- Multi-step planning for chained flows such as food plus exit guidance.
- Proactive suggestions that surface useful next actions before conditions worsen.

## System Architecture

The system follows a simple decision pipeline:

User Input -> Intent Detection -> Context Layer -> Prediction Layer -> Decision Engine -> Response

How the flow works:

1. The user submits a natural-language request through the API.
2. Intent detection identifies whether the request is about entry, food, exit, or a combination of those goals.
3. The context layer loads stadium conditions such as gate crowd, stall wait times, and exit congestion.
4. The prediction layer estimates how those conditions are likely to change shortly.
5. The decision engine scores each available option and selects the best recommendation.
6. The response layer returns the recommendation, reasoning, alternatives, and proactive guidance.

## Google Cloud Integration

Stadium OS is designed for a simple Google Cloud deployment path:

- Cloud Run: hosts the containerized Flask API as a managed serverless service.
- Cloud Build: builds the application container from source and produces the deployment artifact.
- Artifact Registry: stores the built container image for repeatable deployments.

This setup keeps the system easy to ship for a hackathon while still following a production-style deployment pattern.

## How It Works

1. A user sends a query to the `/query` endpoint.
2. The app detects all matching intents in the query.
3. The system loads a stadium context snapshot with gates, food stalls, exits, and event phase.
4. A prediction pass adjusts the current context to estimate near-future congestion and wait times.
5. The decision engine ranks options using the selected priority model.
6. The app returns a structured response that includes the recommendation, reasoning, and any proactive advice.

## Assumptions

- Stadium conditions are represented by a controlled sample context rather than a live sensor feed.
- Crowd, wait-time, and congestion values are simplified to keep the demo deterministic and understandable.
- Predictions are short-horizon and rule-based, which is appropriate for a hackathon prototype but not a final operational model.
- The system assumes a user priority such as fastest, least crowd, or shortest distance.
- Google Maps integration is represented as a route hint abstraction and can be replaced with a live mapping service in production.

## Example Queries

- "What is the fastest way to get in?"
- "Where should I get food during halftime?"
- "I want food now and a good exit later."
- "Which gate has the least crowd right now?"
- "What is the best exit if I leave in 10 minutes?"
- "Help me choose between entry and food based on crowd and distance."

## API Endpoints

- `GET /` returns a basic health response for Cloud Run checks.
- `POST /query` accepts JSON with a `query` string and returns the assistant response.

Example request:

```bash
curl -X POST http://localhost:8080/query \
  -H "Content-Type: application/json" \
  -d '{"query":"Where should I enter and where can I get food quickly?"}'
```

Example response shape:

```json
{
  "response": "..."
}
```

## Local Run

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the app:

```bash
python app.py
```

The service listens on port `8080`.

## Deployment Notes

For Cloud Run deployment, build the container with Cloud Build, push the image to Artifact Registry, and deploy the image to Cloud Run. The included `Dockerfile` and `Procfile` support a straightforward container-first workflow.

## Project Positioning

Stadium OS is intentionally scoped as an operational decision layer for stadium visitors. Its value is not in open-ended chat; its value is in turning live venue conditions into immediate, useful action.