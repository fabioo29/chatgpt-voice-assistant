build-local:
	sudo docker build . -t chatgpt-telegram:latest

deploy-local:
	sudo docker rm chatgpt-telegram -f || true
	sudo docker run -d --network=host --restart=always -v ${PWD}/.env:/app/.env:ro --name chatgpt-telegram chatgpt-telegram:latest

zip-cookies:
	rm -rf cookies.tar.* && tar cvzf - cookies/ | split --bytes=200MB - cookies.tar.gz.

logs:
	docker logs -f chatgpt-telegram