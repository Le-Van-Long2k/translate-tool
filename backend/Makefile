run_with_google_translate:
	cp -f .env.example .env
	sed -i 's/^TRANSLATE_MODEL=.*/TRANSLATE_MODEL=google_translator/' .env
	docker compose up -d --build turbo-ocr translator-backend

run_with_ai:
	cp -f .env.example .env
	sed -i 's/^TRANSLATE_MODEL=.*/TRANSLATE_MODEL=hy-mt/' .env
	docker compose up -d --build

stop:
	docker compose stop 

run_backend:
	docker exec -it translator-backend bash run-backend.sh

build_first_backend:
	rm -rf .venv
	rm -rf logs/*
	cp -f .env.example .env
	docker compose up -d --build

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