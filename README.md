# 🗂️ Projet

| Dossier | Contenu |
|---|---|
| 📚 [`ressources/`](ressources/README.md) | **Bibliothèque de ressources** classée par thème (code, animations, mapping, assets libres, outils…) et par projet (Naruto RP…) |
| 🎬 [`video/`](video/README.md) | **Vidéos musicales animées** façon TikTok : paroles, visualiseur et effets synchronisés sur la musique |
| 🤖 `bot/`, `config/` | Bot Discord et mise en place automatique du serveur (détails ci-dessous) |

---

# 🎮 Bot & serveur Discord communautaire

Ce projet met en place **tout le serveur Discord automatiquement** (rôles, salons, permissions, règlement…) et fournit un **bot** pour la modération et le côté pratique du serveur.

Tout peut se faire **depuis un téléphone**, avec l'app Discord et un navigateur.

---

## 📦 Ce que ça crée

**Rôles** : 👑 Fondateur · 🛡️ Administrateur · ⚔️ Modérateur · 🤝 Support · 🛠️ Développeur · 🎥 Créateur de contenu · 🧪 Testeur · ✅ Membre, plus des rôles que chacun choisit lui-même : notifications (annonces, devlog, événements, recherche de joueurs) et plateformes (PC, console, mobile).

**Salons**

| Catégorie | Salons |
|---|---|
| 📌 ACCUEIL | bienvenue · règlement · vérification · annonces · rôles |
| 💬 COMMUNAUTÉ | discussion · médias · memes · suggestions · événements · commandes-bot |
| 🎮 JEUX | discussions-jeux · recherche-de-joueurs · clips-et-exploits |
| 🛠️ NOS JEUX | devlog · idées-de-jeux · bugs-et-retours · beta-test (testeurs) · dev-privé (développeurs) |
| 🔊 VOCAUX | Général · Partie 1 · Partie 2 · Duo · Squad (4) · Chill & musique · AFK |
| 🆘 SUPPORT | ouvrir-un-ticket |
| 🛡️ STAFF | staff · sanctions · logs · Réunion staff (invisible pour les membres) |

**Système de vérification** : un nouvel arrivant ne voit que l'accueil. Quand il clique sur « J'accepte le règlement », il reçoit le rôle ✅ Membre et débloque le reste du serveur. Ça bloque une bonne partie des bots de spam et des raids.

## 🤖 Ce que fait le bot

- **Accueil** : message de bienvenue, alerte dans les logs si le compte est très récent (anti-raid).
- **Boutons** : vérification, rôles au choix, ouverture et fermeture de tickets.
- **Tickets** : salon privé entre le membre et le staff. À la fermeture, une copie de la conversation est envoyée dans les logs.
- **Automod** : supprime les invitations vers d'autres serveurs, le spam, les mentions en masse et les mots interdits. Rend muet automatiquement en cas de spam.
- **Logs** : messages supprimés ou modifiés, arrivées et départs, sanctions.
- **Commandes staff** : `/warn` `/warns` `/unwarn` `/clearwarns` `/mute` `/unmute` `/kick` `/ban` `/unban` `/clear` `/slowmode` `/lock` `/unlock` `/annonce` `/setup`
- **Sanctions automatiques** : 3 avertissements = mute 1 h, 5 = mute 24 h, 7 = mute 7 jours (modifiable).
- **Commandes pour tous** : `/aide` `/sondage` `/serveur` `/profil`

---

## 📱 Mise en place depuis un téléphone

### Étape 1 — Créer le bot (5 min, navigateur)

1. Ouvre **https://discord.com/developers/applications** dans ton navigateur et connecte-toi.
2. **New Application**, donne-lui un nom (par ex. le nom de ton serveur) et valide.
3. Dans **General Information**, copie l'**Application ID** et garde-le de côté.
4. Menu **Bot** :
   - clique sur **Reset Token** et copie le token. ⚠️ C'est le mot de passe du bot : ne l'envoie à personne et ne le colle jamais dans un fichier du dépôt ni dans une conversation ;
   - active **Server Members Intent** et **Message Content Intent**, puis **Save Changes**.
5. Invite le bot sur ton serveur en ouvrant ce lien (remplace `TON_APPLICATION_ID`) :

   ```
   https://discord.com/oauth2/authorize?client_id=TON_APPLICATION_ID&permissions=8&scope=bot+applications.commands
   ```

   Choisis ton serveur, puis **Autoriser**. (`permissions=8` = Administrateur : le bot en a besoin pour créer les salons et les permissions.)

### Étape 2 — Récupérer l'ID du serveur (optionnel, recommandé)

Dans l'app Discord : **Paramètres (ton avatar) › Avancés › Mode développeur** (active-le). Ensuite, **appui long sur l'icône du serveur › Copier l'identifiant du serveur**.

### Étape 3 — Donner le token à GitHub (navigateur)

Sur la page GitHub de ce dépôt, en version ordinateur si le menu n'apparaît pas :
**Settings › Secrets and variables › Actions › New repository secret**

- `DISCORD_TOKEN` = le token du bot
- `GUILD_ID` = l'ID du serveur (étape 2)

Les secrets sont chiffrés : personne ne peut les relire, pas même toi.

### Étape 4 — Construire le serveur en un clic

Onglet **Actions › Mise en place du serveur Discord › Run workflow**.

Au bout d'une à deux minutes, le serveur est prêt ✨. Tu peux relancer le workflow quand tu veux : il ne crée que ce qui manque et remet à jour le reste, sans rien dupliquer.

> Les salons créés par défaut par Discord (« général », « Général »…) sont supprimés. Pour les garder, vide la liste `remove_default_channels` dans `config/server.yaml`.

### Étape 5 — Réglages finaux dans l'app Discord

1. **Place-toi en Fondateur** : Paramètres du serveur › Membres › toi › ajoute le rôle 👑 Fondateur. Vérifie-toi aussi dans #vérification.
2. **Active la Communauté** (conseillé pour un grand serveur) : Paramètres du serveur › **Activer la Communauté**. Choisis `📜・règlement` comme salon des règles et `💬・staff` pour les mises à jour Discord. Relance ensuite le workflow de l'étape 4 : `📢・annonces` et `📰・devlog` deviennent de vrais salons d'annonces que d'autres serveurs peuvent suivre.
3. Dans **Rôles**, le rôle du bot doit rester **au-dessus** des rôles qu'il gère. Il y est déjà si tu ne l'as pas déplacé.

### Étape 6 — Faire tourner le bot 24 h/24

Les boutons (vérification, rôles, tickets), l'automod, les logs et les commandes ne marchent **que si le bot est allumé**. Il faut donc un hébergement qui tourne en permanence. Un téléphone ou GitHub Actions ne conviennent pas pour ça.

Le projet contient un `Dockerfile`, donc la plupart des hébergeurs peuvent le déployer directement depuis ce dépôt GitHub, tout depuis le navigateur :

1. Crée un compte chez un hébergeur qui déploie depuis GitHub : un service type Railway, Fly.io ou Render (formule « worker », pas « web »), un hébergeur spécialisé en bots Discord, ou un petit VPS. Compte en général quelques euros par mois. Les offres gratuites changent souvent : vérifie les conditions actuelles.
2. Crée un nouveau projet à partir de ce dépôt GitHub (il détectera le `Dockerfile`).
3. Ajoute les variables d'environnement `DISCORD_TOKEN` et `GUILD_ID`.
4. Ajoute si possible un **volume persistant** monté sur `/app/data`, sinon les avertissements sont perdus à chaque redéploiement.
5. Lance le déploiement. Dans Discord, tape `/aide` : si le bot répond, tout marche 🎉

Une fois le bot hébergé, un admin peut aussi taper **`/setup`** dans Discord pour réappliquer la structure, sans passer par GitHub.

---

## ✏️ Personnaliser

Tout se règle dans **`config/server.yaml`**, que tu peux modifier directement depuis GitHub (icône ✏️ sur le fichier) :

- ajouter, renommer ou supprimer des salons et des rôles ;
- changer le règlement, les messages de bienvenue et les couleurs ;
- régler l'automod (mots interdits, seuil de spam…) et les sanctions automatiques.

Après une modification, relance le workflow (étape 4) ou tape `/setup` dans Discord. Les tests GitHub (onglet Actions › Tests) vérifient automatiquement que le fichier est valide.

> ⚠️ Si tu renommes un salon ou un rôle dans le fichier, le bot en crée un nouveau (il repère les éléments par leur nom). Supprime ensuite l'ancien à la main dans Discord.

## 💻 Pour les développeurs (ordinateur)

```bash
pip install -r requirements-dev.txt
cp .env.example .env      # puis remplis DISCORD_TOKEN et GUILD_ID
python -m bot check       # vérifie config/server.yaml
python -m bot setup       # construit le serveur puis s'arrête
python -m bot             # lance le bot
python -m pytest          # tests
```

Organisation du code :

```
config/server.yaml      structure du serveur + réglages du bot
bot/setup_server.py     création / mise à jour des rôles, salons, permissions, messages
bot/views.py            boutons persistants (vérification, rôles, tickets)
bot/cogs/               welcome, moderation, automod, logs, utility
bot/db.py               avertissements (SQLite)
```

## 🚀 Idées pour la suite

- Système de niveaux et d'XP pour récompenser les membres actifs
- Salons vocaux temporaires (« Rejoins pour créer »)
- Annonces automatiques de tes streams et vidéos
- Espace dédié par jeu quand tes jeux sortiront (catégorie + rôle + salons de support)
- Règles AutoMod natives de Discord en complément
