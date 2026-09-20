run_with_google_translate:
	cp -f .env.example .env
	sed -i 's/^TRANSLATE_MODEL=.*/TRANSLATE_MODEL=google_translator/' .env
	docker compose up -d turbo-ocr translator-backend

run_with_facebook_nllb_translate:
	cp -f .env.example .env
	sed -i 's/^TRANSLATE_MODEL=.*/TRANSLATE_MODEL=facebook_nllb_translator/' .env
	docker compose up -d turbo-ocr translator-backend


run_with_ai:
	cp -f .env.example .env
	sed -i 's/^TRANSLATE_MODEL=.*/TRANSLATE_MODEL=hy-mt/' .env
	docker compose start llama-server turbo-ocr translator-backend

run_with_mymemory_translator:
	cp -f .env.example .env || exit 1
	sed -i "s/^TRANSLATE_MODEL=.*/TRANSLATE_MODEL=mymemory_translator/" .env
	docker compose up -d turbo-ocr libretranslate translator-backend

run_with_libretranslate:
	cp -f .env.example .env || exit 1
	sed -i "s/^TRANSLATE_MODEL=.*/TRANSLATE_MODEL=libretranslate_translator/" .env
	docker compose up -d turbo-ocr libretranslate translator-backend


stop:
	docker compose stop translator-backend
	docker compose stop turbo-ocr
	docker compose stop libretranslate

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