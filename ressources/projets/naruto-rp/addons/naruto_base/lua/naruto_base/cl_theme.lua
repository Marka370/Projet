--[[
    Naruto Base — thème graphique : polices, couleurs et composants réutilisables.
    Tous les menus de l'addon passent par ces fonctions : change-les ici pour
    modifier le style partout.
]]

NB.UI = NB.UI or {}
local T = NB.Config.Theme

-- Taille relative à un écran 1080p
function NB.UI.Scale(px)
    return math.Round(px * ScrH() / 1080)
end
local S = NB.UI.Scale

local function createFonts()
    local fonts = {
        ["NB.Title"]  = { size = 34, weight = 800 },
        ["NB.Large"]  = { size = 26, weight = 700 },
        ["NB.Medium"] = { size = 20, weight = 600 },
        ["NB.Small"]  = { size = 16, weight = 500 },
        ["NB.Tiny"]   = { size = 13, weight = 500 },
    }
    for name, def in pairs(fonts) do
        surface.CreateFont(name, {
            font = "Roboto",
            size = math.max(11, S(def.size)),
            weight = def.weight,
            extended = true, -- accents et caractères spéciaux
            antialias = true,
        })
    end
end
createFonts()
hook.Add("OnScreenSizeChanged", "NB_Fonts", createFonts)

-- ───────────────────────────── Dessin

function NB.UI.DrawBar(x, y, w, h, fraction, color, text)
    draw.RoundedBox(4, x, y, w, h, Color(0, 0, 0, 170))
    fraction = math.Clamp(fraction, 0, 1)
    if fraction > 0 then
        draw.RoundedBox(4, x, y, math.max(h, w * fraction), h, color)
    end
    if text then
        draw.SimpleText(text, "NB.Tiny", x + w / 2, y + h / 2, T.text, TEXT_ALIGN_CENTER, TEXT_ALIGN_CENTER)
    end
end

local blurMaterial = Material("pp/blurscreen")
function NB.UI.DrawBlur(panel, amount)
    local x, y = panel:LocalToScreen(0, 0)
    surface.SetDrawColor(255, 255, 255)
    surface.SetMaterial(blurMaterial)
    for i = 1, 3 do
        blurMaterial:SetFloat("$blur", (i / 3) * (amount or 5))
        blurMaterial:Recompute()
        render.UpdateScreenEffectTexture()
        surface.DrawTexturedRect(-x, -y, ScrW(), ScrH())
    end
end

-- ───────────────────────────── Composants

-- Fenêtre au style du serveur. closable = false pour forcer un choix.
function NB.UI.Frame(title, w, h, closable)
    local frame = vgui.Create("DFrame")
    frame:SetSize(math.min(S(w), ScrW() - 20), math.min(S(h), ScrH() - 20))
    frame:Center()
    frame:SetTitle("")
    frame:ShowCloseButton(false)
    frame:SetDraggable(false)
    frame:DockPadding(S(12), S(52), S(12), S(12))
    frame:MakePopup()

    frame.Paint = function(self, pw, ph)
        NB.UI.DrawBlur(self)
        draw.RoundedBox(8, 0, 0, pw, ph, T.background)
        draw.RoundedBoxEx(8, 0, 0, pw, S(40), T.panel, true, true, false, false)
        surface.SetDrawColor(T.accent)
        surface.DrawRect(0, S(40), pw, 2)
        draw.SimpleText(title, "NB.Large", S(16), S(20), T.text, TEXT_ALIGN_LEFT, TEXT_ALIGN_CENTER)
    end

    if closable ~= false then
        local close = vgui.Create("DButton", frame)
        close:SetText("")
        close:SetSize(S(32), S(32))
        close:SetPos(frame:GetWide() - S(38), S(4))
        close.DoClick = function() frame:Close() end
        close.Paint = function(self, pw, ph)
            local col = self:IsHovered() and T.error or T.textDim
            draw.SimpleText("✕", "NB.Medium", pw / 2, ph / 2, col, TEXT_ALIGN_CENTER, TEXT_ALIGN_CENTER)
        end
    end
    return frame
end

function NB.UI.Button(parent, text, onClick, color)
    local button = vgui.Create("DButton", parent)
    button:SetText("")
    button:SetTall(S(38))
    button.Label = text
    button.DoClick = function(self)
        if not self:IsEnabled() then return end
        surface.PlaySound("ui/buttonclick.wav")
        if onClick then onClick(self) end
    end
    button.Paint = function(self, pw, ph)
        local base = color or T.accent
        local col = base
        if not self:IsEnabled() then
            col = Color(70, 70, 80)
        elseif self:IsHovered() then
            col = Color(math.min(base.r + 25, 255), math.min(base.g + 25, 255), math.min(base.b + 25, 255))
        end
        draw.RoundedBox(6, 0, 0, pw, ph, col)
        draw.SimpleText(self.Label, "NB.Small", pw / 2, ph / 2, T.text, TEXT_ALIGN_CENTER, TEXT_ALIGN_CENTER)
    end
    return button
end

-- Carte sélectionnable (titre + description + couleur)
function NB.UI.Card(parent, title, description, color, onSelect)
    local card = vgui.Create("DButton", parent)
    card:SetText("")
    card:SetTall(S(description and 70 or 44))
    card:Dock(TOP)
    card:DockMargin(0, 0, 0, S(6))
    card.Selected = false
    card.DoClick = function(self)
        surface.PlaySound("ui/buttonclick.wav")
        if onSelect then onSelect(self) end
    end
    card.Paint = function(self, pw, ph)
        local bg = self.Selected and Color(T.accent.r, T.accent.g, T.accent.b, 60) or T.panel
        if self:IsHovered() and not self.Selected then bg = Color(45, 45, 58, 240) end
        draw.RoundedBox(6, 0, 0, pw, ph, bg)
        draw.RoundedBoxEx(6, 0, 0, S(6), ph, color or T.accent, true, false, true, false)
        if self.Selected then
            surface.SetDrawColor(T.accent)
            surface.DrawOutlinedRect(0, 0, pw, ph, 2)
        end
        draw.SimpleText(title, "NB.Medium", S(16), S(description and 18 or 22), T.text, TEXT_ALIGN_LEFT, TEXT_ALIGN_CENTER)
    end

    if description then
        local label = vgui.Create("DLabel", card)
        label:SetFont("NB.Tiny")
        label:SetTextColor(T.textDim)
        label:SetText(description)
        label:SetWrap(true)
        label:SetMouseInputEnabled(false)
        label:SetPos(S(16), S(32))
        local basePerformLayout = card.PerformLayout
        card.PerformLayout = function(self, pw, ph)
            if basePerformLayout then basePerformLayout(self, pw, ph) end
            label:SetSize(pw - S(24), S(34))
        end
    end
    return card
end

function NB.UI.KeyName(key)
    local name = input.GetKeyName(key)
    return name and string.upper(name) or "?"
end
