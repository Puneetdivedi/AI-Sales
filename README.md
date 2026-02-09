# AI Sales and Monitoring Agent (Beginner)

This is a simple, beginner-friendly AI sales assistant and monitoring tool you can run from the terminal.
It works without an API key and can be upgraded to use a real LLM later.

## 1) Setup (Windows)

1. Open VS Code.
2. Open the folder `Ai Agent`.
3. Open a terminal in VS Code.

Create and activate a virtual environment:

```bash
python -m venv venv
venv\Scripts\activate
```


Install dependencies:

```bash
pip install -r requirements.txt
```

## 2) Configure

Open `.env` and update:

- `COMPANY_NAME`
- `COMPANY_EMAIL`
- `ALERT_EMAIL`

Optional LLM settings (only if you want to connect a real AI API):

- `LLM_PROVIDER=openai_compatible`
- `API_KEY=your_api_key_here`
- `LLM_ENDPOINT=your-provider-endpoint`
- `LLM_MODEL=your-model-name`

If you do not set these, the app uses a safe fallback response.
When you run it, you will see an AI status line telling you if it is enabled.

## 3) Run

```bash
python main.py
```

## 4) What this  do

- Answers customer questions (AI if configured, fallback if not)
- Logs interactions to `data/interactions.csv`
- Creates sample data files automatically
- Generates a daily sales report and alerts

## 5) Files.

- `main.py` entry point
- `sales_agent.py` sales assistant
- `monitoring.py` reporting and alerts
- `llm_client.py` AI provider wrapper
- `config.py` configuration + data setup
- `data/` CSV storage
- `logs/` reserved for future logs
