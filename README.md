# 🧠 LangChain Agent with Routing and Google Calendar Tools

This project is a LangChain-based AI agent designed to route user questions intelligently between two specialized models: a **General Assistant** and a **Developer Assistant**. The General Assistant is further enhanced with tools to interact with **Google Calendar**, allowing it to **read** and **write events**.

## 🚀 Getting Started

To launch the agent in development mode, simply run:

```bash
langchain dev
```

Make sure your environment is properly configured with any required API keys or credentials (e.g., for Google Calendar access).

## 🧭 Architecture Overview

The core of this agent is a **Router Chain**, which analyzes each incoming question and decides which of the two expert agents should respond:

- **General Model**
  - Focused on everyday tasks and productivity-related queries.
  - Equipped with two tools:
    - `get_calendar_events`: Fetches upcoming events.
    - `create_calendar_event`: Adds new events to your calendar.
- **Developer Model**
  - Specialized in technical questions, programming help, and dev workflows.

This modular approach allows the system to deliver more accurate and context-aware responses based on the user’s intent.

## 🛠️ Tools

### General Model Tools

| Tool Name              | Description                             |
|------------------------|-----------------------------------------|
| `get_calendar_events`  | Retrieves upcoming events from Calendar |
| `create_calendar_event`| Creates new events in Calendar          |

These tools require valid OAuth credentials and appropriate permissions to access the user's Google Calendar.

