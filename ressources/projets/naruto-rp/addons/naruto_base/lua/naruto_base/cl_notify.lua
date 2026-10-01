--[[
    Naruto Base — notifications à l'écran (en haut, au centre).
    Côté client : NB.Notify(texte, "info" | "success" | "error")
]]

local T = NB.Config.Theme
local S = NB.UI.Scale

local notices = {}
local LIFETIME = 4
local FADE = 0.4

local KIND_COLORS = {
    info = T.accent,
    success = T.success,
    error = T.error,
}

function NB.Notify(text, kind)
    table.insert(notices, 1, { text = text, kind = kind or "info", born = RealTime() })
    while #notices > 5 do table.remove(notices) end
    if kind == "error" then
        surface.PlaySound("buttons/button10.wav")
    else
        surface.PlaySound("buttons/button15.wav")
    end
end

net.Receive("nb_notify", function()
    local text = net.ReadString()
    local kind = net.ReadString()
    NB.Notify(text, kind)
end)

hook.Add("HUDPaint", "NB_Notifications", function()
    local now = RealTime()
    local y = S(80)
    surface.SetFont("NB.Small")

    for i = #notices, 1, -1 do
        if now - notices[i].born > LIFETIME then table.remove(notices, i) end
    end

    for _, notice in ipairs(notices) do
        local age = now - notice.born
        local alpha = 1
        if age < FADE then alpha = age / FADE end
        if age > LIFETIME - FADE then alpha = (LIFETIME - age) / FADE end

        local tw, th = surface.GetTextSize(notice.text)
        local w, h = tw + S(40), th + S(16)
        local x = (ScrW() - w) / 2
        local color = KIND_COLORS[notice.kind] or T.accent

        draw.RoundedBox(6, x, y, w, h, Color(T.background.r, T.background.g, T.background.b, 230 * alpha))
        draw.RoundedBoxEx(6, x, y, S(5), h, Color(color.r, color.g, color.b, 255 * alpha), true, false, true, false)
        draw.SimpleText(notice.text, "NB.Small", x + w / 2 + S(2), y + h / 2,
            Color(T.text.r, T.text.g, T.text.b, 255 * alpha), TEXT_ALIGN_CENTER, TEXT_ALIGN_CENTER)
        y = y + h + S(6)
    end
end)
