.PHONY: help backend frontend demo test zip

help:
	@echo "PactBounty commands"
	@echo "  make backend   - run FastAPI backend"
	@echo "  make frontend  - run Next.js frontend"
	@echo "  make demo      - run local mock agent workflow once"
	@echo "  make test      - run backend tests"
	@echo "  make zip       - create pactbounty.zip"

backend:
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

frontend:
	cd frontend && npm run dev

demo:
	cd backend && python -m app.scripts.run_demo

test:
	cd backend && python -m pytest -q

zip:
	cd .. && zip -r pactbounty.zip pactbounty -x "pactbounty/frontend/node_modules/*" "pactbounty/backend/.venv/*" "pactbounty/backend/storage/*" "pactbounty/contracts/out/*" "pactbounty/contracts/cache/*"
