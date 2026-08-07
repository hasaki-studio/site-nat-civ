# Site — Réussir mon entretien de naturalisation

Site public de l'application Android « Réussir mon entretien » (Hasaki Studio).
Il porte la **politique de confidentialité** et les **mentions légales** exigées par la
Play Console, par AdMob et par le droit français.

Site statique, sans dépendance et sans requête vers un service tiers.

Destination : `https://naturalisation.hasakistudio.fr`

## URL à déclarer

| Où | URL |
|---|---|
| Play Console → Contenu de l'application → Politique de confidentialité | `https://naturalisation.hasakistudio.fr/confidentialite` |
| AdMob → Confidentialité et messages (RGPD) | `https://naturalisation.hasakistudio.fr/confidentialite` |
| `src/screens/MentionsLegales.tsx` de l'app | `https://naturalisation.hasakistudio.fr/mentions-legales` |

Ces adresses sont revérifiées périodiquement par Google. **Ne les changez plus** une fois
saisies : une URL modifiée ou tombée en 404 peut suspendre la fiche Play Store.

## Organisation

```
content/                Sources éditoriales en Markdown — c'est ici qu'on écrit
build/build.py          Générateur (Python 3, aucune dépendance)
build/index.body.html   Corps de la page d'accueil, conservé tel quel
wrangler.jsonc          Configuration de déploiement Cloudflare

public/                 SEUL dossier publié sur le web
  *.html                Pages générées — ne pas éditer directement
  assets/site.css       Feuille de style commune (éditée à la main)
  assets/site.js        Bascule des blocs repliables
  sitemap.xml           Généré
  robots.txt            Généré
  _headers              En-têtes HTTP appliqués par Cloudflare
  favicon.ico
```

Cette séparation est délibérée : `content/` et `build/` restent dans le dépôt mais ne sont
jamais servis, sinon les sources Markdown seraient accessibles en ligne et feraient doublon
avec les pages.

Le contenu se modifie dans `content/*.md`, jamais dans les `.html` de `public/`, qui sont
écrasés à chaque génération. `public/assets/site.css` est en revanche un fichier source :
extrait une fois de l'export initial puis complété à la main, le générateur n'y touche pas.

## Générer

```bash
python3 build/build.py
```

Régénère les 5 pages, `sitemap.xml` et `robots.txt`. Le domaine et l'adresse de contact
sont définis en tête de `build/build.py` — un seul endroit à modifier.

## Prévisualiser

Cloudflare sert `confidentialite.html` sur `/confidentialite`. Pour reproduire ce routage
en local :

```bash
cd public && python3 - <<'EOF'
import http.server, os, socketserver
class H(http.server.SimpleHTTPRequestHandler):
    def translate_path(self, path):
        p = super().translate_path(path)
        if not os.path.exists(p) and not p.endswith(('/', '.html')) and os.path.exists(p + '.html'):
            return p + '.html'
        return p
socketserver.TCPServer.allow_reuse_address = True
socketserver.TCPServer(("127.0.0.1", 8899), H).serve_forever()
EOF
```

## Déployer

Le site est un **Worker à ressources statiques** : aucun code n'est exécuté, Cloudflare
sert directement les fichiers de `public/`. Tout est décrit dans `wrangler.jsonc`.

### Depuis la machine

```bash
npx wrangler deploy
```

### Depuis le tableau de bord Cloudflare

*Workers & Pages → Create application → Import a repository* → dépôt `site-nat-civ`.

| Champ | Valeur |
|---|---|
| Project name | `site-nat-civ` |
| Build command | *(vide)* |
| Deploy command | `npx wrangler deploy` |
| Path | `/` |

**Ne choisissez aucun modèle** dans la galerie : les templates créent un nouveau dépôt et
un Worker sans rapport avec ce site.

Le domaine se rattache ensuite depuis l'onglet **Domains** du projet →
`naturalisation.hasakistudio.fr`. La zone `hasakistudio.fr` étant chez Cloudflare,
l'enregistrement DNS et le certificat sont créés automatiquement.

Un hôte ne peut servir qu'un seul Worker : si le domaine est déjà rattaché ailleurs, il
faut l'en détacher avant.

### Le domaine

`hasakistudio.fr` est enregistré chez OVH — Cloudflare Registrar ne vend pas de `.fr` — et
ses serveurs de noms pointent vers Cloudflare. Conserver le verrou de transfert activé chez
OVH : il n'a aucun rapport avec la délégation DNS et protège contre le détournement.

Prévoir un sous-domaine par produit :

```
hasakistudio.fr                 vitrine du studio
naturalisation.hasakistudio.fr  ce site
test-civique.hasakistudio.fr    seconde application
```

## Avant la mise en ligne

Emplacements encore à renseigner — ils apparaissent en surbrillance ocre sur les pages :

- [ ] **SIREN** (mentions légales et politique, §1) — après immatriculation
- [ ] **Adresse du siège** (mentions légales et politique, §1)
- [ ] **Directeur de la publication** — nom et prénom de la personne physique ; la LCEN ne
      se contente pas du nom commercial
- [ ] **Durée de conservation Firebase Analytics** (politique, §3.2) — relever le réglage
      dans la console Firebase (2 ou 14 mois)
- [ ] **Médiateur de la consommation** (mentions légales) — si l'activité y est soumise
- [ ] **Liens officiels** de `content/conseils-de-revision.md` — les cliquer un par un ;
      ils n'ont pas pu être vérifiés automatiquement
- [x] **`contact@hasakistudio.fr`** — réception vérifiée. L'offre OVH du domaine est
      « MX Plan redirect » : zéro boîte aux lettres, mais 1000 redirections. L'adresse
      est donc un alias qui achemine vers la boîte Gmail de l'éditeur.
      *Limite connue* : une redirection ne permet pas d'**émettre** depuis l'adresse ;
      les réponses partent de l'adresse personnelle. Pour y remédier, commander une
      vraie boîte MX Plan puis configurer l'envoi via le SMTP d'OVH (`ssl0.ovh.net`) —
      le SPF du domaine (`include:mx.ovh.com`) le couvre déjà sans modification.
      Tester depuis une adresse tierce : un envoi depuis la boîte de destination est
      dédupliqué par Gmail et donne un faux négatif.
- [ ] **DKIM et DMARC** — absents de la zone. Sans importance tant que le domaine
      n'émet pas de courrier ; à ajouter le jour où une vraie boîte est en place, sous
      peine de voir les réponses classées en indésirables (or le RGPD impose une
      réponse sous un mois).
- [ ] Rafraîchir les dates de « dernière mise à jour » si la mise en ligne est postérieure

## Ajouter la seconde application

Les pages légales de `test-civique` seront proches à quelques lignes près, mais doivent
rester **des fichiers distincts** : une politique commune devrait être scindée le jour où
une application est cédée ou retirée, ce qui changerait l'URL déclarée à Google.

Dupliquer ce dépôt, puis dans `build/build.py` : ajuster `SITE_URL`, les entrées de
`PAGES` et le bloc `APPLICATION`. Le contenu se reprend depuis `content/`.
