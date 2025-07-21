PWD = $(shell pwd)

LOCAL_DIR = $(PWD)/venv/bin
PYTHON = $(LOCAL_DIR)/python
PYTHON3 = python3.11

help:  ## Show help
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m\033[0m\n"} /^[$$()% a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

install: ## Install the Python libraries in a virtual environment
	@$(PYTHON) -m pip install --no-cache-dir -r requirements.txt

compile: ## Compile the requirements.txt file to requirements.lock
	@pip-compile --output-file=requirements.txt --strip-extras pyproject.toml

run:  ## Run the application client
	@$(PYTHON) -m streamlit run app/main.py