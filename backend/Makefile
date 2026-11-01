run_with_google_translate:
	cp -f .env.example .env
	sed -i 's/^TRANSLATE_MODEL=.*/TRANSLATE_MODEL=google_translator/' .env
	docker compose up -d turbo-ocr translator-backend
	bash run-backend.sh

run_with_facebook_nllb_translate:
	cp -f .env.example .env
	sed -i 's/^TRANSLATE_MODEL=.*/TRANSLATE_MODEL=facebook_nllb_translator/' .env
	docker compose up -d turbo-ocr translator-backend
	bash run-backend.sh

run_with_llm_HY_MT2_1.8B:
	cp -f .env.example .env || exit 1
	sed -i 's/^TRANSLATE_MODEL=.*/TRANSLATE_MODEL=hy-mt/' .env
	sed -i 's/^LLAMA_MODEL=.*/LLAMA_MODEL=Hy-MT2-1.8B-Q8_0.gguf/' .env
	docker compose up -d llama-server turbo-ocr translator-backend
	bash run-backend.sh &

run_with_llm_HY_MT2_7B:
	cp -f .env.example .env || exit 1
	sed -i 's/^TRANSLATE_MODEL=.*/TRANSLATE_MODEL=hy-mt/' .env
	sed -i 's/^LLAMA_MODEL=.*/LLAMA_MODEL=Hy-MT2-7B-Q4_K_M.gguf/' .env
	docker compose up -d llama-server turbo-ocr translator-backend
	bash run-backend.sh &

run_with_mymemory_translator:
	cp -f .env.example .env || exit 1
	sed -i "s/^TRANSLATE_MODEL=.*/TRANSLATE_MODEL=mymemory_translator/" .env
	docker compose up -d turbo-ocr libretranslate translator-backend
	bash run-backend.sh &

run_with_libretranslate:
	cp -f .env.example .env || exit 1
	sed -i "s/^TRANSLATE_MODEL=.*/TRANSLATE_MODEL=libretranslate_translator/" .env
	docker compose up -d turbo-ocr libretranslate translator-backend
	bash run-backend.sh &

run_with_llm_index_translate_2b:
	cp -f .env.example .env || exit 1
	sed -i 's/^SOURCE_LANG=.*/SOURCE_LANG=auto/' .env
	sed -i 's/^TRANSLATE_MODEL=.*/TRANSLATE_MODEL=index_translate_translator/' .env
	sed -i 's/^LLAMA_MODEL=.*/LLAMA_MODEL=Index-Translate-2B.Q8_0.gguf/' .env
	docker compose up -d turbo-ocr llama-server translator-backend
	bash run-backend.sh

run_with_llm:
	sed -i 's/^SOURCE_LANG=.*/SOURCE_LANG=auto/' .env
	sed -i 's/^TRANSLATE_MODEL=.*/TRANSLATE_MODEL=llm_translator/' .env
	sed -i 's/^LLAMA_MODEL=.*/LLAMA_MODEL=/' .env
	docker compose up -d turbo-ocr translator-backend
	bash run-backend.sh

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