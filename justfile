hello:
    echo "Hello world"

ai-client:
    python3 app/ai/client.py


backend:
    cd /home/eric/GitHub/issue-pilot/backend && python -m uvicorn app.main:app --reload

frontend:
    cd /home/eric/GitHub/issue-pilot/frontend && npm run dev
