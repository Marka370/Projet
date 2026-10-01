--[[
    Naruto Base — projectile « boule de feu » (Katon : Gōkakyū no Jutsu).
    Sert d'exemple pour créer d'autres projectiles (Suiton, Fūton…).
]]

AddCSLuaFile()

ENT.Type = "anim"
ENT.Base = "base_anim"
ENT.PrintName = "Boule de feu"
ENT.Spawnable = false

ENT.Radius = 160   -- rayon de l'explosion
ENT.Damage = 45
ENT.Lifetime = 4

if SERVER then
    function ENT:Initialize()
        self:SetModel("models/hunter/misc/sphere025x025.mdl")
        self:PhysicsInitSphere(10, "default")
        self:SetCollisionGroup(COLLISION_GROUP_PROJECTILE)
        self:DrawShadow(false)
        self.DieTime = CurTime() + self.Lifetime

        local phys = self:GetPhysicsObject()
        if IsValid(phys) then
            phys:EnableGravity(false)
            phys:Wake()
        end
    end

    function ENT:Launch(direction, speed)
        local phys = self:GetPhysicsObject()
        if IsValid(phys) then phys:SetVelocity(direction * speed) end
    end

    function ENT:Explode()
        if self.Exploded then return end
        self.Exploded = true

        local pos = self:GetPos()
        local owner = IsValid(self:GetOwner()) and self:GetOwner() or self

        util.BlastDamage(self, owner, pos, self.Radius, self.Damage)
        for _, ent in ipairs(ents.FindInSphere(pos, self.Radius * 0.75)) do
            if ent ~= owner and (ent:IsPlayer() or ent:IsNPC()) then
                ent:Ignite(3)
            end
        end
        NB.Util.Effect("Explosion", pos, 1)

        -- Ne jamais supprimer une entité pendant une collision physique
        SafeRemoveEntityDelayed(self, 0)
    end

    function ENT:PhysicsCollide()
        self:Explode()
    end

    function ENT:Think()
        if CurTime() > self.DieTime then self:Explode() end
        self:NextThink(CurTime() + 0.1)
        return true
    end
else
    local glow = Material("sprites/light_glow02_add")

    function ENT:Draw()
        local pos = self:GetPos()
        render.SetMaterial(glow)
        render.DrawSprite(pos, 110, 110, Color(255, 110, 30))
        render.DrawSprite(pos, 55, 55, Color(255, 220, 140))
    end

    function ENT:Think()
        local light = DynamicLight(self:EntIndex())
        if light then
            light.pos = self:GetPos()
            light.r, light.g, light.b = 255, 120, 40
            light.brightness = 3
            light.decay = 1000
            light.size = 256
            light.dietime = CurTime() + 0.1
        end
    end
end
