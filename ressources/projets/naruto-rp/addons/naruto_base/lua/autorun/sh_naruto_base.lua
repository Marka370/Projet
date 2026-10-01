--[[
    Naruto Base — chargeur de l'addon
    Charge les fichiers selon leur préfixe :
      sh_  partagé (serveur + client)
      sv_  serveur uniquement
      cl_  client uniquement (envoyé aux joueurs par le serveur)
]]

NB = NB or {}
NB.Version = "0.1.0"

local BASE = "naruto_base/"

local function loadFile(path)
    local name = path:match("([^/]+)$") or path
    local prefix = name:sub(1, 3)

    if prefix == "sv_" then
        if SERVER then include(path) end
    elseif prefix == "cl_" then
        if SERVER then
            AddCSLuaFile(path)
        else
            include(path)
        end
    else
        if SERVER then AddCSLuaFile(path) end
        include(path)
    end
end

-- L'ordre compte : la config et le cœur avant tout le reste.
local ORDER = {
    "sh_config.lua",
    "sh_lang.lua",
    "sh_core.lua",
    "sh_jutsu.lua",

    "sv_data.lua",
    "sv_player.lua",
    "sv_jutsu.lua",
    "sv_commands.lua",

    "cl_theme.lua",
    "cl_net.lua",
    "cl_notify.lua",
    "cl_hud.lua",
    "cl_hotbar.lua",
    "cl_menu_creation.lua",
    "cl_menu_jutsu.lua",
}

for _, fileName in ipairs(ORDER) do
    loadFile(BASE .. fileName)
end

-- Les jutsus : un fichier par technique dans naruto_base/jutsus/
local jutsuFiles = file.Find(BASE .. "jutsus/*.lua", "LUA")
table.sort(jutsuFiles)
for _, fileName in ipairs(jutsuFiles) do
    loadFile(BASE .. "jutsus/" .. fileName)
end

NB.BuildIndexes()
hook.Run("NB_Loaded")
NB.Log("version " .. NB.Version .. " chargée (" .. #NB.JutsuList .. " jutsus)")
