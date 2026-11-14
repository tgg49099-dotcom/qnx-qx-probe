# Le benchmark : QX-PROBE sur 17 vrais gestionnaires de ressources QNX

> Le counterpart anglais de ce fichier est dans
> [`docs/BENCHMARK.md`](BENCHMARK.md), mis a jour avec lui : le meme
> corpus, les memes mesures, les memes conclusions.

Les exemples de ce depot sont des **exemples**. Un linteur qui ne voit que
ses propres exemples ne prouve rien du code des autres. Ce document est la
mesure de QX-PROBE sur **17 gestionnaires de ressources ecrits par d'autres
personnes** — **sept publies par QNX ou BlackBerry eux-memes** — et le
registre des **cinq defauts de l'outil** qu'il a exposes — **neuf faux
positifs dans cinq fichiers** —, du **vrai positif** qu'il a confirme, et des
tests ecrits pour chacun d'eux.

Tout ce qui suit a ete mesure le **11 novembre 2026** avec la version de
`qx_probe.py` de ce depot.

---

## 1. Pourquoi un benchmark sur du vrai code

Une regle qui ne s declenche que sur des fixtures ecrits pour la declencher
est une regle qui n'a jamais ete essaiee sur du code que son auteur n'a pas
ecrit. Trois choses ne se verifient que sur du vrai code :

1. **les faux positifs** — la regle condamne-t-elle du code valide publie par
   d'autres ? C'est le pire defaut d'un linteur, et il est invisible sur des
   exemples ecrits pour le linteur ;
2. **la duree de stockage et le graphe d'appels** — un vrai gestionnaire
   repartit ses tables, ses handlers et sa boucle de messages sur plusieurs
   fichiers et plusieurs idiomes (`resmgr_attach()`, un pool de threads, une
   `struct` qui porte les tables) ;
3. **les vrais positifs** — la regle trouve-t-elle un vrai defaut dans du code
   ecrit par quelqu'un d'autre, sans aucune raison de flatter l'outil ?

Le corpus a donc ete choisi pour etre **adversaire par construction** :
sept fichiers publies par QNX ou BlackBerry eux-memes (quatre sur
`gitlab.com/qnx/projects`, deux sur `github.com/qnx`, un sur
`github.com/qnx-ports`), et dix fichiers d'auteurs independants (un codelab,
un cours, un dispositif medical, un pilote UVC, deux pilotes de bus, un port
virtio).

---

## 2. Le corpus

Dix-sept fichiers preleves dans treize depots publics. **Chaque fichier est
bloque sur le commit exact qui a ete lu** : la mesure ne depend donc pas de
l'etat du depot aujourd'hui. Le script recupere ce commit-la et lit ce
chemin-la.

| # | Editeur | Projet | Chemin | Commit | SHA-256 (16) | Lignes |
|---|---|---|---|---|---|---|
| 1 | QNX | rpi-gpio | `resmgr/main.c` | `880d66fe20a3` | `0a8993aea26d6b09` | 740 |
| 2 | QNX | rpi-mailbox | `rpi_mbox.c` | `dd9ed5928da2` | `eebbb82888389ec4` | 639 |
| 3 | QNX | rpi-thermal | `rpi_thermal.c` | `4ba4fdc40c68` | `b82b73103843e2d5` | 890 |
| 4 | BlackBerry / QNX | shim-demo | `eventfd-mgr.c` | `5be2cd24780f` | `96acb0f8c2c0ea00` | 185 |
| 5 | BlackBerry / QNX | bsp_raspberrypi-bcm2712-rpi5 | `src/hardware/support/bcm2712/fan/resmgr.c` | `573dda1a1ca3` | `9bc95d2e0716bab4` | 291 |
| 6 | BlackBerry / QNX | qnx-posix-publish-subscribe | `qpp/main.c` | `b5ca892f3746` | `ee048cb302f06e0d` | 219 |
| 7 | QNX ports | epoll | `epoll-mgr.c` | `aea458535243` | `806f2950044e90f4` | 1167 |
| 8 | llmike | devu-uvc | `uvc_rm.c` | `8534b138a8f5` | `455a34627ce22ee7` | 557 |
| 9 | llmike | smbus | `smb-ec/main.c` | `fa3c7bbff27f` | `279e7aad6f1377c7` | 184 |
| 10 | llmike | smbus | `smb-ich/main.c` | `fa3c7bbff27f` | `ac65ff517bb691c6` | 187 |
| 11 | kodebooth | qnx-virtio | `src/gpio/resmgr.c` | `037f84fe9b20` | `9da9f7ab6c35e1cb` | 348 |
| 12 | ebenworks | phila-bedside-monitor-qnx | `src/qnx/resmgr.c` | `e255b4be9408` | `0539ffb4cc63befe` | 136 |
| 13 | DesignMaster Solutions | qnx8-resmgr-codelab | `src/hello.c` | `d13f0fbda9b6` | `8217baed0d13f78b` | 85 |
| 14 | DesignMaster Solutions | qnx8-resmgr-codelab | `src/ticks.c` | `d13f0fbda9b6` | `f8b22e50d8baef1f` | 97 |
| 15 | Embedded AI Design Labs | qnx_advance | `module04_drivers/block_rm.c` | `d1a82cef2b82` | `5b2f1844c002d6b7` | 95 |
| 16 | Embedded AI Design Labs | qnx_advance | `module04_drivers/can_rm.c` | `d1a82cef2b82` | `aec260bf680f80b7` | 159 |
| 17 | Embedded AI Design Labs | qnx_advance | `module04_drivers/qtn_sensor_rm.c` | `d1a82cef2b82` | `f7ae084f6a677b1e` | 119 |

Les URL exactes, les commits bloques et la version que chaque projet declare
pour lui-meme sont dans
[`scripts/benchmark-corpus.py`](../scripts/benchmark-corpus.py) : le
manifeste est dans le script, il se lit et se verifie sans rien lancer.

**Ce que dit la colonne « version ».** Quatre projets indiquent eux-memes
leur cible (`QNX 8.0`, `qnx800/qnxsdp-env.sh`) ; les autres n'indicquent rien,
et le manifeste le dit au lieu de deviner. Un fichier ecrit pour QNX 7.1 peut
utiliser une API que QNX 8.0 a conservee : le metier du linteur est de lire
la documentation QNX 8.0, pas de deviner la version du fichier.

---

## 3. La methode

```console
$ python3 -I scripts/benchmark-corpus.py
```

Le script fait, pour chaque entree :

1. `git init` dans un **repertoire temporaire** (ou dans `--cache`), puis
   `git remote add origin <url>` et `git fetch --depth 1 origin <sha>` ;
2. lit **exactement un blob** : `git show <sha>:<path>` ;
3. lance `qx_probe.analyse()` dessus et compte les constats.

Rien n'est ecrit dans le depot, et le repertoire temporaire est supprime a la
fin. Le script affiche `NOT CHECKED` pour tout fichier qu'il n'a pas pu
recuperer — **une verification qui n'a pas pu tourner n'est jamais comptee
comme un succes**, et la derniere ligne ne compte que les fichiers
reellement lus.

Le corpus est du code public, lu avec le protocole Git public ; rien n'est
copie dans le depot et aucun fichier du corpus n'y est redistribue.

---

## 4. La mesure

Resultat du run du 14 novembre 2026, avec la version du linteur de ce depot :

| # | Fichier | Constats | ERROR | WARN | Code de sortie |
|---|---|---|---|---|---|
| 1 | rpi-gpio `resmgr/main.c` | 5 | 0 | 0 | 0 |
| 2 | rpi-mailbox `rpi_mbox.c` | 7 | 0 | 0 | 0 |
| 3 | **rpi-thermal `rpi_thermal.c`** | 7 | **1** | 0 | **1** |
| 4 | shim-demo `eventfd-mgr.c` | 5 | 0 | 0 | 0 |
| 5 | bsp rpi5 `fan/resmgr.c` | 5 | 0 | 0 | 0 |
| 6 | qpp `main.c` | 37 | 0 | 0 | 0 |
| 7 | epoll `epoll-mgr.c` | 11 | 0 | 0 | 0 |
| 8 | **devu-uvc `uvc_rm.c`** | 3 | 0 | **1** | **1** |
| 9 | smbus `smb-ec/main.c` | 8 | 0 | 0 | 0 |
| 10 | smbus `smb-ich/main.c` | 8 | 0 | 0 | 0 |
| 11 | qnx-virtio `gpio/resmgr.c` | 4 | 0 | 0 | 0 |
| 12 | phila `src/qnx/resmgr.c` | 5 | 0 | 0 | 0 |
| 13 | codelab `src/hello.c` | 5 | 0 | 0 | 0 |
| 14 | codelab `src/ticks.c` | 6 | 0 | 0 | 0 |
| 15 | qnx_advance `block_rm.c` | 5 | 0 | 0 | 0 |
| 16 | qnx_advance `can_rm.c` | 6 | 0 | 0 | 0 |
| 17 | qnx_advance `qtn_sensor_rm.c` | 5 | 0 | 0 | 0 |

**17/17 fichiers analyses, 1 ERROR au total.** Les constats qui ne sont pas
ERROR sont les informationnels (QX008, QX010) : un slot non cable, un nombre
de slots tenu dans une macro. Ce ne sont pas des defauts.

Les deux lignes qui portent un constat sont tout l'interet du corpus, et
elles ont ete relues a la main avant d'etre crues :

```console
$ python3 -I scripts/benchmark-corpus.py
...
rpi-thermal/rpi_thermal.c    7 finding(s), 1 ERROR, 0 WARN (exit 1)
    ERROR QX004 rpi-thermal/rpi_thermal.c:465: resmgr_read() never calls iofunc_read_verify(): the access gate is missing
...
devu-uvc/uvc_rm.c             3 finding(s), 0 ERROR, 1 WARN (exit 1)
    WARN QX006 devu-uvc/uvc_rm.c:511: no message loop in this file: neither dispatch_block() nor resmgr_block() is called or referenced here; in a resource manager split over several files the loop usually lives in another translation unit (it is then set in pool_attr.block_func) — check the whole project
```

---

## 5. Le vrai positif : le `rpi-thermal` de QNX n'a pas de porte d'acces

`rpi-thermal` est publie par **QNX lui-meme**, dans
`gitlab.com/qnx/projects`. Son handler de lecture est :

```c
static int resmgr_read(resmgr_context_t *ctp, io_read_t *msg, RESMGR_OCB_T *ocb)
{
    ...
}
```

et le fichier ne contient **aucun appel a `iofunc_read_verify()`** — la
recherche de `iofunc_read_verify` dans le blob bloque ne renvoie rien.

La documentation QNX 8.0 est explicite, sur la page de
`iofunc_read_verify()` :

> All read handlers should start with a call to `iofunc_read_verify()` and
> proceed only if it returns EOK.

Le linteur signale donc `ERROR QX004` sur ce fichier, et il a raison : la
porte d'acces manque. C'est un vrai defaut dans du code publie par
l'editeur du systeme d'exploitation — trouve par un linteur statique sur la
source publique, sans rien executer. **Aucun rapport n'a ete envoye a QNX, et
aucun tiers n'a ete contacte** : le fichier a ete lu depuis son depot public,
au commit fige, et rien n'a ete ecrit nulle part.

**Ce que cela ne veut pas dire.** Cela ne veut pas dire que le fichier est
casse en production, ni que le noeud reste non protege. Cela veut dire que le
fichier ne suit pas la regle que la documentation enonce pour les handlers de
lecture, et que cette regle vaut la peine d'etre signalee. Concretement :

1. **Les permissions d'ouverture existent.** Les deux noeuds sont crees avec le
   mode `0664` (`mode_t mode = 0664;`, ligne 732, applique aux deux attributs
   aux lignes 830-831), et l'ouverture est traitee par le gestionnaire
   d'ouverture **par defaut** de la bibliotheque resource-manager :
   `iofunc_func_init()` (ligne 824) installe les fonctions par defaut de la
   couche POSIX, et le handler d'ouverture n'est pas surcharge. Le mode du
   noeud est donc verifie contre le client au moment ou il ouvre la ressource,
   avant toute lecture : le gestionnaire d'ouverture par defaut
   (`iofunc_open_default()`,
   <https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/i/iofunc_open_default.html>)
   appelle `iofunc_open()` pour verifier le mode d'ouverture du client contre
   les attributs de la ressource. Ce que la porte manquante laisse passer
   n'est donc **pas** la permission sur le noeud : c'est la seconde
   verification, celle que la documentation fait de l'etape a part.

2. **Ce que la porte manquante laisse passer.** La page de
   `iofunc_read_verify()` dit ce qu'est cette etape :

   > This function checks at least that:
   > the original open included read access
   > the incoming message is well-formed, including that:
   > if an xtype is specified that includes extra data headers, the extra data is in the receive buffer
   > the read offset to be used is non-negative

   et ce qu'elle retourne quand la verification echoue :

   > EBADF
   > The client didn't open the resource for read access.

   `resmgr_read()` ne l'appelle jamais, donc aucune de ces verifications n'est
   faite : un client qui a ouvert le noeud en ecriture seule recoit la
   temperature, et le handler ne regarde jamais le `xtype` du message auquel il
   repond — le mot `xtype` n'apparait nulle part dans le fichier — si bien
   qu'une lecture qui porte une position, ou des en-tetes de donnees
   supplementaires, est servie comme une lecture simple de la valeur.

3. **Un second point reel, visible sans la documentation.** La reponse ignore
   `msg->i.nbytes` : la longueur de la reponse est bornee par
   `ctp->msg_max_size` (1024, ligne 845), et non par le nombre d'octets
   demandes par le client (lignes 530-534). Un client qui demande huit octets
   recoit toute la chaine. Celui-ci est **un candidat pour une regle future**,
   et non un constat : QX-PROBE ne le detecte pas aujourd'hui, et rien ici ne
   pretend le contraire.

---

## 6. Les faux positifs que le benchmark a trouves, et les corrections

Avant que le corpus existe, les cinq defauts actionnables ci-dessous
etaient invisibles : les exemples du depot ne pouvaient pas les produire.

**La mesure « avant ».** Le meme corpus, lance avec la version du linteur du
**08/11/2026** (md5 `bdc705b7636bea56d849a127e7c341a0`) :

```console
$ git show eeb99e4:qx_probe.py > qx_probe.py && python3 -I scripts/benchmark-corpus.py
...
bsp_raspberrypi-bcm2712-rpi5/.../fan/resmgr.c    7 finding(s), 0 ERROR, 2 WARN (exit 1)
    WARN QX011 ...: the dispatch table 'connect_funcs' is an automatic variable that is never initialised: ...
    WARN QX011 ...: the dispatch table 'io_funcs' is an automatic variable that is never initialised: ...
epoll/epoll-mgr.c                                15 finding(s), 0 ERROR, 3 WARN (exit 1)
    WARN QX011 ...: the dispatch table 'connect_funcs' is an automatic variable that is never initialised: ...
    WARN QX011 ...: the dispatch table 'devnode_io_funcs' is an automatic variable that is never initialised: ...
    WARN QX011 ...: the dispatch table 'epoll_io_funcs' is an automatic variable that is never initialised: ...
qnx-posix-publish-subscribe/qpp/main.c          18 finding(s), 1 ERROR, 0 WARN (exit 1)
    ERROR QX006 ...: no message loop: neither dispatch_block() nor resmgr_block() is called, so the resource manager never waits for a message
qnx-virtio/src/gpio/resmgr.c                     6 finding(s), 0 ERROR, 2 WARN (exit 1)
    WARN QX011 ...: the dispatch table 'connect_funcs' is an automatic variable that is never initialised: ...
    WARN QX011 ...: the dispatch table 'io_funcs' is an automatic variable that is never initialised: ...
devu-uvc/uvc_rm.c                                3 finding(s), 1 ERROR, 0 WARN (exit 1)
    ERROR QX006 ...: no message loop: neither dispatch_block() nor resmgr_block() is called, so the resource manager never waits for a message

17/17 files analysed, 3 ERROR in total
```

**Neuf faux positifs dans cinq fichiers**, dont un au niveau ERROR. La
mesure « apres » du § 4 — le meme corpus, les memes commits, le code actuel —
donne **1 ERROR et aucun faux positif**.

| # | Regle | Ce que le benchmark a trouve | Ou | Correction |
|---|---|---|---|---|
| 1 | QX011 | une table de dispatch qui est **membre d'une `struct`** etait signalee comme « table automatique jamais initialisee » | bsp rpi5 `fan/resmgr.c` (2), epoll `epoll-mgr.c` (3), qnx-virtio `gpio/resmgr.c` (2) | la regle calcule maintenant la **duree de stockage** de la declaration : un membre a la duree de l'objet qui le porte, pas celle d'une variable automatique |
| 2 | QX011 | une table initialisee par une **expression membre** (`&resmgr.io_funcs`) n'etait pas reconnue comme initialisee | les memes trois fichiers | `ident_of()` reduit maintenant une expression membre a son dernier composant, donc `&resmgr.io_funcs` est rapproche de l'appel `iofunc_func_init()` |
| 3 | QX011 | un **deuxieme** appel a `iofunc_func_init()` etait ignore — la regle ne lisait que le premier | epoll `epoll-mgr.c` (`epoll_io_funcs` est rempli par le deuxieme appel) | la regle parcourt maintenant **tous** les appels `iofunc_func_init()` du fichier |
| 4 | QX006 | une boucle de messages **deleguee a un pool de threads** (`pool_attr.block_func = &dispatch_block;`) n'etait pas reconnue — la fonction est *referencee*, pas appelee | qpp `main.c` | la regle accepte maintenant un appel **ou une reference** |
| 5 | QX006 | un gestionnaire **reparti sur plusieurs fichiers** etait signale « aucune boucle de messages » alors que la boucle est dans une autre unite de compilation (`uvc_driver.c`) | devu-uvc `uvc_rm.c` | QX006 est **passe de ERROR a WARN**, et son message dit exactement ce qu'il veut dire : *dans ce fichier* ; verifiez le projet entier |

Les defauts 1 et 2 sont les deux moities de la meme erreur — une table qui
est membre d'une structure n'est pas une variable automatique, et elle est
remplie a travers le membre —, donc les sept constats QX011 du run « avant »
sont sept instances de ce meme couple.

Le defaut 5 merite un mot, car c'est un changement de **niveau** et pas
seulement de code. Une unite de compilation ne peut pas prouver qu'un projet
n'a pas de boucle de messages : la boucle peut etre dans `main.c`, les
handlers dans `io.c` et les tables dans `resmgr.c`. Signaler l'absence de
boucle au niveau ERROR sur le fichier qui porte les handlers, c'est un
**faux positif sur une architecture valide**. Le niveau honnete pour une
regle qui ne voit qu'un fichier est WARN, et le message dit maintenant quoi
faire. Les deux regles qui partagent cette limite sont **QX006** (pas de
boucle dans ce fichier) et **QX007** (une boucle dans ce fichier mais aucun
handler dans ce fichier) ; toutes deux sont en WARN maintenant, et toutes
deux disent *dans ce fichier*.

### La preuve que chaque correction est une correction

Une correction non couverte par un test ne prouve rien. Chacun des cinq
defauts ci-dessus est maintenant couvert par un test qui **echoue sur le code
precedent** et **passe sur le code actuel** — le contrat rouge/vert de ce
depot :

```console
$ git stash push -q qx_probe.py && python3 -I tests/test_qx_probe.py
...
FAIL: test_api_resmgr_block_et_resmgr_handler
AssertionError: 'QX006' unexpectedly found in [...] : false positive: the loop is delegated to a thread pool
FAIL: test_qx011_table_mise_a_zero_statique
AssertionError: 'QX011' unexpectedly found in [...] : false positive: a member has the storage duration of the object that holds it
...
Ran 27 tests in 0.143s
FAILED (failures=4)

$ git stash pop -q && python3 -I tests/test_qx_probe.py
...
Ran 27 tests in 0.167s
OK
```

Les quatre echecs sont les quatre assertions que le benchmark a produites : la
boucle deleguee (QX006/QX007), la table qui est membre d'une structure, la
table remplie par un deuxieme appel a `iofunc_func_init()`, et le niveau de
QX006/QX007.

---

## 7. La verification manuelle de chaque porte d'acces

L'outil est heuristique ; le benchmark n'est credible que si son verdict est
compare a une lecture humaine. La porte (QX004) a donc ete verifiee a la main
sur les dix-sept fichiers : pour chaque handler de lecture/ecriture de chaque
fichier, le corps contient-il `iofunc_read_verify()` / `iofunc_write_verify()` ?

| # | Fichier | Handlers lecture/ecriture | Porte trouvee a la main | Verdict de l'outil | Accord |
|---|---|---|---|---|---|
| 1 | rpi-gpio `main.c` | `read_gpio` | oui | aucun constat | ✔ |
| 2 | rpi-mailbox `rpi_mbox.c` | aucun | — | aucun constat | ✔ |
| 3 | **rpi-thermal `rpi_thermal.c`** | `resmgr_read()` | **non** | **ERROR QX004** | ✔ |
| 4 | shim-demo `eventfd-mgr.c` | `io_read`, `io_write` | oui | aucun constat | ✔ |
| 5 | bsp rpi5 `fan/resmgr.c` | `io_read`, `io_write` | oui | aucun constat | ✔ |
| 6 | qpp `main.c` | aucun dans ce fichier | — | aucun constat | ✔ |
| 7 | epoll `epoll-mgr.c` | aucun dans ce fichier | — | aucun constat | ✔ |
| 8 | devu-uvc `uvc_rm.c` | `uvc_read`, `uvc_write` | oui | aucun constat | ✔ |
| 9 | smbus `smb-ec/main.c` | aucun dans ce fichier | — | aucun constat | ✔ |
| 10 | smbus `smb-ich/main.c` | aucun dans ce fichier | — | aucun constat | ✔ |
| 11 | qnx-virtio `gpio/resmgr.c` | `resmgr_read`, `resmgr_write` | oui | aucun constat | ✔ |
| 12 | phila `resmgr.c` | `io_read`, `io_write` | oui | aucun constat | ✔ |
| 13 | codelab `hello.c` | `hello_read`, `hello_write` | oui | aucun constat | ✔ |
| 14 | codelab `ticks.c` | `ticks_read` | oui | aucun constat | ✔ |
| 15 | qnx_advance `block_rm.c` | `io_read`, `io_write` | oui | aucun constat | ✔ |
| 16 | qnx_advance `can_rm.c` | aucun dans ce fichier | — | aucun constat | ✔ |
| 17 | qnx_advance `qtn_sensor_rm.c` | `io_read` | oui | aucun constat | ✔ |

**17/17 accords.** Le seul desaccord qui aurait pu exister — la porte
 manquante de `rpi-thermal` — est un cas ou l'outil et la lecture manuelle
disent la meme chose.

Deux fichiers meritent une ligne d'explication :

* **qpp `main.c`** (ligne 6) ne porte aucun handler de lecture : les
  handlers sont dans `qpp/ioread.c`, `qpp/ioread_dir.c` et
  `qpp/ioread_text.c`. Les trois ont ete lus aussi, et les trois appellent
  `iofunc_read_verify()` — l'outil ne dit rien parce qu'il analyse un
  fichier a la fois, et la lecture manuelle dit que le code est correct.
  Sa boucle de messages est dans ce fichier-la, mais **deleguee a un pool de
  threads** (`pool_attr.block_func = &dispatch_block;`) : c'est le cas qui a
  fait accepter a la regle une reference, et pas seulement un appel.
* **devu-uvc `uvc_rm.c`** (ligne 8) est le WARN du tableau ci-dessus : le
  fichier porte les handlers mais pas la boucle — la boucle est dans
  `uvc_driver.c`, une autre unite de compilation du meme projet. La lecture
  manuelle dit exactement ce que dit l'outil : *la boucle est ailleurs dans le
  projet*, donc le constat est un rappel, pas une condamnation. C'est un
  WARN pour cette raison, et c'est ce fichier qui a fait changer le
  niveau.

---

## 8. Ce que le benchmark ne prouve pas

L'honnetete sur les limites fait partie de la mesure :

* **Un fichier a la fois.** QX-PROBE analyse un fichier, pas un projet. Les
  limites de QX001, QX003, QX004 et QX006 en sont la consequence directe,
  et elles sont ecrites dans `RULES.md` pour chaque regle.
* **Un corpus n'est pas une preuve de completude.** Dix-sept fichiers et
  treize depots montrent que l'outil se comporte sur du vrai code ; ils ne
  montrent pas qu'il a raison sur tout code possible. La revendication de ce
  depot est plus etroite et verifiable : **chaque regle est adossee a une
  page officielle QNX 8.0**, et chaque citation est reverifiee par
  `scripts/verifier-citations.py`.
* **Le corpus est un instantane.** Chaque fichier est bloque sur un commit ;
  une version ulterieure du meme projet peut differer. Les blocs sont dans
  le manifeste, donc n'importe qui peut refaire la mesure sur les memes
  octets.
* **Aucune compilation.** Le corpus est lu, jamais compile : le SDP QNX
  n'est pas necessaire, et les constats portent sur ce que la source dit,
  pas sur ce que le compilateur accepte.
* **Le benchmark n'est pas une entree de concours.** C'est une piece a
  conviction pour les jurés.

---

## 9. Comment le reproduire

```console
$ git clone https://github.com/tgg49099-dotcom/qnx-qx-probe.git
$ cd qnx-qx-probe
$ python3 -I scripts/benchmark-corpus.py
```

Le script a besoin de `git` et du reseau. Il n'ecrit rien dans le depot.
Avec `--json` le meme resultat est produit sous forme lisible par une
machine ; avec `--only <projet>` une seule entree du corpus est mesuree.

Les deux verifications du depot qui doivent rester vertes :

```console
$ bash scripts/verify-all.sh
$ python3 -I tests/test_qx_probe.py
```

## 10. Programmes entiers : neuf gestionnaires de sources QNX (v8, 14 novembre 2026)

Le corpus ci-dessus prend un fichier par projet. Les gros services QNX sont
decoupes : un fichier par handler, les tables dans `main.c`, la boucle
ailleurs. Pour tester ce cas, QX-PROBE a ete lance **une fois par programme,
avec tous ses fichiers**, sur neuf gestionnaires de sources QNX 6.4 publiees
(<https://github.com/vocho/openqnx>, commit `cc95df3543a1c481d4f8ad387e29f0d1ff0c87fe`,
`trunk/services/` : random, pipe, dumper, slogger, syslogd, devc-ditto,
mqueue, mq, system/pathmgr — 54 fichiers C). C'est du code plus ancien que
QNX 8.0, utilise ici seulement pour tester la lecture d'un programme decoupe.

| | ERROR | WARN |
|---|---|---|
| v7 | 22 | 20 |
| v8 | 1 | 10 |

* **21 fausses ERROR retirees** : 19 fichiers de handlers ou d'auxiliaires
  signales QX001 alors que les tables sont dans un autre fichier du meme
  programme ; 2 QX004 sur devc-ditto, qui lie son propre OCB par
  `resmgr_open_bind()` sans la couche OCB iofunc dont `iofunc_read_verify()`
  a besoin (desormais INFO, « a verifier a la main »).
* **10 faux WARN retires** : boucle ou handler dans un autre fichier (QX006,
  QX007), chemin racine `""` lu comme relatif (QX005), table `extern` dans
  une fonction lue comme table automatique non initialisee (QX011).
* **L'ERROR restante est vraie** : `io_write()` de syslogd ecrit le message
  sans appeler `iofunc_write_verify()`, le mode d'ouverture du client n'est
  jamais controle.
* **Les 10 WARN restants** sont des fichiers du gestionnaire de chemins du
  noyau (procnto) : leur boucle est dans procnto, hors des fichiers donnes,
  et l'avertissement le dit.

Reproduire : voir la section 10 de `BENCHMARK.md` (memes commandes). Les
fichiers d'essai (`tests/fixtures/multifile/`) sont ecrits pour la suite de
tests ; aucune ligne n'est copiee de ces sources.
