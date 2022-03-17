.PHONY: run setup clean

AMBER := \033[1;33m
GREEN := \033[1;32m
NO_COLOR := \033[0m

all : run setup 
	@printf "🚀 ${GREEN}Running NuttyNios-Client! ${NO_COLOR}\n"

run : setup
	@python src/main.py

setup : requirements.txt
	@printf "${AMBER}▶ Installing dependencies ... ${NO_COLOR}\n"
	@pip install -r requirements.txt
	@printf "${GREEN}... Dependencies installed! ${NO_COLOR}\n"

clean : 
	@printf "${AMBER}▶ Cleaning previous builds ... ${NO_COLOR}\n"
	@rm -rf __pycache__
	@printf "${GREEN}... Previous builds cleaned! ${NO_COLOR}\n"
