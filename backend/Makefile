test:
	pwd

build_new:
	sudo rm -rf .venv
	sudo rm -rf logs/*
	docker compose up -d --build

commit:
	git add .
	git commit -m "Update code"

run_fastapi:
	uv run uvicorn main:app --host 0.0.0.0 --port 8052

log:
	docker logs -f backend-translator_backend-1

rebuild_fastapi:
	docker compose stop translator_backend
	docker compose up -d --build translator_backend

check_size_docker:
	docker system df

remove_all_docker:
	docker ps -aq | xargs -r docker rm -f
	docker images -aq | xargs -r docker rmi -f
	docker volume ls -q | xargs -r docker volume rm
	docker network prune -f
	docker builder prune -a -f
	docker system prune -a --volumes -f