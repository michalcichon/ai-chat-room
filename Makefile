BIN ?= .venv/bin
RUN := .run

.PHONY: up client down

up: ## start server + one agent in the background, print PIDs
	@mkdir -p $(RUN)
	@if [ -f $(RUN)/server.pid ] && kill -0 $$(cat $(RUN)/server.pid) 2>/dev/null; then \
		echo "already running, use 'make down' first"; exit 1; fi
	@nohup $(BIN)/aichat-server > $(RUN)/server.log 2>&1 & echo $$! > $(RUN)/server.pid
	@sleep 1
	@kill -0 $$(cat $(RUN)/server.pid) 2>/dev/null || { \
		echo "server failed to start, see $(RUN)/server.log:"; tail -n 20 $(RUN)/server.log; \
		rm -f $(RUN)/server.pid; exit 1; }
	@nohup $(BIN)/aichat-agent > $(RUN)/agent.log 2>&1 & echo $$! > $(RUN)/agent.pid
	@sleep 1
	@kill -0 $$(cat $(RUN)/agent.pid) 2>/dev/null || { \
		echo "agent failed to start, see $(RUN)/agent.log:"; tail -n 20 $(RUN)/agent.log; \
		rm -f $(RUN)/agent.pid; exit 1; }
	@echo "server pid $$(cat $(RUN)/server.pid), agent pid $$(cat $(RUN)/agent.pid)"
	@echo "logs: $(RUN)/server.log, $(RUN)/agent.log - join the chat with: make client"

client: ## open the terminal client
	@$(BIN)/aichat-client

down: ## stop the server and agent started by 'make up' (logs are kept)
	@for p in agent server; do \
		if [ -f $(RUN)/$$p.pid ]; then kill $$(cat $(RUN)/$$p.pid) 2>/dev/null || true; rm -f $(RUN)/$$p.pid; fi; \
	done
	@echo "stopped"
