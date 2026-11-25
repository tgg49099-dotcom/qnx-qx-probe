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
| La suite de tests (`tests/`) | 100 tests en 22 classes : le contrat a double sens, plus le chemin du jour de la licence | done | `bash scripts/run_tests.sh` |
| Le codelab (`docs/CODELAB.md`) | 30 minutes, Python 3 seul | done | `python3 -I scripts/verifier-codelab.py` |
| La preuve QNX 8.0 (`scripts/qnx8-proof.sh`) | Compile les exemples avec `qcc`, lit l'en-tete ELF, les execute sur une cible | waiting | sort 2 tant que le SDP est absent : c'est la contre-epreuve, pas un echec |
| L'installation du SDP (`scripts/install-sdp8.sh`) | Installe le SDP 8.0 avec les commandes officielles du QNX Software Center, puis appelle la preuve | done | `bash scripts/install-sdp8.sh --check` (le controle avant installation) ; il demande le nom d'utilisateur et le mot de passe myQNX **au clavier** (jamais dans l'environnement, jamais dans un fichier), et sans terminal il sort 3 en listant ce qui manque |
| La mesure du reseau (`scripts/mesurer-reseau-qnx.sh`) | Une ligne par hote QNX : la commande exacte et sa reponse | done | `bash scripts/mesurer-reseau-qnx.sh` |
| La video publiee (`media/qx-demo-v3.mp4`) | 89,72 s, 18 scenes, chaque chiffre remesure | done | `python3 -I scripts/audit-sous-titres-pixels.py` (les sous-titres SONT les pixels) |
| Le texte de soumission (`docs/SUBMISSION-EN.md`) | Champ par champ, tout ce qui se colle dans DevPost | done | `python3 -I scripts/verifier-soumission-devpost.py` |
| L'integration continue | Un workflow GitHub Actions qui rejoue les preuves | waiting | le jeton du proprietaire n'a pas le scope `workflow` |

## 2. Les chiffres publies, et d'ou ils viennent

| Chiffre | Ou il est publie | La commande qui le mesure |
|---|---|---|
| 100 tests, 22 classes | `README.md`, `docs/SUBMISSION-EN.md` | `bash scripts/run_tests.sh` |
| 97 fichiers dans l'arbre publie | `docs/SUBMISSION-EN.md` | `git ls-files \| wc -l` |
| 17 vrais gestionnaires de ressources analyses | `docs/BENCHMARK.md` | `python3 -I scripts/benchmark-corpus.py` |
| 36 citations de 14 pages officielles | `RULES.md` | `python3 -I scripts/verifier-citations.py` |
| 89,72 s de video | `docs/YOUTUBE-VIDEO.md` | `ffprobe` |

Chaque controle a sa contre-epreuve : un chiffre volontairement fausse dans
une copie des documents publies doit etre signale comme perime. La
contre-epreuve tourne a chaque execution normale, donc un controle ne peut
pas perdre ses dents en silence.

## 3. Progression du 25 novembre 2026, 04:00 (la compilation et l'execution sur une cible QNX 8.0 vivante sont MESUREES)

- **La question du cycle** : la licence SDP 8.0 non commerciale gratuite etait
  arrivee le 24 novembre 2026, donc la preuve publiee devait etre remise en
  accord avec la realite -- la compilation etait mesuree, l'execution sur une
  cible ne l'etait pas. Ce cycle a mesure l'execution.
- **La compilation, mesuree le 24 novembre 2026** : `scripts/qnx8-proof.sh`
  compile les trois exemples C avec le vrai `qcc -Vgcc_ntox86_64 -Werror`, et
  `scripts/check_qnx_elf.py` lit l'en-tete ELF de chaque binaire : **3/3 sont
  des executables QNX 8.0 x86_64** (interpreteur
  `/usr/lib/ldqnx-64.so.2`). Le tableau de preuve dit maintenant MEASURED,
  avec la date de la mesure.
- **L'execution, mesuree le 25 novembre 2026** : l'image QEMU du SDP 8.0
  (construite par `mkqnximage`) a ete demarree, les trois binaires y ont ete
  copies par ssh, lances, et **chaque gestionnaire de ressources a attache son
  chemin** dans l'espace de noms de QNX (`/dev/qxprobe-demo`,
  `/var/run/qxprobe-status`, `/dev/qxprobe-official`).
  `scripts/qnx8-target-run.sh` le fait en une commande, et le tableau de
  preuve porte cela comme deux assertions.
- **Deux choses que le script d'execution ignorait, et qu'il a du apprendre** :
  (1) QNX 8.0 repond `x86pc` a `uname -m` pour la cible x86 64 bits, donc
  l'architecture est desormais lue avec l'outil officiel `pidin info`
  (`CPU:X86_64 Release:8.0.0`) ; (2) `scp` cherche `ssh` a un endroit fixe et
  pas dans le PATH, donc on lui donne maintenant le vrai chemin de `ssh` avec
  `-S`. Le script accepte aussi `QNX_TARGET_PORT` (le port de ssh sur la
  cible, 22 par defaut).
- **Rien n'est simule** : les deux chemins qui ne peuvent pas tourner le
  disent ("NOT MEASURED" pour l'execution quand aucune cible ne repond, code
  de sortie 2 pour la compilation quand il n'y a pas de SDK), et le controle
  rapporte une ligne qu'il n'a pas pu verifier comme **NOT CHECKED**, jamais
  comme OK et jamais comme un echec.

## 4. Progression du 18 novembre 2026, 21:40 (l'installation du SDP demande les identifiants myQNX au clavier)

- **La question du cycle** : l'installation du SDP 8.0 ne pouvait pas
  demarrer, parce que les identifiants myQNX ne doivent ni voyager dans
  l'environnement d'un conteneur, ni dans un fichier, ni dans une demande
  de cle. Le script les demande donc **au clavier**, une seule fois, et ne
  les ecrit nulle part.
- **Ce que le script fait maintenant** : `read -r` pour le nom d'utilisateur
  (en minuscules, comme le demande la documentation officielle) et
  `read -r -s` pour le mot de passe, qui n'est donc jamais affiche. Sans
  terminal, il s'arrete avec le code 3 en disant pourquoi, **sans envoyer
  une seule requete**. Le mot de passe ne quitte pas la memoire du shell :
  il n'est pas exporte dans l'environnement des processus enfants (la purge
  de la trace QNX le recoit par un tube, pas par une variable), et il est
  efface (`unset`) avant la sortie.
- **Ce qui reste en memoire, et pourquoi** : l'options file de `/dev/shm`
  (une memoire, jamais un disque) qui porte `-myqnx.password`. La
  documentation officielle impose de passer cette option en argument, et
  une ligne de commande afficherait le mot de passe a tous les processus de
  la machine (`ps`). Ce fichier, le jar de cookies et le fichier du mot de
  passe sont supprimes a la fin, la trace que le QNX Software Center
  ecrit dans son propre journal est purgee, et le script affiche le
  controle final : « le mot de passe apparait 0 fois dans $HOME et dans
  /work ».
- **Le resultat du run est ecrit dans un fichier hors de ce depot**
  (`RESULTAT-SDP8-<date>.txt`) : la date, le chemin du SDP, la version de
  `qcc`, la sortie de `scripts/qnx8-proof.sh` et le code de sortie. Jamais
  un secret.
- **Les trois tests du 18/11/2026** : sans terminal -> code 3 et 0 requete
  envoyee ; reponses vides -> code 3 et 0 requete envoyee ; reponses saisies
  -> le controle final affiche 0 occurrence du mot de passe dans `$HOME` et
  dans `/work`.

## 5. Progression du 17 novembre 2026, 15:21 (l'installation du SDP 8.0, mesuree)

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
  myQNX : le script demande le nom d'utilisateur et le mot de passe **au
  clavier**, il ne lit plus aucune variable d'environnement et n'ecrit le
  mot de passe dans aucun fichier,
  (3) un reseau qui atteint les serveurs de gestion de contenu qui portent
  les paquets — la note technique officielle dit que leur nom n'est connu
  qu'a l'execution, et le journal du QNX Software Center
  (`~/.qnx/swupdate/.metadata/.log`) nomme celui qui echoue.
- **Rien n'est simule.** `qcc -V` repond toujours 127 (le compilateur est
  absent) et `scripts/qnx8-proof.sh` sort toujours 2 (« SDP absent ») : les
  documents publies continuent de dire **NOT MEASURED**, et c'est la verite.

## 6. Les cycles precedents (resume)

| Cycle | Ce qu'il a fait |
|---|---|
| 197 | Le chemin du juge : une installation compatible PEP 668, un « 51-test » perime trouve et corrige |
| 198 | L'outil qui pose l'URL de la video, et la veille qui la detecte |
| 199-200 | La preuve QNX 8.0 ecrite, publiee et prouvee depuis l'exterieur ; une erreur factuelle sur QX PORTMAP corrigee |
| 201 (le 17/11) | L'installation du SDP 8.0 rendue executable et mesuree ; le reseau mesure hote par hote |
| 202 (celui-ci) | L'installation du SDP demande les identifiants myQNX au clavier : aucune variable d'environnement, aucun fichier qui porte le mot de passe, resultat du run ecrit hors du depot |
