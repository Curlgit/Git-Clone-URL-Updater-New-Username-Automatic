#!/bin/bash

# Git Clone Fix Installer
# Developed by Curlgit

C_GREEN="\033[1;32m"
C_RED="\033[1;31m"
C_CYAN="\033[1;36m"
C_RESET="\033[0m"

echo -e "${C_CYAN}[*] Installing Git Clone Fix...${C_RESET}"

# Install Python and Git
if [ -n "$PREFIX" ] && [ -d "$PREFIX" ]; then
    pkg update -y && pkg install python git -y || exit 1
else
    sudo apt update && sudo apt install python3 python3-pip git -y || exit 1
fi

# Install required Python libraries
echo -e "${C_CYAN}[*] Installing requests and colorama...${C_RESET}"

python -m pip install requests colorama || {
    echo -e "${C_RED}[!] Library installation failed.${C_RESET}"
    exit 1
}

echo -e "${C_GREEN}[✔] Installation completed successfully!${C_RESET}"
echo -e "${C_CYAN}[i] Run your tool using:${C_RESET}"
echo -e "${C_GREEN}python git clone update.py${C_RESET}"