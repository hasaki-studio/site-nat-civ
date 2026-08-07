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
content/            Sources éditoriales en Markdown — c'est ici qu'on écrit
build/build.py      Générateur (Python 3, aucune dépendance)
build/index.body.html   Corps de la page d'accueil, conservé tel quel
assets/site.css     Feuille de style commune aux 5 pages (éditée à la main)
assets/site.js      Bascule des blocs repliables
*.html              Pages générées — ne pas éditer directement
sitemap.xml         Généré
robots.txt          Généré
_headers            En-têtes HTTP servis par Cloudflare Pages
```

Le contenu se modifie dans `content/*.md`, jamais dans les `.html`, qui sont écrasés à
chaque génération. `assets/site.css` est en revanche un fichier source : il a été extrait
une fois de l'export initial puis complété à la main, et le générateur n'y touche pas.

## Générer

```bash
python3 build/build.py
```

Régénère les 5 pages, `sitemap.xml` et `robots.txt`. Le domaine et l'adresse de contact
sont définis en tête de `build/build.py` — un seul endroit à modifier.

## Prévisualiser

Cloudflare Pages sert `confidentialite.html` sur `/confidentialite`. Pour reproduire ce
routage en local :

```bash
python3 - <<'EOF'
import http.server, os, socketserver
os.chdir(os.path.dirname(os.path.abspath('.')) and '.')
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

## Déployer sur Cloudflare Pages

1. **Cloudflare → Workers & Pages → Create → Pages → Connect to Git**, choisir ce dépôt.
2. Configuration de build :
   - Framework preset : **None**
   - Build command : *(vide — les pages sont générées et versionnées)*
   - Build output directory : `/`
3. **Custom domains → Set up a custom domain** → `naturalisation.hasakistudio.fr`.
   Cloudflare crée l'enregistrement DNS et le certificat automatiquement si la zone
   `hasakistudio.fr` est déjà chez lui.

### Le domaine

`hasakistudio.fr` s'achète chez un registrar accrédité AFNIC — Cloudflare Registrar ne
vend pas de `.fr`. Une fois acheté, ajouter la zone dans Cloudflare et faire pointer les
serveurs de noms du registrar vers ceux indiqués par Cloudflare.

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
- [ ] **Boîte `contact@hasakistudio.fr`** — la créer dans l'espace client OVH (offre MX
      Plan incluse avec le domaine), puis s'envoyer un message de test. C'est le seul
      canal de contact prévu par les trois documents : la LCEN, l'exercice des droits
      RGPD et la Play Console s'appuient tous dessus.
- [ ] Rafraîchir les dates de « dernière mise à jour » si la mise en ligne est postérieure

## Ajouter la seconde application

Les pages légales de `test-civique` seront proches à quelques lignes près, mais doivent
rester **des fichiers distincts** : une politique commune devrait être scindée le jour où
une application est cédée ou retirée, ce qui changerait l'URL déclarée à Google.

Dupliquer ce dépôt, puis dans `build/build.py` : ajuster `SITE_URL`, les entrées de
`PAGES` et le bloc `APPLICATION`. Le contenu se reprend depuis `content/`.
