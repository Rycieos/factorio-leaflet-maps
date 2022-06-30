# Factorio to Leaflet Maps

A Python script to convert [Factorio](http://factorio.com/) screenshots into [Leaflet](https://leafletjs.com/) map tiles.

## Getting Factorio Screenshots

1. In Factorio, open the console. The default hotkey for the console is **`**.
2. Paste the following command and press **Enter**.

```(lua)
/c __space-exploration__
json='';

for _, surface in pairs(game.surfaces) do
    if Zone.from_surface(surface) then
        if (json ~= '') then
            json=json..', ';
        end;
        json=json..'"'..surface.index..'": "'..surface.name..'"';
        for x=-1000,1000 do
            for y=-1000,1000 do
                if game.forces["player"].is_chunk_charted(surface, {x, y}) then
                    game.take_screenshot{surface=surface, show_entity_info=true, daytime=0, water_tick=0, zoom=1, resolution={1024,1024}, position={x=32*x+16,y=32*y+16}, path="factoriomaps/"..surface.index.."/chunk_"..x.."_"..y..".jpg"};
                end;
            end;
        end;
    end;
end;

zones = {}
player = game.player;
for _, zone in pairs(global.zone_index) do
    if zone.type == "star" and Zone.is_visible_to_force(zone, game.player.force.name) then
        table.insert(zones, zone);
        if (json ~= '') then
            json=json..', ';
        end;
        json=json..'"virtual-'..zone.index..'": "'..zone.name..'"';
    end;
end;

script.on_event(defines.events.on_tick, function(event)
    zone = table.remove(zones);
    if not zone then
        script.on_event(defines.events.on_tick, nil);

        MapView.start_interstellar_map(player);
        for x=-1000,1000 do
            for y=-1000,1000 do
                if game.forces["player"].is_chunk_charted(player.surface, {x, y}) then
                    game.take_screenshot{surface=player.surface, show_entity_info=true, daytime=0, water_tick=0, zoom=1, resolution={1024,1024}, position={x=32*x+16,y=32*y+16}, path="factoriomaps/virtual-0/chunk_"..x.."_"..y..".jpg"}
                end;
            end;
        end;
        game.set_wait_for_screenshots_to_finish();
        return;
    end;

    MapView.start_system_map(player, zone);
    for x=-1000,1000 do
        for y=-1000,1000 do
            if game.forces["player"].is_chunk_charted(player.surface, {x, y}) then
                game.take_screenshot{surface=player.surface, show_entity_info=true, daytime=0, water_tick=0, zoom=1, resolution={1024,1024}, position={x=32*x+16,y=32*y+16}, path="factoriomaps/virtual-"..zone.index.."/chunk_"..x.."_"..y..".jpg"};
            end;
        end;
    end;
    game.set_wait_for_screenshots_to_finish();
end);

json=json..', "virtual-0": "Interstellar Map"';
game.write_file("factoriomaps/surfaces.json", "{"..json.."}");
```

> **NOTE:** Using console commands disables achievements in your current game. To retain achievements, reload your save after running the command.

3. A set of screenshots is taken and saved to `%APPDATA%\Factorio\script-output\factoriomaps`

## Getting Leaflet Tiles

### Script Requirements
  * [Python 3.6+](https://www.python.org/downloads/release/latest)
  * [Pillow](https://pypi.org/project/Pillow/)
  * [tqdm](https://pypi.org/project/tqdm/)
  
1. Execute the script: `python3 factoriomap.py [source] [destination]`
  * **Source:** The path to the directory containing the screenshots, or the path to a tar file containing the screenshots.
  * **Destination:** The path to a directory to hold the Leaflet tiles.
  
> **NOTE:** Depending on your system configuration, the command to run a Python 3 script (`python3` above) may differ. Use the appropriate command for your system.
> **NOTE:** The tar file option is useful if the screenshots need to be uploaded to a remote server before running the script.

2. The screenshots are converted to Leaflet tiles.

## Creating a Leaflet Map

1. Create an HTML page to launch Leaflet. A simple example page is included in the repository. Change `PATH_TO_TILE_DIRECTORY` to the actual path of the tile directory.

2. For further customation, see the Leaflet documentation.
