run:
	cp -f .env.example .env
	docker compose up -d --build turbo-ocr translator-backend

run_all:
	cp -f .env.example .env
	docker compose up -d --build

build_new:
	sudo rm -rf .venv
	sudo rm -rf logs/*
	docker compose up -d --build

commit:
	git add .
	git commit -m "Update code"

run_backend:
	docker exec -it translator-backend bash run-backend.sh

rebuild_fastapi:
	docker compose stop translator-backend
	docker compose up -d --build translator-backend

check_size_docker:
	docker system df

remove_all_docker:
	docker ps -aq | xargs -r docker rm -f
	docker images -aq | xargs -r docker rmi -f
	docker volume ls -q | xargs -r docker volume rm
	docker network prune -f
	docker builder prune -a -f
	docker system prune -a --volumes -f

docker_status:
	docker stats