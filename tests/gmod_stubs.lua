-- Simulation minimale de l'API Garry's Mod (côté serveur) pour tester
-- naruto_base en dehors du jeu. Seules les fonctions utilisées sont simulées.

SERVER, CLIENT = true, false

-- Constantes : toute globale KEY_/ACT_/DMG_/MASK_/... inconnue vaut un nombre.
local PREFIXES = { "KEY_", "ACT_", "DMG_", "MASK_", "COLLISION_GROUP_", "GESTURE_SLOT_", "TEXT_ALIGN_" }
local constCounter = 1000
setmetatable(_G, {
    __index = function(t, k)
        if type(k) == "string" then
            for _, p in ipairs(PREFIXES) do
                if k:sub(1, #p) == p then
                    constCounter = constCounter + 1
                    rawset(t, k, constCounter)
                    return constCounter
                end
            end
        end
        return nil
    end,
})

-- ───────────── Fonctions de base GMod
function isstring(v) return type(v) == "string" end
function isnumber(v) return type(v) == "number" end
function istable(v) return type(v) == "table" end
function isfunction(v) return type(v) == "function" end
function IsValid(v) return v ~= nil and v ~= false and (type(v) ~= "table" or v.IsValid == nil or v:IsValid()) end
function Color(r, g, b, a) return { r = r, g = g, b = b, a = a or 255 } end
function math.Clamp(v, lo, hi) return math.min(math.max(v, lo), hi) end
function math.Round(v) return math.floor(v + 0.5) end

TIME = 100
function CurTime() return TIME end

LOGS = {}
local realPrint = print
function print(...) local t = {} for i = 1, select("#", ...) do t[#t + 1] = tostring(select(i, ...)) end LOGS[#LOGS + 1] = table.concat(t, " ") end

-- ───────────── hook
hook = { list = {} }
function hook.Add(event, name, fn) hook.list[event] = hook.list[event] or {}; hook.list[event][name] = fn end
function hook.Remove(event, name) if hook.list[event] then hook.list[event][name] = nil end end
function hook.Run(event, ...)
    for _, fn in pairs(hook.list[event] or {}) do
        local a, b = fn(...)
        if a ~= nil then return a, b end
    end
end

-- ───────────── timer
timer = { timers = {}, simple = {} }
function timer.Create(name, delay, reps, fn) timer.timers[name] = { delay = delay, fn = fn } end
function timer.Simple(delay, fn) table.insert(timer.simple, { at = TIME + delay, fn = fn }) end
function timer.RunTimer(name) timer.timers[name].fn() end
function timer.Advance(dt)
    TIME = TIME + dt
    local pending = timer.simple
    timer.simple = {}
    for _, t in ipairs(pending) do
        if t.at <= TIME then t.fn() else table.insert(timer.simple, t) end
    end
end

-- ───────────── net (le message en cours est une simple liste de valeurs)
net = { receivers = {}, sent = {}, current = nil }
util = {}
function util.AddNetworkString(name) end
function net.Start(name) net.current = { name = name, values = {} } end
local function write(v) table.insert(net.current.values, v) end
net.WriteString, net.WriteFloat, net.WriteEntity = write, write, write
function net.WriteUInt(v) write(v) end
function net.Send(ply) net.current.to = ply; table.insert(net.sent, net.current) end
function net.Broadcast() net.current.to = "all"; table.insert(net.sent, net.current) end
function net.Receive(name, fn) net.receivers[name] = fn end
local reading
local function read() return table.remove(reading, 1) end
net.ReadString, net.ReadFloat, net.ReadEntity = read, read, read
function net.ReadUInt() return read() end
-- Simule un message envoyé par un client
function net.FromClient(ply, name, ...)
    reading = { ... }
    net.receivers[name](0, ply)
end
function net.Last(name, ply)
    for i = #net.sent, 1, -1 do
        local m = net.sent[i]
        if m.name == name and (ply == nil or m.to == ply) then return m end
    end
end

-- ───────────── sql (SQLite simulé pour une seule table clé/valeur)
DB = {}
sql = {}
function sql.SQLStr(s) return "'" .. tostring(s):gsub("'", "''") .. "'" end
local function unquote(s) return (s:gsub("''", "'")) end
function sql.Query(q)
    if q:find("^CREATE") then return nil end
    local id, data = q:match("^REPLACE INTO %S+ %(steamid, data%) VALUES %('(.-)', '(.*)'%)$")
    if id then DB[unquote(id)] = unquote(data); return nil end
    id = q:match("^DELETE FROM %S+ WHERE steamid = '(.-)'$")
    if id then DB[unquote(id)] = nil; return nil end
    error("requête SQL non simulée : " .. q)
end
function sql.QueryValue(q)
    local id = q:match("WHERE steamid = '(.-)'$")
    return DB[unquote(id)]
end
function sql.LastError() return "" end

-- JSON fourni par Python (voir le test)
util.TableToJSON = function(t) return PY_TO_JSON(t) end
util.JSONToTable = function(s) return PY_FROM_JSON(s) end

-- ───────────── Joueurs
local PLAYER = {}
PLAYER.__index = PLAYER
function FindMetaTable(name) assert(name == "Player"); return PLAYER end

ALL_PLAYERS = {}
player = {}
function player.GetAll() return ALL_PLAYERS end

local nextId = 1
function NewPlayer(nick)
    local ply = setmetatable({ nick = nick, nw = {}, alive = true, health = 100, crouching = false,
        speed = 0, admin = false, valid = true, chat = {} }, PLAYER)
    ply.steamid64 = "7656119800000000" .. nextId
    nextId = nextId + 1
    table.insert(ALL_PLAYERS, ply)
    return ply
end
function RemovePlayer(ply)
    for i, p in ipairs(ALL_PLAYERS) do if p == ply then table.remove(ALL_PLAYERS, i) end end
    ply.valid = false
end

function PLAYER:IsValid() return self.valid end
function PLAYER:IsPlayer() return true end
function PLAYER:Nick() return self.nick end
function PLAYER:SteamID64() return self.steamid64 end
function PLAYER:SteamID() return "STEAM_0:0:" .. self.steamid64:sub(-4) end
function PLAYER:Alive() return self.alive end
function PLAYER:IsAdmin() return self.admin end
function PLAYER:Crouching() return self.crouching end
function PLAYER:GetVelocity() local s = self.speed; return { Length = function() return s end } end
function PLAYER:ChatPrint(t) table.insert(self.chat, t) end
function PLAYER:Health() return self.health end
local function nwGet(self, k, d) local v = self.nw[k]; if v == nil then return d end; return v end
local function nwSet(self, k, v) self.nw[k] = v end
PLAYER.GetNW2Float, PLAYER.GetNW2Int, PLAYER.GetNW2String, PLAYER.GetNW2Bool = nwGet, nwGet, nwGet, nwGet
PLAYER.SetNW2Float, PLAYER.SetNW2Int, PLAYER.SetNW2String, PLAYER.SetNW2Bool = nwSet, nwSet, nwSet, nwSet

-- ───────────── Divers
concommand = { list = {} }
function concommand.Add(name, fn) concommand.list[name] = fn end

ADDON_ROOT = ADDON_ROOT or "."
function AddCSLuaFile() end
function include(path)
    local fn = assert(loadfile(ADDON_ROOT .. "/lua/" .. path))
    return fn()
end
file = {}
function file.Find(pattern) return PY_LIST_LUA(pattern), {} end

-- ───────────── Vecteurs, effets, traces (pour exécuter de vrais jutsus)
local V = {}
V.__index = V
function Vector(x, y, z) return setmetatable({ x = x or 0, y = y or 0, z = z or 0 }, V) end
V.__add = function(a, b) return Vector(a.x + b.x, a.y + b.y, a.z + b.z) end
V.__sub = function(a, b) return Vector(a.x - b.x, a.y - b.y, a.z - b.z) end
V.__unm = function(a) return Vector(-a.x, -a.y, -a.z) end
V.__mul = function(a, b)
    if type(a) == "number" then a, b = b, a end
    return Vector(a.x * b, a.y * b, a.z * b)
end
function V:Length() return math.sqrt(self.x ^ 2 + self.y ^ 2 + self.z ^ 2) end
function V:Normalize()
    local l = self:Length()
    if l > 0 then self.x, self.y, self.z = self.x / l, self.y / l, self.z / l end
end

EFFECTS = {}
function EffectData()
    local d = {}
    return setmetatable(d, { __index = function(_, k)
        return function(self, v) self[k:sub(4)] = v end
    end })
end
function util.Effect(name, data) table.insert(EFFECTS, { name = name, data = data }) end

TRACE_RESULT = nil
function util.TraceHull(t) return TRACE_RESULT or { Fraction = 1, HitPos = t.endpos, Entity = nil } end

function PLAYER:GetAimVector() return Vector(1, 0, 0) end
function PLAYER:GetPos() return self.pos or Vector(0, 0, 0) end
function PLAYER:SetPos(p) self.pos = p end
function PLAYER:EyePos() return self:GetPos() + Vector(0, 0, 64) end
function PLAYER:SetVelocity(v) self.velocity = v end
function PLAYER:EmitSound(s) self.lastSound = s end
function PLAYER:GetMaxHealth() return 100 end
function PLAYER:SetHealth(h) self.health = h end
function PLAYER:IsNPC() return false end
function PLAYER:IsNextBot() return false end

-- ───────────── Aides pour les tests
function NoticesFor(ply)
    local out = {}
    for _, m in ipairs(net.sent) do
        if m.name == "nb_notify" and m.to == ply then out[#out + 1] = m.values[1] end
    end
    return out
end
function Compiles(src, name)
    local fn, err = loadstring(src, name)
    return fn ~= nil, err
end
function RunHook(...) return (hook.Run(...)) end
