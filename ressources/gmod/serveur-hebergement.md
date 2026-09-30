# 🖥️ Garry's Mod – Serveur & hébergement

[← Sommaire](../README.md) · Légende : 🟢 libre · 🟡 conditions · 🔵 outil/doc · 🔴 référence seulement

## Installer un serveur

| | Ressource | Contenu | Remarque |
|---|---|---|---|
| 🔵 | [Wiki – Linux Dedicated Server Hosting](https://wiki.facepunch.com/gmod/Linux_Dedicated_Server_Hosting) | Procédure officielle (SteamCMD, `srcds_run`) | |
| 🟢 | [LinuxGSM](https://linuxgsm.com) | Installer et gérer un serveur en quelques commandes | Idéal sur un VPS |
| 🟢 | [Pterodactyl](https://pterodactyl.io) · [egg Garry's Mod](https://eggs.pterodactyl.io/egg/games-garrys-mod/) | Panneau web pour gérer plusieurs serveurs (Docker) | Pratique à plusieurs admins |
| 🟢 | [gmod-server-docker](https://github.com/suchipi/gmod-server-docker) | Serveur GMod dans Docker | |
| 🟢 | [GMod-CSS-content](https://github.com/Be1zebub/GMod-CSS-content) | Egg Pterodactyl qui installe le contenu CSS | Beaucoup d'addons en ont besoin |

## Contenu & Workshop

- Le serveur télécharge les addons d'une **collection Workshop** (paramètre `+host_workshop_collection <ID>`).
- Les joueurs reçoivent automatiquement les addons de cette collection.
- Un **token de serveur** Steam est nécessaire pour être listé publiquement (`+sv_setsteamaccount`).

## Sécurité

- Scanner chaque addon avant de l'installer (voir [code-lua › Sécurité](code-lua.md#-sécurité-important-)).
- Ne jamais installer d'addons « leakés » (versions piratées d'addons payants) : c'est la première source de backdoors.
- Guide : [How to Secure Your GMod Server](https://zerosrp.co.uk/blog/how-to-secure-your-gmod-server).
