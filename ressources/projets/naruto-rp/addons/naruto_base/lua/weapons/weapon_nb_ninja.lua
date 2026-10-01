--[[
    Naruto Base — « Mains de ninja » : arme pour lancer les jutsus à la souris.
      Clic gauche : lance le jutsu sélectionné
      Clic droit  : emplacement suivant
      Recharger   : ouvre le livre des jutsus
    (Les touches de la barre fonctionnent aussi sans cette arme.)
]]

AddCSLuaFile()

SWEP.PrintName = "Mains de ninja"
SWEP.Author = "Naruto Base"
SWEP.Category = "Naruto Base"
SWEP.Instructions = "Clic gauche : jutsu · Clic droit : changer · R : livre des jutsus"
SWEP.Spawnable = true

SWEP.ViewModel = "models/weapons/c_arms.mdl"
SWEP.WorldModel = ""
SWEP.UseHands = true
SWEP.ViewModelFOV = 54
SWEP.Slot = 0
SWEP.SlotPos = 5
SWEP.DrawAmmo = false
SWEP.DrawCrosshair = true

SWEP.Primary.ClipSize = -1
SWEP.Primary.DefaultClip = -1
SWEP.Primary.Automatic = false
SWEP.Primary.Ammo = "none"
SWEP.Secondary.ClipSize = -1
SWEP.Secondary.DefaultClip = -1
SWEP.Secondary.Automatic = false
SWEP.Secondary.Ammo = "none"

function SWEP:SetupDataTables()
    self:NetworkVar("Int", 0, "JutsuSlot")
end

function SWEP:Initialize()
    self:SetHoldType("fist")
    self:SetJutsuSlot(1)
end

function SWEP:PrimaryAttack()
    self:SetNextPrimaryFire(CurTime() + 0.3)
    if CLIENT then return end
    local owner = self:GetOwner()
    local id = NB.GetSlotJutsu(owner, self:GetJutsuSlot())
    if id then
        NB.TryCast(owner, id)
    else
        NB.Notify(owner, NB.L("empty_slot", "J"), "error")
    end
end

function SWEP:SecondaryAttack()
    self:SetNextSecondaryFire(CurTime() + 0.2)
    local count = #NB.Config.HotbarKeys
    local slot = self:GetJutsuSlot() % count + 1
    self:SetJutsuSlot(slot)

    if CLIENT and IsFirstTimePredicted() then
        local id = NB.Local.slots[slot]
        local jutsu = id and NB.GetJutsu(id)
        NB.Notify(NB.L("slot_selected", slot, jutsu and jutsu.name or "—"), "info")
    end
end

function SWEP:Reload()
    if CLIENT and IsFirstTimePredicted() and (self.NextMenu or 0) < CurTime() then
        self.NextMenu = CurTime() + 0.5
        NB.OpenJutsuMenu()
    end
end
