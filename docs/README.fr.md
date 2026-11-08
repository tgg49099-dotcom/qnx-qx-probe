# QX-PROBE — analyseur statique du protocole resource-manager QNX 8.0

QX-PROBE lit du code C et signale les **faux positifs que l'on ne peut pas se
permettre** dans un driver QNX 8.0 : un gestionnaire de ressources qui n'appelle
jamais `iofunc_read_verify()`, une boucle de messages qui bloque sans distribuer,
un reply qui renvoie plus de parties que l'IOV n'en contient.

C'est un outil **hôte** : il tourne sur Linux, macOS ou Windows, il n'a
**aucune dépendance** et il ne demande **ni SDK QNX ni carte QNX**. C'est ce qui
le rend utilisable dans une chaine d'integration continue, ou dans un jury qui
n'a pas de materiel.

```console
$ python3 -I qx_probe.py examples/qnx80_resmgr_minimal.c
INFO  QX008  examples/qnx80_resmgr_minimal.c: io_funcs.devctl is not assigned (the POSIX default iofunc_devctl_default() applies unless you override it)
...
RESULTAT: 5 constat(s), 0 ERROR, 0 WARN
```

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
QNX SDP 8.0 (les pages citees sont mises a jour le 11 juin 2026). Le detail
regle par regle, avec la citation et l'URL, est dans **[RULES.md](RULES.md)**.

## Les onze regles

| Code | Ce que la sonde signale | Niveau | Source officielle QNX 8.0 |
|---|---|---|---|
| QX001 | le fichier utilise l'API resmgr mais ne cable aucune table de dispatch | ERROR | `resmgr_attach()` |
| QX002 | plus de slots cables que `iofunc_func_init()` n'en remplit | ERROR | `iofunc_func_init()` |
| QX003 | un slot pointe vers une fonction non definie dans le fichier | ERROR | `resmgr_io_funcs_t()` |
| QX004 | un handler `read`/`write` n'appelle pas `iofunc_*_verify()` | ERROR | `iofunc_read_verify()` |
| QX005 | le chemin monte par `resmgr_attach()` est **relatif** | WARN | `resmgr_attach()` |
| QX006 | aucune boucle de messages (`dispatch_block()`/`resmgr_block()`) | ERROR | `resmgr_block()` |
| QX007 | la boucle bloque mais aucun handler n'est appele | ERROR | `resmgr_handler()` |
| QX008 | un slot de `io_funcs` n'est pas cable (le defaut POSIX s'applique) | INFO | `resmgr_io_funcs_t()` |
| QX009 | le reply renvoie plus de parties que `attr.nparts_max` n'en autorise | ERROR | `_RESMGR_NPARTS()` |
| QX010 | le nombre de slots de `iofunc_func_init()` est une macro | INFO | `iofunc_func_init()` |
| QX011 | aucune table n'est initialisee par `iofunc_func_init()` | WARN | `iofunc_func_init()` |

Sortie : `0` si aucun constat actionnable, `1` si au moins un `ERROR` ou `WARN`,
`2` si l'appel est mal forme. Les constats `INFO` n'affectent jamais le code de
sortie : ils decrivent l'etat du gestionnaire, ils ne le condamnent pas.

**Ce qui a ete corrige dans cette version :** cinq regles (QX001, QX002,
QX003, QX004, QX011) avaient un defaut connu qui contredisait la
documentation officielle. Elles sont maintenant corrigees, et chaque correction
est couverte par un test qui **echoue sur le code precedent** et **passe sur le
code actuel** — une regle qu'on a simplement supprimee ne prouverait rien. Le
detail, regle par regle, est dans **[RULES.md](RULES.md)**, section « Ce qui a
ete corrige dans cette version, et comment c'est prouve ».

## Ce qui est dans le depot

```
.gitignore                                   ce que git ignore (artefacts de build, caches Python)
LICENSE                                      Apache-2.0, le texte integral
NOTICE                                       attribution du code de tiers et avis IA
README.md                                    ce fichier
RULES.md                                     chaque regle + sa source officielle QNX 8.0
qx_probe.py                                  la sonde (un seul fichier, sans dependance)
docs/AI-ASSISTED-RULES.md                    comment les onze regles ont ete ecrites, et comment chacune a ete prouvee
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
scripts/build_qcc.sh                         compilation QNX 8.0 (necessite le SDP 8.0)
scripts/run_tests.sh                         lance la suite de tests
scripts/verifier-citations.py                relit les 12 pages QNX 8.0 citees et verifie les 29 citations
scripts/verifier-codelab.py                  rejoue chaque commande de docs/CODELAB.md et verifie sa sortie
scripts/verifier-soumission-devpost.py       verifie le texte de soumission : longueurs, anglais, liens
scripts/verify-all.sh                        rejoue toutes les preuves publiees en une commande
tests/fixtures/qnx80_resmgr_qx004_no_gate.c  le fichier sabote utilise par les tests et la video
tests/test_qx_probe.py                       27 tests : 10 anti-faux-positif, 15 detection, 2 format de sortie
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
de la video, la relecture des 12 pages QNX 8.0 citees et le controle du
texte de soumission, puis affiche un tableau : une ligne par verification,
son resultat et son code de sortie. Elle ne sort en 0 que si chaque ligne
est OK ; une verification qui n'a pas pu etre faite est NOT CHECKED, jamais
OK.

## Compiler pour QNX 8.0

```console
$ bash scripts/build_qcc.sh
```

Ce script utilise `qcc` du SDP 8.0 : il n'est donc **pas** exécutable sans le
SDK. Il s'arrête avec un message explicite si `qcc` est absent, et il n'invente
jamais une sortie de compilateur.

## Licence

Code de QX-PROBE : Apache-2.0 (voir `LICENSE`).
L'exemple `examples/blackberry_eventfd_mgr.c` et l'en-tete `examples/sys/eventfd.h`
viennent du depot public `shim-demo` de BlackBerry et sont sous Apache-2.0 ;
l'en-tete de licence complet est conserve en tete de chaque fichier et l'avis
est dans `NOTICE`.

Assistance IA : ce projet a ete ecrit avec l'assistance d'un modele de langue.
La documentation officielle QNX 8.0 et le code de reference public de BlackBerry
sont les seules sources factuelles citees.
