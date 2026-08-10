.PHONY: install start stop deploy test lint config gpu

install:
	./scripts/install.sh

start:
	./scripts/start.sh

stop:
	./scripts/stop.sh

deploy:
	./scripts/deploy.sh

config:
	docker compose config

test:
	python -m pytest -q

gpu:
	./scripts/check-gpu.sh
