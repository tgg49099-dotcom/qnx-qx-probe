# QX-PROBE — analyseur statique du protocole resource-manager QNX 8.0

QX-PROBE lit du code C et signale les **bugs de gestionnaire de ressources que
l'on ne peut pas se permettre** dans un driver QNX 8.0 : un gestionnaire de
lecture qui n'appelle jamais `iofunc_read_verify()`, une boucle de messages qui
bloque sans distribuer, un reply qui renvoie plus de parties que l'IOV n'en
contient.

C'est un outil **hôte** : il tourne sur Linux, macOS ou Windows, il n'a
**aucune dépendance** et il ne demande **ni SDK QNX ni carte QNX**. C'est ce qui
le rend utilisable dans une chaine d'integration continue, ou dans un jury qui
n'a pas de materiel.

```console
$ python3 -I qx_probe.py tests/fixtures/qnx80_resmgr_qx004_no_gate.c
ERROR QX004  tests/fixtures/qnx80_resmgr_qx004_no_gate.c:52: qx_read() never calls iofunc_read_verify(): the access gate is missing
...
RESULT: 6 finding(s), 1 ERROR, 0 WARN
```

Chaque constat pointe sur une ligne (`fichier:ligne:`, le format de gcc) : un
clic dans VS Code, dans l'IDE QNX Momentics (Eclipse) ou dans un journal de CI
ouvre la ligne du source. Sur l'exemple officiel de QNX, la meme commande ne
signale rien d'actionnable (`0 ERROR, 0 WARN`, code de sortie 0).

Rien n'a a etre installe pour utiliser la sonde. Si vous preferez une
commande a part entiere, `pip install .` lit `pyproject.toml` et vous donne le
point d'entree `qx-probe` — le meme outil, les memes codes de sortie :

```console
$ pip install .
$ qx-probe tests/fixtures/qnx80_resmgr_qx004_no_gate.c
ERROR QX004  tests/fixtures/qnx80_resmgr_qx004_no_gate.c:52: qx_read() never calls iofunc_read_verify(): the access gate is missing
...
RESULT: 6 finding(s), 1 ERROR, 0 WARN
```

Les trois choses que le reglement du concours demande a une soumission de
dire :

| | |
|---|---|
| **Version QNX** | **QNX SDP 8.0** — chaque regle est adossee a une page de la BlackBerry QNX SDP 8.0 C Library Reference (14 pages, 36 citations, relues le 14 novembre 2026) |
| **Cible** | l'outil lui-meme est un outil **hote** (Linux, macOS, Windows) ; les exemples C ciblent **QNX 8.0 sur QEMU x86_64** (`qcc -Vgcc_ntox86_64`) |
| **Chaine d'outils** | **Python 3, bibliotheque standard uniquement**, pour l'outil ; **`qcc` du SDP 8.0**, pour les exemples C — dont la compilation n'est **PAS MESUREE**, car aucune licence SDP 8.0 n'existe dans l'environnement ou ce projet a ete ecrit |

## Regle d'or : zero faux positif

QNX 8.0 est un OS temps reel. Le code de reference des resource managers est
public et ecrit par l'editeur lui-meme. **Une regle qui signale a tort
du code canonique est pire qu'une regle absente** : elle ferait perdre le
concours au premier regard du jury.

Concretement, la sonde ne signale **jamais** :

* un point de montage hors de `/dev/` — `resmgr_attach()` "puts the path into
  the general pathname space" ;
* un gestionnaire en lecture seule (sans `io_funcs.write`) — chaque slot de
  `resmgr_io_funcs_t` a un defaut POSIX documente ;
* l'idiome `resmgr_block()` / `resmgr_handler()` — c'est l'exemple canonique de
  la documentation QNX 8.0 ;
* un `iofunc_func_init()` appele avec les macros `_RESMGR_IO_NFUNCS` /
  `_RESMGR_CONNECT_NFUNCS` — le cas normal.

Chaque regle est adossee a une page de la documentation **officielle** BlackBerry
QNX SDP 8.0 (les 14 pages citees ont ete relues les 12 et 14 novembre 2026 ; chacune
porte la date de mise a jour que QNX lui a donnee, et
`scripts/verifier-citations.py` affiche cette date). Le detail regle par
regle, avec la citation et l'URL, est dans **[RULES.md](RULES.md)**.

## Les onze regles

| Code | Ce que la sonde signale | Niveau | Source officielle QNX 8.0 |
|---|---|---|---|
| QX001 | le fichier utilise l'API resmgr mais ne cable aucune table de dispatch | ERROR | `resmgr_attach()` |
| QX002 | plus de slots cables que `iofunc_func_init()` n'en remplit | ERROR | `iofunc_func_init()` |
| QX003 | un slot pointe vers une fonction non definie dans les fichiers analyses | INFO | `resmgr_io_funcs_t()` |
| QX004 | un handler `read`/`write` n'appelle pas `iofunc_*_verify()` | ERROR | `iofunc_read_verify()` |
| QX005 | le chemin monte par `resmgr_attach()` est **relatif** | WARN | `resmgr_attach()` |
| QX006 | aucune boucle de messages **dans ce fichier** (`dispatch_block()`/`resmgr_block()`) | WARN | `resmgr_block()` |
| QX007 | la boucle bloque mais aucun handler n'est appele **dans ce fichier** | WARN | `resmgr_handler()` |
| QX008 | un slot de `io_funcs` n'est pas cable (le defaut POSIX s'applique) | INFO | `resmgr_io_funcs_t()` |
| QX009 | le reply renvoie plus de parties que `attr.nparts_max` n'en autorise | ERROR | `_RESMGR_NPARTS()` |
| QX010 | le nombre de slots de `iofunc_func_init()` est une macro | INFO | `iofunc_func_init()` |
| QX011 | aucune table **automatique** n'est initialisee par `iofunc_func_init()` | WARN | `iofunc_func_init()` |

Sortie : `0` si aucun constat actionnable, `1` si au moins un `ERROR` ou `WARN`,
`2` si l'appel est mal forme. Les constats `INFO` n'affectent jamais le code de
sortie : ils decrivent l'etat du gestionnaire, ils ne le condamnent pas.

**Ce qui a ete corrige dans cette version :** sept regles (QX001, QX002,
QX003, QX004, QX006, QX007, QX011) avaient un defaut connu qui contredisait la
documentation officielle. Elles sont maintenant corrigees, et chaque correction
est couverte par un test qui **echoue sur le code precedent** et **passe sur le
code actuel** — une regle qu'on a simplement supprimee ne prouverait rien. Le
detail, regle par regle, est dans **[RULES.md](RULES.md)**, section « Ce qui a
ete corrige dans cette version, et comment c'est prouve ».

Les trois dernieres ont ete trouvees en faisant tourner la sonde sur **17
vrais gestionnaires de ressources ecrits par d'autres personnes** — dont sept
publies par QNX ou BlackBerry eux-memes — et en relisant chaque constat a la
main. Le corpus, la mesure et les cinq defauts de l'outil qu'il a exposes
— neuf faux positifs dans cinq fichiers — sont dans
**[docs/BENCHMARK.fr.md](BENCHMARK.fr.md)**.

## Ce qui est dans le depot

```
.gitignore                                   ce que git ignore (artefacts de build, caches Python)
LICENSE                                      Apache-2.0, le texte integral
NOTICE                                       attribution du code de tiers et avis IA
README.md                                    ce fichier
RULES.md                                     chaque regle + sa source officielle QNX 8.0
pyproject.toml                               empaquetage optionnel : `pip install .` donne la commande `qx-probe`
qx_probe.py                                  la sonde (un seul fichier, sans dependance)
docs/AI-ASSISTED-RULES.md                    comment les onze regles ont ete ecrites, et comment chacune a ete prouvee
docs/BENCHMARK.fr.md                         le correspondant francais de docs/BENCHMARK.md, mis a jour avec lui
docs/BENCHMARK.md                            le benchmark : QX-PROBE sur 17 vrais gestionnaires de ressources QNX
docs/CODELAB.md                              le tutoriel pratique (30 minutes, aucun SDK requis)
docs/README.fr.md                            le correspondant francais de ce fichier, mis a jour avec lui : les parties qui n'ont pas ete retraduites decrivent encore la premiere version de l'outil
docs/README.md                               ce que sont les fichiers de docs/
docs/RULES.fr.md                             le correspondant francais de RULES.md, mis a jour avec lui
docs/SCENARIO.fr.md                          l'original francais de video/SCENARIO.md
docs/SUBMISSION-EN.md                        le texte de soumission DevPost, champ par champ
docs/YOUTUBE-VIDEO.md                        le paquet de publication YouTube (titre, description, fichier, miniature, etapes)
examples/blackberry_eventfd_mgr.c            le gestionnaire de ressources public de BlackBerry (Apache-2.0)
examples/qnx80_resmgr_minimal.c              gestionnaire de ressources canonique (ecrit pour ce depot)
examples/qnx80_resmgr_official_example.c     l'exemple officiel de la documentation QNX 8.0
examples/qnx80_resmgr_readonly.c             lecture seule, monte hors /dev/
examples/qnx80_resmgr_relative_path.c        declenche exactement un avertissement QX005
examples/sys/eventfd.h                       l'en-tete de l'exemple ci-dessus (Apache-2.0)
media/qx-demo-thumbnail.png                  la miniature de la video (PNG, 1280x720)
media/qx-demo-v2.mp4                         la video de demonstration (MP4, H.264, 1920x1080, 71,44 s)
scripts/audit-sous-titres-pixels.py          prouve que les sous-titres publies SONT les pixels de la video
scripts/benchmark-corpus.py                  fait tourner la sonde sur un corpus fige de 17 vrais gestionnaires de ressources QNX
scripts/build_qcc.sh                         compilation QNX 8.0 (necessite le SDP 8.0)
scripts/run_tests.sh                         lance la suite de tests
scripts/verifier-citations.py                relit les 14 pages QNX 8.0 citees et verifie les 36 citations
scripts/verifier-codelab.py                  rejoue chaque commande de docs/CODELAB.md et verifie sa sortie
scripts/verifier-soumission-devpost.py       verifie le texte de soumission : longueurs, anglais, liens
scripts/verify-all.sh                        rejoue toutes les preuves publiees en une commande
tests/fixtures/qnx80_resmgr_qx004_no_gate.c  le fichier sabote utilise par les tests et la video
tests/test_qx_probe.py                       27 tests : 10 anti-faux-positif, 15 detection, 2 format de sortie
tests/test_robustness.py                     8 tests : 20 variantes de l'exemple officiel dans des styles C courants (#if 0, litteral '}', garde a deux niveaux d'aides, = &handler, pointeur de table, fonction de reglage, garde en macro, delegation a iofunc_*_default())
tests/test_multifile.py                      17 tests : un gestionnaire de ressources eparti sur plusieurs fichiers lu comme un seul programme, la ligne de commande (--help, option inconnue, fichier absent) sans traceback
video/SCENARIO.md                            le scenario de la demonstration video
```

## Executer les tests

```console
$ bash scripts/run_tests.sh
```

La suite verifie les deux sens du contrat : les cas valides ne doivent
declencher **aucun** constat actionnable, et les cas failles doivent declencher
le constat attendu. Une regle qu'on a simplement supprimee ne prouve rien.

## Rejouer toutes les preuves en une commande

Toutes les preuves de ce depot sont rejouees par une seule commande, depuis
la racine du depot :

```console
$ bash scripts/verify-all.sh
```

Elle enchaine la suite de tests, la relecture du codelab, l'audit des pixels
de la video, la relecture des 14 pages QNX 8.0 citees, le controle du
texte de soumission et le benchmark sur 17 vrais gestionnaires de ressources
QNX, puis affiche un tableau : une ligne par verification, son resultat et
son code de sortie.

Avant ce tableau, la commande affiche le journal complet de chaque controle
— les 64 noms de tests, les 12 blocs du codelab rejoues, les 19 scenes de la
video auditees, les 36 citations relues et les 17 fichiers du benchmark :
**399 lignes** pour le premier des trois runs ci-dessous. Les trois blocs
qui suivent sont la **fin de la sortie REELLE** (mesuree le 14 novembre 2026
dans une copie de cette revision ou `docs/CODELAB.md` etait encore le
fichier public precedent — le controle C compare le codelab publie avec la
copie locale ; sur un clone frais de ce depot, chaque ligne se lit de la
meme facon) :

```console
======================================================================================================
SUMMARY - one line per verification
======================================================================================================
VERIFICATION                               RESULT       DETAIL                                           EXIT
------------------------------------------ ------------ ------------------------------------------------ ----
run_tests.sh (64 unit tests)               OK           -                                                0
verifier-codelab.py (12 blocks)            OK           -                                                0
audit-sous-titres-pixels.py (video)        OK           -                                                0
verifier-citations.py (36 quotations)      OK           -                                                0
verifier-soumission-devpost.py (13 blocks) OK           -                                                0
benchmark-corpus.py (17 real resource managers) OK           -                                                0
======================================================================================================
VERDICT: EVERY CHECK PASSED - 6/6 OK (RC 0)
======================================================================================================
```

**Voici la sortie REELLE sur une machine sans Pillow.** L'audit des pixels a
besoin de `ffmpeg`, `ffprobe` et `pillow` ; quand l'un d'eux manque, cette
verification est nommee dans le tableau, elle n'est **jamais** reportee OK, et
la commande dit ce qui manque :

```console
======================================================================================================
SUMMARY - one line per verification
======================================================================================================
VERIFICATION                               RESULT       DETAIL                                           EXIT
------------------------------------------ ------------ ------------------------------------------------ ----
run_tests.sh (64 unit tests)               OK           -                                                0
verifier-codelab.py (12 blocks)            OK           -                                                0
audit-sous-titres-pixels.py (video)        NOT CHECKED  dependency absent: pip install pillow            2
verifier-citations.py (36 quotations)      OK           -                                                0
verifier-soumission-devpost.py (13 blocks) OK           -                                                0
benchmark-corpus.py (17 real resource managers) OK           -                                                0
======================================================================================================
WHAT TO INSTALL (the checks that could not run need these):
  pip install pillow  - required by audit-sous-titres-pixels.py (video)
======================================================================================================
VERDICT: NO CHECK FAILED - 5/6 OK, 1 NOT CHECKED (RC 0)
         the check(s) that could not run on this machine are named in the
         table above and are never reported as OK: nothing was disproved,
         but these proofs were NOT re-run here (see the list below).
======================================================================================================
```

**Voici la sortie REELLE sur une machine sans reseau.** Les trois
verifications qui lisent le web ne peuvent pas etre faites, et elles le
disent :

```console
======================================================================================================
SUMMARY - one line per verification
======================================================================================================
VERIFICATION                               RESULT       DETAIL                                           EXIT
------------------------------------------ ------------ ------------------------------------------------ ----
run_tests.sh (64 unit tests)               OK           -                                                0
verifier-codelab.py (12 blocks)            OK           -                                                0
audit-sous-titres-pixels.py (video)        OK           -                                                0
verifier-citations.py (36 quotations)      NOT CHECKED  network absent: the pages could not be read      2
verifier-soumission-devpost.py (13 blocks) NOT CHECKED  network absent: the links could not be read      2
benchmark-corpus.py (17 real resource managers) NOT CHECKED  network absent: the corpus could not be fetched  2
======================================================================================================
VERDICT: NO CHECK FAILED - 3/6 OK, 3 NOT CHECKED (RC 0)
         the check(s) that could not run on this machine are named in the
         table above and are never reported as OK: nothing was disproved,
         but these proofs were NOT re-run here (see the list below).
======================================================================================================
```

**Le code de sortie repond a une seule question : une preuve publiee s'est-elle
revelee fausse ?** 0 = non (une verification qui n'a pas pu etre faite sur
cette machine est reportee NOT CHECKED, jamais OK) ; 1 = oui (au moins une
ligne est FAILED) ; 2 = la commande elle-meme n'a pas pu etre executee.

## Compiler pour QNX 8.0

```console
$ bash scripts/build_qcc.sh
```

Ce script utilise `qcc` du SDP 8.0 : il n'est donc **pas** exécutable sans le
SDK. Il s'arrête avec un message explicite si `qcc` est absent, et il n'invente
jamais une sortie de compilateur.

**La compilation n'est PAS MESUREE (NOT MEASURED).** Le SDP 8.0 n'est pas
installé dans l'environnement où ce projet a été écrit et aucune clé de licence
QNX n'y a été utilisée : les exemples n'ont jamais été compilés pour QNX 8.0,
et rien dans ce dépôt ne prétend le contraire.

## Licence

Code de QX-PROBE : Apache-2.0 (voir `LICENSE`).
L'exemple `examples/blackberry_eventfd_mgr.c` et l'en-tete `examples/sys/eventfd.h`
viennent du depot public `shim-demo` de BlackBerry et sont sous Apache-2.0 ;
l'en-tete de licence complet est conserve en tete de chaque fichier et l'avis
est dans `NOTICE`.

Assistance IA : ce projet a ete ecrit avec l'assistance d'un modele de langue.
La documentation officielle QNX 8.0 et le code de reference public de BlackBerry
sont les seules sources factuelles citees.
