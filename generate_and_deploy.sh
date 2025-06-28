#!/bin/zsh


rm output/*

GENERATED_MAP="worlds/megaquarium/data/sample_map2.json"
MEGAQUARIUM_PATH="/home/sachour/.local/share/Megaquarium/Saves"

if python3 Generate.py; then
    echo "world generation succeeded."
    ARCHIPELAGOGAME=$(ls output)
    unzip -d output output/$ARCHIPELAGOGAME
    cp output/archipelago_map.sav $MEGAQUARIUM_PATH/archipelago_map.sav
    python3 MultiServer.py output/${ARCHIPELAGOGAME}
else
    echo "Failed to generate world."
    exit 1
fi

