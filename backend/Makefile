test:
	pwd

build:
	docker compose up -d --build

commit:
	git add .
	git commit -m "Update code"

run_fastapi:
	uv run uvicorn main:app --reload --host 0.0.0.0 --port 8052

log:
	docker logs -f backend-translator_backend-1

rebuild_fastapi:
	docker compose stop translator_backend
	docker compose up -d --build translator_backend