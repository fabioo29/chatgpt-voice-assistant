build-local:
	docker build . -t chatgpt-telegram:latest --no-cache

deploy-local:
	docker rm chatgpt-telegram -f || true
	docker run -d --network=host --restart=always -v ${PWD}/.env:/app/.env:ro --name chatgpt-telegram chatgpt-telegram:latest

push-image:
	docker save chatgpt-telegram:latest | gzip > chatgpt-telegram.tar.gz
	scp chatgpt-telegram.tar.gz ${host}:
	rm -f chatgpt-telegram.tar.gz
	ssh ${host} "zcat chatgpt-telegram.tar.gz | sudo docker load"
	ssh ${host} "sudo docker system prune -f"
	ssh ${host} "rm -f chatgpt-telegram.tar.gz"

deploy-host:
	ssh ${host} "sudo docker rm chatgpt-telegram -f || true"
	ssh ${host} "sudo docker run -d --restart=always --name chatgpt-telegram chatgpt-telegram:latest"

zip-cookies:
	rm -rf cookies.tar.* && tar cvzf - cookies/ | split --bytes=200MB - cookies.tar.gz.

logs:
	docker logs -f chatgpt-telegram

run-pipeline-local:
	make zip-cookies
	make build-local
	make deploy-local

run-pipeline-host:
	make zip-cookies
	make build-local
	make push-image
	make deploy-host