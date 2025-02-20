.DEFAULT_GOAL := dev

# Docker Compose Base
COMPOSE_BASE = docker compose -f docker-compose.base.yml

# File where the last raised environment is stored
LAST_ENV_FILE = .last_env

# Function to save the current environment
define save_env
	echo "$(1)" > $(LAST_ENV_FILE)
endef

# Function to load the active environment or display an error
define LOAD_ENV
	@if [ ! -f $(LAST_ENV_FILE) ]; then \
		echo "❌ No active environment found. First run ‘make dev’ or ‘make prod’."; \
		exit 1; \
	fi; \
	COMPOSE_ENV=$$(cat $(LAST_ENV_FILE))
endef

.PHONY: dev
dev:
	$(COMPOSE_BASE) -f docker-compose.dev.yml up -d --build
	$(call save_env, -f docker-compose.base.yml -f docker-compose.dev.yml)
	$(MAKE) remove-base-containers

.PHONY: prod
prod:
	@if echo "$(MAKECMDGOALS)" | grep -q -- "--watchtower"; then \
		echo "🚀 Deploying production WITH Watchtower..."; \
		$(COMPOSE_BASE) -f docker-compose.prod.yml -f docker-compose.watchtower.yml up -d --build; \
		$(call save_env, -f docker-compose.base.yml -f docker-compose.prod.yml -f docker-compose.watchtower.yml); \
	else \
		echo "🚀 Deploying production WITHOUT Watchtower..."; \
		$(COMPOSE_BASE) -f docker-compose.prod.yml up -d --build; \
		$(call save_env, -f docker-compose.base.yml -f docker-compose.prod.yml); \
	fi; \
	$(MAKE) remove-base-containers

.PHONY: prod-ssl
prod-ssl:
	@if echo "$(MAKECMDGOALS)" | grep -q -- "--watchtower"; then \
		echo "🚀 Deploying production SSL WITH Watchtower..."; \
		$(COMPOSE_BASE) -f docker-compose.prod.yml -f docker-compose.prod.ssl.yml -f docker-compose.watchtower.yml up -d --build; \
		$(call save_env, -f docker-compose.base.yml -f docker-compose.prod.yml -f docker-compose.prod.ssl.yml -f docker-compose.watchtower.yml); \
	else \
		echo "🚀 Deploying production SSL WITHOUT Watchtower..."; \
		$(COMPOSE_BASE) -f docker-compose.prod.yml -f docker-compose.prod.ssl.yml up -d --build; \
		$(call save_env, -f docker-compose.base.yml -f docker-compose.prod.yml -f docker-compose.prod.ssl.yml); \
	fi; \
	$(MAKE) remove-base-containers

.PHONY: prod-webhook
prod-webhook:
	$(COMPOSE_BASE) -f docker-compose.prod.yml -f docker-compose.prod.webhook.yml up -d --build
	$(call save_env, -f docker-compose.base.yml -f docker-compose.prod.yml -f docker-compose.prod.webhook.yml)
	$(MAKE) remove-base-containers

.PHONY: remove-base-containers
remove-base-containers:
	@echo "🛑 Removing base and runtime containers..."
	@docker compose -f docker-compose.base.yml rm -f base runtime || true

.PHONY: down
down:
	$(call LOAD_ENV); \
	docker compose $$COMPOSE_ENV down;

.PHONY: up
up:
	$(call LOAD_ENV); \
	docker compose $$COMPOSE_ENV up -d;

.PHONY: restart
restart:
	$(call LOAD_ENV); \
	docker compose $$COMPOSE_ENV down; \
	$(MAKE) remove-base-containers; \
	docker compose $$COMPOSE_ENV up -d

.PHONY: logs
logs:
	$(call LOAD_ENV); \
	docker compose $$COMPOSE_ENV logs -f

.PHONY: rebuild
rebuild:
	$(call LOAD_ENV); \
	docker compose $$COMPOSE_ENV down; \
	$(MAKE) remove-base-containers; \
	echo "🧹 Cleaning Docker..."; \
	docker system prune -af; \
	echo "🚀 Building images..."; \
	docker compose $$COMPOSE_ENV build; \
	echo "🔄 Starting services..."; \
	docker compose $$COMPOSE_ENV up -d; \
	$(MAKE) remove-base-containers

.PHONY: clean
clean:
	@echo "🛑 Stopping all containers..."
	@docker stop $$(docker ps -aq) || true

	@echo "🗑️ Removing all containers..."
	@docker rm $$(docker ps -aq) || true

	@echo "🧹 Removing all volumes..."
	@docker volume rm $$(docker volume ls -q) || true

	@echo "🔥 Removing all images..."
	@docker rmi -f $$(docker images -q) || true

	@echo "🔗 Removing all custom networks..."
	@docker network prune -f || true

	@echo "✅ Cleanup completed."

.PHONY: ssl-setup
ssl-setup:
	@while true; do \
		echo "Enter your domain (including 'www' and the extension, e.g., www.exampledomain.com):"; \
		read domain; \
		echo "Enter your email: "; \
		read email; \
		echo "Configured with the domain $$domain"; \
		echo "Configured with the email $$email"; \
		echo ""; \
		echo "Are you sure the entered information is correct? [y/n]"; \
		read confirm; \
		if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
			break; \
		else \
			echo "Please re-enter the information."; \
			echo ""; \
		fi; \
	done; \
	echo "🔧 Configuring SSL with domain: $$domain and email: $$email"; \
	cp ./nginx/nginx.prod.no-ssl.conf.template ./nginx/nginx.prod.ssl.conf; \
	sed -i "s/{{domain}}/$$domain/g" ./nginx/nginx.prod.ssl.conf; \
	echo "🚀 Starting Nginx without SSL to obtain certificates..."; \
	docker compose -f docker-compose.base.yml -f docker-compose.prod.yml -f docker-compose.prod.ssl.yml up -d nginx; \
	echo "🔐 Requesting SSL certificate with Certbot..."; \
	docker compose -f docker-compose.base.yml -f docker-compose.prod.yml -f docker-compose.prod.ssl.yml run --rm certbot certonly --webroot --webroot-path=/var/www -d $$domain --email $$email --agree-tos --no-eff-email --force-renewal; \
	cp ./nginx/nginx.prod.ssl.conf.template ./nginx/nginx.prod.ssl.conf; \
	sed -i "s/{{domain}}/$$domain/g" ./nginx/nginx.prod.ssl.conf; \
	echo "🔄 Restarting Nginx with SSL configuration..."; \
	docker compose -f docker-compose.base.yml -f docker-compose.prod.yml -f docker-compose.prod.ssl.yml down; \
	docker compose -f docker-compose.base.yml -f docker-compose.prod.yml -f docker-compose.prod.ssl.yml up -d --build; \
	echo "✅ SSL setup completed!"

.PHONY: ssl-renew
ssl-renew:
	@echo "🔄 Renewing SSL certificates..."; \
	docker compose -f docker-compose.base.yml -f docker-compose.prod.yml -f docker-compose.prod.ssl.yml run --rm certbot renew --webroot --webroot-path=/var/www; \
	echo "🔄 Restarting Nginx to apply new certificates..."; \
	docker compose -f docker-compose.base.yml -f docker-compose.prod.yml -f docker-compose.prod.ssl.yml restart nginx; \
	echo "✅ SSL certificates renewed successfully!"
