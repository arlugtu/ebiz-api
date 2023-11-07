
local-build:
	docker-compose build


local-run: local-build
	 docker-compose up -d

build:
	docker-compose -f docker-compose-prod.yaml build


up: build
	docker-compose -f docker-compose-prod.yaml up -d

down:
	 docker-compose -f docker-compose-prod.yaml down