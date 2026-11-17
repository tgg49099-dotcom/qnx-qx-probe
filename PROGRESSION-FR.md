# PROGRESSION — QX-PROBE (version francaise)

Le correspondant francais de [`PROGRESSION.md`](PROGRESSION.md). Meme
structure, cycle par cycle.

Une ligne par partie : ce que c'est, son etat, et la commande qui le
prouve.
Etat = `done` (publie et prouve) / `partial` (fait mais incomplet) /
`planned` (pas fait) / `waiting` (impossible avant l'arrivee d'une piece
exterieure).

---

## 1. L'outil

| Partie | Ce que c'est | Etat | La commande qui le prouve |
|---|---|---|---|
| `qx_probe.py` | La sonde : lit une source C et signale les erreurs du protocole de gestionnaire de ressources QNX 8.0 | done | `python3 -I qx_probe.py examples/blackberry_eventfd_mgr.c` |
| Les onze regles (`RULES.md`) | Chaque regle avec la page officielle QNX 8.0 dont elle vient | done | `python3 -I scripts/verifier-citations.py` (36 citations, 14 pages relues) |
| Les cinq exemples (`examples/`) | De vrais gestionnaires de ressources, dont celui de BlackBerry | done | `python3 -I scripts/benchmark-corpus.py` (17 vrais fichiers, 7 publies par QNX ou BlackBerry) |
| La suite de tests (`tests/`) | 97 tests en 22 classes : le contrat a double sens, plus le chemin du jour de la licence | done | `bash scripts/run_tests.sh` |
| Le codelab (`docs/CODELAB.md`) | 30 minutes, Python 3 seul | done | `python3 -I scripts/verifier-codelab.py` |
| La preuve QNX 8.0 (`scripts/qnx8-proof.sh`) | Compile les exemples avec `qcc`, lit l'en-tete ELF, les execute sur une cible | waiting | sort 2 tant que le SDP est absent : c'est la contre-epreuve, pas un echec |
| L'installation du SDP (`scripts/install-sdp8.sh`) | Installe le SDP 8.0 avec les commandes officielles du QNX Software Center, puis appelle la preuve | done | `bash scripts/install-sdp8.sh --check` (le controle avant installation) ; sans les secrets dans l'environnement, il sort 3 en listant les pieces manquantes |
| La mesure du reseau (`scripts/mesurer-reseau-qnx.sh`) | Une ligne par hote QNX : la commande exacte et sa reponse | done | `bash scripts/mesurer-reseau-qnx.sh` |
| La video publiee (`media/qx-demo-v3.mp4`) | 89,72 s, 18 scenes, chaque chiffre remesure | done | `python3 -I scripts/audit-sous-titres-pixels.py` (les sous-titres SONT les pixels) |
| Le texte de soumission (`docs/SUBMISSION-EN.md`) | Champ par champ, tout ce qui se colle dans DevPost | done | `python3 -I scripts/verifier-soumission-devpost.py` |
| L'integration continue | Un workflow GitHub Actions qui rejoue les preuves | waiting | le jeton du proprietaire n'a pas le scope `workflow` |

## 2. Les chiffres publies, et d'ou ils viennent

| Chiffre | Ou il est publie | La commande qui le mesure |
|---|---|---|
| 97 tests, 22 classes | `README.md`, `docs/SUBMISSION-EN.md` | `bash scripts/run_tests.sh` |
| 94 fichiers dans l'arbre publie | `docs/SUBMISSION-EN.md` | `git ls-files \| wc -l` |
| 17 vrais gestionnaires de ressources analyses | `docs/BENCHMARK.md` | `python3 -I scripts/benchmark-corpus.py` |
| 36 citations de 14 pages officielles | `RULES.md` | `python3 -I scripts/verifier-citations.py` |
| 89,72 s de video | `docs/YOUTUBE-VIDEO.md` | `ffprobe` |

Chaque controle a sa contre-epreuve : un chiffre volontairement fausse dans
une copie des documents publies doit etre signale comme perime. La
contre-epreuve tourne a chaque execution normale, donc un controle ne peut
pas perdre ses dents en silence.

## 3. Progression de ce cycle — 17 novembre 2026, 15:21 (l'installation du SDP 8.0, mesuree)

- **La question du cycle** : rendre l'installation *reelle* du SDP QNX 8.0
  executable dans le conteneur qui construit ce depot, et prouver par la
  mesure exactement ce qui manque encore. La reponse est desormais dans du
  code et dans un fichier date, pas dans une phrase.
- **`scripts/install-sdp8.sh` est nouveau** (et publie). Il utilise les
  commandes officielles du QNX Software Center, chacune avec sa source
  dans l'en-tete : l'extraction du client, `-addLicenseKey`,
  `-mirrorBaseline qnx800`, `-installBaseline com.qnx.qnx800`, puis
  `source qnxsdp-env.sh`, `qcc -V` et `scripts/qnx8-proof.sh`, dont il
  propage le code de sortie. La cle de licence et le mot de passe myQNX
  sont lus dans l'environnement et nulle part ailleurs : jamais dans ce
  depot, jamais dans un journal du script, jamais dans un rapport.
- **Il echoue comme il doit.** Lance sans les trois variables
  d'environnement, il affiche les trois variables manquantes et le
  installateur manquant, et sort 3 sans rien toucher. Un script qui ne peut
  pas echouer ne prouve rien.
- **Le reseau est mesure, pas suppose**
  (`docs/MESURE-RESEAU-20261117.md`, rejouable avec
  `scripts/mesurer-reseau-qnx.sh`) : `www.qnx.com` repond (HTTP 301), et la
  note technique officielle dit que le serveur myQNX et le serveur de
  licences QNX sont tous deux heberges la ; `download.qnx.com` **expire au
  niveau TCP** depuis cette machine (20 s, 45 s, puis une socket brute au
  bout de 25 s) ; et quatre des sept noms de la demande de mesure —
  `my.qnx.com`, `account.qnx.com`, `qnx.qnx.com`, `update.qnx.com` —
  **n'existent pas dans le DNS public** (NXDOMAIN depuis un resolveur
  public) : ils ne peuvent pas repondre, ils n'ont pas d'adresse.
- **Le client lui-meme ne se telecharge pas sans compte** : le lien officiel
  repond 302 et arrive sur `www.qnx.com/account/login.html`. Le fichier
  exact est `qnx-setup-2.0.4-202501021438-linux.run` (99,85 Mo).
- **Ce qui manque encore, exactement** : (1) le fichier
  `qnx-setup-2.0.4-202501021438-linux.run`, (2) les trois variables
  d'environnement `MYQNX_USER`, `MYQNX_PASSWORD`, `QNX_LICENSE_KEY`,
  (3) un reseau qui atteint les serveurs de gestion de contenu qui portent
  les paquets — la note technique officielle dit que leur nom n'est connu
  qu'a l'execution, et le journal du QNX Software Center
  (`~/.qnx/swupdate/.metadata/.log`) nomme celui qui echoue.
- **Rien n'est simule.** `qcc -V` repond toujours 127 (le compilateur est
  absent) et `scripts/qnx8-proof.sh` sort toujours 2 (« SDP absent ») : les
  documents publies continuent de dire **NOT MEASURED**, et c'est la verite.

## 4. Les cycles precedents (resume)

| Cycle | Ce qu'il a fait |
|---|---|
| 197 | Le chemin du juge : une installation compatible PEP 668, un « 51-test » perime trouve et corrige |
| 198 | L'outil qui pose l'URL de la video, et la veille qui la detecte |
| 199-200 | La preuve QNX 8.0 ecrite, publiee et prouvee depuis l'exterieur ; une erreur factuelle sur QX PORTMAP corrigee |
| 201 (celui-ci) | L'installation du SDP 8.0 rendue executable et mesuree ; le reseau mesure hote par hote |
