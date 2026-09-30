# ➕ Ajouter une ressource ou un projet

Tout le monde ayant accès au dépôt peut compléter la bibliothèque, même depuis un téléphone : ouvre le fichier sur GitHub, clique sur ✏️, modifie, puis **Commit changes**.

## Ajouter une ressource

1. Choisis le bon fichier :
   - **utile à plusieurs projets** → la section thématique (`gmod/`, `assets-libres/`, `outils/`…) ;
   - **spécifique à un projet** → `projets/<projet>/README.md`.
2. Ajoute une ligne dans le tableau, au même format que les autres :

   ```markdown
   | 🟢 | [Nom de la ressource](https://lien) | Ce que c'est, en une phrase | Licence / remarque |
   ```

3. Choisis la bonne pastille (voir la [légende](README.md#-légende-des-licences)). En cas de doute, mets 🔴 et précise-le.

## Créer la section d'un nouveau projet

1. Copie le dossier [`projets/_modele`](projets/_modele/README.md) sous un nouveau nom, par ex. `projets/one-piece-rp/`.
   Sur téléphone : **Add file › Create new file**, tape `ressources/projets/one-piece-rp/README.md`, puis colle le contenu du modèle.
2. Remplis le modèle.
3. Ajoute le projet dans le tableau « Par projet » de [README.md](README.md).

## ✅ Ce qu'on met dans le dépôt

- Des **liens** vers des ressources, avec leur licence.
- **Notre propre travail** : code, guides, fichiers créés par nous.
- Des fichiers **🟢 libres** (CC0, MIT…), en notant leur origine dans [LICENCES.md](LICENCES.md).

## ❌ Ce qu'on ne met jamais

- Des fichiers **extraits d'un jeu** (modèles, animations, sons, textures « rippés »).
- Des **addons Workshop recopiés** ou décompilés sans l'accord de leur auteur.
- Des fichiers **🔴** ou **🟡** dont la licence interdit la redistribution (Mixamo, par exemple).
- Des mots de passe, tokens ou clés.

Pourquoi : c'est illégal. GitHub supprime les dépôts sur plainte pour droits d'auteur (DMCA) et peut suspendre le compte.
