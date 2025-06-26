#!/bin/zsh


rm output/*
if python3 Generate.py; then
    echo "world generation succeeded."
    ARCHIPELAGOGAME=$(ls output)
    python3 MultiServer.py output/${ARCHIPELAGOGAME}
else
    echo "Failed to generate world."
    exit 1
fi

