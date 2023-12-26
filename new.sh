#!/bin/zsh
if [ $# -eq 0 ]; then
    # Default behavior when no arguments are provided
    npx zenn new:article --slug myarticle-slug --title mytitle --type tech --emoji 🦀
elif [ $# -eq 1 ]; then
    # Actions to perform when arguments are provided
    npx zenn new:article --slug $1 --title mytitle --type tech --emoji 🦀
    # Additional logic based on arguments
else
    # Actions to perform when more than one argument is provided
    echo "Too many arguments"
fi