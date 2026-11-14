# Regles de QX-PROBE et leurs sources officielles QNX 8.0

Chaque regle de la sonde est adossee a une page de la documentation officielle
**BlackBerry QNX SDP 8.0** (QNX OS 8.0 C Library Reference). Les 14 pages
citees ci-dessous ont ete relues les **12 et 14 novembre 2026** : les 14 ont repondu
HTTP 200 et chacune porte la date de mise a jour que QNX lui a donnee
(`Page updated: November 05, 2026`). Cette date est affichee par
`scripts/verifier-citations.py`.

Convention de lecture : une regle sans source officielle est une regle qui
n'existe pas. Quand la documentation contredit une regle, c'est la regle qui
cede — jamais le code canonique de QNX.

---

## QX001 — aucune table de dispatch cablee

* **Niveau :** ERROR
* **Source :** `resmgr_attach()`
  <https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/r/resmgr_attach.html>
* **Ce que dit la doc :** `resmgr_attach()` prend `connect_funcs` et `io_funcs`,
  « a pointer to the `resmgr_connect_funcs_t` structure that defines the
  POSIX-level connect functions » ; sans ces tables, le gestionnaire n'a rien a
  executer pour le client.
* **Limite connue :** la detection est lexicale (`.slot = handler`). Un
  initialiseur de structure C99 (`resmgr_io_funcs_t f = { .read = my_read };`)
  ou un nom de variable libre n'est pas vu. Une regle plus fine est prevue mais
  n'est pas implementee : mieux vaut un constat manquant qu'un faux positif.

## QX002 — plus de slots cables que `iofunc_func_init()` n'en remplit

* **Niveau :** ERROR
* **Source :** `iofunc_func_init()`
  <https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/i/iofunc_func_init.html>
* **Ce que dit la doc :** « The `nconnect` and `nio` arguments indicate how many
  entries this function should fill. This is in place to support forward
  compatibility. » — `nio` designe un **nombre d'entrees a remplir**, pas une
  borne de tableau.
* **Limite connue :** la regle compte les slots cables, pas les slots
  *positionnes* dans la structure. Ce defaut a ete corrige dans cette version
  (voir la section « Ce qui a ete corrige dans cette version, et comment c'est
  prouve » de ce fichier).

## QX003 — un slot pointe vers une fonction non definie

* **Niveau :** INFO (c'etait ERROR avant cette version)
* **Source :** `resmgr_io_funcs_t()`
  <https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/r/resmgr_io_funcs_t.html>
* **Ce que dit la doc :** chaque membre de la table est un pointeur de fonction
  (`int (*read)(resmgr_context_t *ctp, io_read_t *msg, RESMGR_OCB_T *ocb);`).
  Un pointeur nul ou vers une fonction inexistante n'est pas un gestionnaire.
* **Ce que verifie la regle :** le handler affecte a un slot n'est ni defini ni
  declare dans les fichiers analyses. Le constat dit exactement la condition :
  « if it is not defined in another translation unit, the link will fail ».
* **Ce qui a change dans cette version :** une seule unite de compilation ne
  peut pas prouver qu'un symbole manque — un handler defini dans un autre
  fichier est parfaitement legal. La regle ne condamne donc plus le code :
  elle est passee de **ERROR** a **INFO**, et la CLI resout desormais les
  symboles de **tous** les fichiers qu'elle analyse : le constat disparait
  des que le handler est defini ailleurs.

## QX004 — la porte d'acces `iofunc_*_verify()` est absente

* **Niveau :** ERROR
* **Sources :**
  * `iofunc_read_verify()` <https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/i/iofunc_read_verify.html>
  * `iofunc_write_verify()` <https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/i/iofunc_write_verify.html>
  * `iofunc_read_default()` <https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/i/iofunc_read_default.html>
  * `iofunc_write_default()` <https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/i/iofunc_write_default.html>
* **Ce que dit la doc :** « All read handlers should start with a call to
  `iofunc_read_verify()` and proceed only if it returns EOK. »
* **Ce que verifie la regle :** le corps du handler `read`/`write`, chaines et
  commentaires effaces, doit contenir la porte — directement, ou via une
  fonction auxiliaire du meme fichier (un controle delegue est un controle).
  Un handler qui appelle le traitement POSIX par defaut
  `iofunc_read_default()` / `iofunc_write_default()` a aussi sa porte : les
  pages officielles de ces fonctions (relues le 14 novembre 2026) disent
  « The `iofunc_read_default()` function calls `iofunc_read_verify()` to
  verify if this read operation should be permitted » (de meme pour
  l'ecriture). Un appel compte ; une mention en commentaire ou en chaine non.
* **Ce qui a change dans cette version :** la recherche etait purement
  textuelle. Un controle delegue a une fonction auxiliaire etait signale
  comme une porte manquante (faux positif), et le *nom* de la porte cite
  dans un message d'erreur etait pris pour une verification (faux negatif).
  Les deux sont corriges : les chaines et les commentaires sont effaces
  avant la recherche, et un appel delegue compte.
* **Limite connue :** la porte est cherchee dans le corps du handler, **dans
  le fichier analyse** : un controle delegue a une fonction auxiliaire d'un
  **autre** fichier est toujours signale comme une porte manquante, meme si
  cette auxiliaire fait partie des fichiers analyses. Une auxiliaire du
  **meme** fichier est acceptee, et une porte seulement citee dans une chaine
  ne compte pas.

## QX005 — le chemin monte par `resmgr_attach()` est relatif

* **Niveau :** WARN
* **Source :** `resmgr_attach()`
  <https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/r/resmgr_attach.html>
* **Ce que dit la doc :**
  > The `resmgr_attach()` function puts the path into the **general pathname
  > space** and binds requests on this path to the dispatch handle `dpp`. You
  > usually provide an absolute path; if you provide a path that doesn't start
  > with a slash, it's considered to be relative to the current working
  > directory.
* **Pourquoi cette regle existe (et pourquoi elle est etroite) :** une version
  anterieure de l'outil exigeait un point de montage sous `/dev/`. C'etait
  **faux** : le pathname space de QNX est general, et `/var/run/...`, `/tmp/...`,
  `/etc/...` sont des points de montage valides. Signaler ces cas etait un faux
  positif sur du code canonique — le pire genre d'erreur pour cet outil.
  La regle actuelle ne signale que le cas documente comme dependant du
  repertoire courant : un chemin **relatif**.
* **Ce que la regle ne fait pas :** elle n'exige rien sur le prefixe
  (`/dev/` ou autre) et elle ne se déclenche pas si le chemin n'est pas un
  litteral (variable, macro) — dans ce cas, on ne peut rien dire.

## QX006 — aucune boucle de messages

* **Niveau :** WARN
* **Sources :**
  * `resmgr_block()` <https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/r/resmgr_block.html>
  * `dispatch_block()` <https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/d/dispatch_block.html>
* **Ce que dit la doc :** `resmgr_block()` « waits for a message » et « is a
  special case of `dispatch_block()` ». Un gestionnaire qui n'appelle ni l'un ni
  l'autre n'attend jamais de message : il ne fait rien.
* **Pourquoi les deux API sont acceptees :** l'exemple de reference de la
  documentation QNX 8.0 utilise `resmgr_block()`, pas `dispatch_block()`. Exiger
  l'un des deux produirait un faux positif sur le code de reference.
* **Ce qui a change dans cette version :** la regle cherchait un **appel** a
  `dispatch_block()` ou `resmgr_block()`. Un gestionnaire qui delegue la
  boucle a un **pool de threads** — `pool_attr.block_func = &resmgr_block;` —
  ne les appelle jamais : il les *reference*. La regle accepte maintenant un
  appel **ou une reference**.
* **Ce qui a change dans cette version (le niveau) :** la regle etait en
  **ERROR**, elle est maintenant en **WARN**. QX-PROBE analyse **un fichier a
  la fois**, et la boucle d'un gestionnaire reparti sur plusieurs fichiers vit
  dans une autre unite de compilation : signaler l'absence de boucle en ERROR
  sur le fichier qui porte les handlers, c'est un faux positif sur une
  architecture valide. Le niveau est maintenant celui qu'un outil qui ne voit
  qu'un fichier peut defendre, et le message dit exactement ce qu'il veut dire
  — *dans ce fichier* — et ou regarder (`pool_attr.block_func`). La mesure qui
  a motive ce changement est dans
  [`docs/BENCHMARK.fr.md`](BENCHMARK.fr.md) §6.
* **Limite connue :** la regle ne voit pas les autres fichiers du projet. Elle
  dit ce que contient le fichier analyse, et le dit dans son message.

## QX007 — la boucle bloque mais aucun handler n'est appele

* **Niveau :** WARN
* **Sources :**
  * `resmgr_handler()` <https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/r/resmgr_handler.html>
  * `dispatch_handler()` <https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/d/dispatch_handler.html>
* **Ce que dit la doc :** `resmgr_handler()` « handles the message received in
  `ctp` » et « is a special case of `dispatch_handler()` ». Sans appel a l'un des
  deux, le message reste en attente et le client ne recoit jamais de reponse.
* **Ce qui a change dans cette version (le niveau) :** comme QX006, cette
  regle etait en **ERROR** et elle est maintenant en **WARN**, pour la meme
  raison : un handler peut vivre dans une autre unite de compilation, et un
  fichier seul ne peut pas prouver que le projet ne traite rien.
* **Limite connue :** la regle ne voit pas les autres fichiers du projet. Un
  fichier qui bloque sans appeler de handler est un **rappel de verifier le
  projet entier**, pas une condamnation du fichier.

## QX008 — un slot de `io_funcs` n'est pas cable

* **Niveau :** INFO
* **Source :** `resmgr_io_funcs_t()`
  <https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/r/resmgr_io_funcs_t.html>
* **Ce que dit la doc :** « You can initialize this table by calling
  `iofunc_func_init()` and then overriding the defaults with your own
  functions. » Chaque membre a une valeur par defaut documentee dans la
  colonne « Default » de la table : `iofunc_read_default()` pour `read`,
  `iofunc_write_default()` pour `write`, `iofunc_devctl_default()` pour
  `devctl`, `iofunc_unblock_default()` pour `unblock` ; `notify`, lui, n'a
  **aucun** defaut (« None »).
* **Pourquoi INFO et pas ERROR :** un gestionnaire en **lecture seule** (pas de
  `write`) ou en **ecriture seule** (pas de `read`) est parfaitement valide.
  Exiger `read` et `write` en ERROR bloquait des gestionnaires valides — c'etait
  un faux positif fatal. Les slots 64 bits (`read64`, `write64`, `notify64`,
  `utime64`) sont pris en compte comme equivalents de leurs homologues 32 bits.

## QX009 — le reply renvoie plus de parties que l'IOV n'en contient

* **Niveau :** ERROR
* **Sources :**
  * `resmgr_attach()` <https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/r/resmgr_attach.html>
  * `resmgr_context_t()` <https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/r/resmgr_context_t.html>
  * `_RESMGR_NPARTS()` <https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/r/_resmgr_nparts.html>
* **Ce que dit la doc :**
  > `resmgr_attach()` — `nparts_max` : « The number of components to allocate
  > for the IOV array. »
  >
  > `resmgr_context_t()` — `iov` : « An I/O vector where you can place the data
  > that you're returning to the client. This defaults to one entry, but can be
  > configured by the `attr.nparts_max` parameter. »
  >
  > `_RESMGR_NPARTS()` — Caveats : « The `resmgr_attach()` function should set
  > `attr->nparts_max` to be the maximum value for `num`. »
* **Ce que la regle verifie :** si le fichier declare
  `resmgr_attr.nparts_max = N` et qu'un handler renvoie `_RESMGR_NPARTS(k)`
  avec `k > N`, la reponse au client porterait plus de parties que l'IOV n'en
  contient.
* **Preuve de non-faux-positif :** le `k` n'est retenu que s'il est connu sans
  ambiguite (litteral, ou une seule affectation dans le handler). Dans le doute,
  la regle ne dit rien.

## QX010 — le nombre de slots de `iofunc_func_init()` est une macro

* **Niveau :** INFO
* **Source :** `iofunc_func_init()`
  <https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/i/iofunc_func_init.html>
* **Ce que dit la doc :** « Typically, you pass `_RESMGR_CONNECT_NFUNCS` for this
  argument » et « Typically, you pass `_RESMGR_IO_NFUNCS` ». C'est le cas normal ;
  la sonde le signale comme information, et n'en tire aucune conclusion
  (pas de faux « overflow »).

## QX011 — aucune table n'est initialisee par `iofunc_func_init()`

* **Niveau :** WARN
* **Source :** `iofunc_func_init()`
  <https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/i/iofunc_func_init.html>
* **Ce que dit la doc :** c'est cette fonction qui remplit les tables avec les
  valeurs par defaut POSIX. Sans elle, les pointeurs restent a leur valeur
  initiale.
* **Ce qui a change dans cette version :** la regle signalait **toute** table
  qui n'etait pas remplie par `iofunc_func_init()`, y compris les tables
  statiques. Une table statique est mise a zero par C — c'est un choix
  deliberé (les handlers sont NULL et la couche de base repond ENOSYS), pas un
  bug. Le faux positif a disparu ; l'avertissement tombe toujours sur le cas
  pour lequel il a ete ecrit.
* **Ce qui a change dans cette version (la duree de stockage) :** la regle
  decidait qu'une table etait « automatique » parce que sa declaration ne
  disait pas `static`. Une table qui est **membre d'une structure** a la duree
  de stockage de l'objet qui la porte, et elle est remplie a travers le membre
  (`iofunc_func_init(…, &resmgr.io_funcs)`). Les deux etaient signales a tort
  sur de vrais gestionnaires de ressources, dont un publie par QNX lui-meme.
  La regle calcule maintenant la duree de stockage de la declaration, et
  reconnait une initialisation faite par expression membre.
* **Ce qui a change dans cette version (chaque appel) :** la regle lisait le
  **premier** appel a `iofunc_func_init()` du fichier et ignorait les suivants.
  Un gestionnaire peut remplir deux tables io — une par device — et la
  deuxieme etait signalee comme non initialisee. La regle parcourt maintenant
  **tous** les appels. Ces trois defauts ont ete trouves en faisant tourner
  l'outil sur 17 vrais gestionnaires de ressources ; la mesure est dans
  [`docs/BENCHMARK.fr.md`](BENCHMARK.fr.md) §6.
* **Limite connue :** la regle reconnait les trois initialisations qu'elle
  connait — `iofunc_func_init()`, un initialiseur de structure C99 et un
  `memset` a zero. Une table initialisee par **copie d'une autre table**
  (`io_funcs = model;`) n'est pas reconnue et est avertee, alors que ses
  pointeurs sont parfaitement definis.

---

## Ce qui a ete corrige dans cette version, et comment c'est prouve

Sept regles avaient un defaut connu qui contredisait la documentation
officielle (QX001, QX002, QX003, QX004, QX006, QX007, QX011). Chacune est
maintenant couverte par un test qui **echoue sur le code precedent** et
**passe sur le code actuel** :

| Regle | Defaut corrige | Test qui le prouve |
|---|---|---|
| QX001 | l'exemple officiel de la documentation etait signale ; les initialiseurs de structure C99 etaient invisibles | `test_qx001_exemple_officiel_de_la_documentation`, `test_qx001_initialiseur_de_structure_c99`, `test_qx001_table_nulle_a_l_attach` |
| QX002 | « slots cables » etait compare a « entrees remplies » ; le vrai debordement n'etait jamais detecte | `test_qx002_slots_cables_au_dela_des_entrees_remplies`, `test_qx002_debordement_du_tableau` |
| QX003 | un handler defini dans une autre unite de compilation etait condamne | `test_qx003_handler_dans_une_autre_unite_de_compilation`, `test_qx003_handler_non_defini` |
| QX004 | une verification deleguee etait ratee ; une porte citee dans une chaine comptait | `test_qx004_porte_deleguee_a_un_helper`, `test_qx004_porte_citee_dans_une_chaine` |
| QX006 | une boucle deleguee a un pool de threads (`pool_attr.block_func = &resmgr_block`) n'etait pas reconnue ; un gestionnaire reparti sur plusieurs fichiers etait condamne en ERROR | `test_api_resmgr_block_et_resmgr_handler` (le cas delegue est verifie dans le meme test), `test_qx006_boucle_de_messages_absente` |
| QX007 | la meme limite que QX006 : le handler peut vivre dans une autre unite de compilation | `test_api_resmgr_block_et_resmgr_handler`, `test_qx007_dispatch_absent` |
| QX011 | une table statique (mise a zero) etait avertee a tort ; une table membre d'une structure etait dite « automatique » ; seul le premier appel a `iofunc_func_init()` etait lu | `test_qx011_table_mise_a_zero_statique` (il couvre aussi le cas membre et le deuxieme appel), `test_qx011_table_automatique_non_initialisee` |

Les trois dernieres lignes viennent du **benchmark sur du vrai code** — 17
gestionnaires de ressources ecrits par d'autres personnes, dont sept
publies par QNX ou BlackBerry eux-memes. Le corpus, la mesure et la verification manuelle de
chaque constat sont dans [`docs/BENCHMARK.fr.md`](BENCHMARK.fr.md).

Rejouez la preuve (machine hote seule, aucun SDK QNX n'est necessaire) :

```console
$ bash scripts/run_tests.sh
```

La suite est le contrat a deux sens : les cas valides ne doivent produire
**aucun** constat actionnable, et les cas sabotes doivent produire le constat
attendu. Une regle qu'on a simplement supprimee ne prouve rien.

Chacune des onze regles est citee par au moins un test — une regle qu'aucun
test ne cite est une regle qui n'existe pas. Deux regles (QX008, le slot non
cable signale en INFO, et QX010, la macro signalee en INFO) n'avaient aucun
test propre jusqu'a cette version ; elles en ont un maintenant.

Le principe directeur reste le meme : **une regle qui ne peut pas etre corrigee
avec une source officielle doit etre supprimee** — une regle sans source est
pire qu'une regle absente.

---

## Le reglement du concours, cite — video v2 (06/11/2026)

Les six exigences qui suivent sont citees **mot pour mot** depuis la page des
regles du QNX Global Hackathon, consultee le **06/11/2026** (HTTP 200,
160 476 octets pour la copie enregistree — la page vivante varie de quelques
centaines d'octets selon les jetons de session et l'habillage de la page, le
texte des regles non) : <https://qnx.devpost.com/rules>. Pour chacune, la video v2
et la maniere dont elle y repond.

*Relu le 07/11/2026 :* la page repond HTTP 200 et son **texte** est
**identique** a la copie du 06/11/2026 — 39 540 caracteres de texte dans les
deux copies, mesures par le meme script (balises HTML retirees, lignes vides
supprimees, lignes restantes jointes par des retours a la ligne). La seule
difference dans ce texte est le compteur de participants, qui est vivant : 601
sur la copie du 06/11, 657 puis 658 pendant la relecture du 07/11 ; remplace
par un joker, les deux textes sont strictement egaux. Les six citations
ci-dessous ont ete verifiees caractere par caractere sur la copie du
07/11/2026 : les six sont toujours exactes.

*Relu encore le 12/11/2026 :* la page repond HTTP 200 et le **texte des
regles est toujours identique** a la copie du 06/11/2026. Le corps des regles
— de la ligne de titre a la fin de la page — donne les memes **37 665
caracteres** dans les quatre copies enregistrees les 06/11, 07/11, 11/11 et
12/11, mesures par la meme methode que ci-dessus (balises HTML retirees,
lignes vides supprimees, lignes restantes jointes par des retours a la ligne ;
les 39 540 caracteres du paragraphe precedent comptent toute la page, navigation
comprise). Le compteur de participants, qui est vivant et se trouve au-dessus
de ce texte, est passe de 601 le 06/11 a 1 192 le 11/11 et 1 310 le 12/11. Les
six citations ci-dessous ont ete reverifiees caractere par caractere sur la
copie du 12/11/2026 : les six sont toujours exactes.

**1. Duree** — « should be less than three (3) minutes ».

*Comment la video le satisfait :* elle dure **71,44 s** (mesuree avec
`ffprobe` sur le fichier du depot), donc bien en dessous des trois minutes,
et au-dela de la minute demandee en interne. Une seule scene occupe 3,12 s
au minimum, chaque sous-titre reste affiche au moins 2,5 s.

**2. L'appareil** — « should include footage that shows the Project functioning
on the device for which it was built ».

*Comment la video le satisfait :* QX-PROBE est un **outil hote** : il lit du
code source C, il ne s'execute pas sur une carte QNX et n'a pas besoin d'en
avoir une. « the device for which it was built » est donc **la machine hote**
qui fait tourner l'outil — ce que le reglement confirme dans la definition
de la categorie retenue : « a host-based tool (Windows, macOS, or Linux) that
builds, tests, analyzes, or otherwise supports software targeting QNX 8.0 ».
La video montre **le vrai outil** qui s'execute sur **les vrais fichiers
publics du depot** — le gestionnaire de ressources publie par BlackBerry, un
exemple en lecture seule, une fixture volontairement abimee — avec la sortie
reelle et le code de retour reel a l'ecran. Ce n'est ni une maquette, ni une
sortie simulee, ni une capture de documentation.

*Si le jury lit cette exigence comme « la carte QNX » :* cette lecture est
defendable, et les deux options qu'elle impose ont un cout. (a) Executer les
exemples C sur la cible demande le kit **QNX SDP 8.0** sous licence
non commerciale **QNX Everywhere** (compte myQNX) — gratuit en argent, mais
il faut s'inscrire et attendre ; (b) les faire tourner dans un guest **QEMU**
demande le meme kit (image QNX 8.0 et `mkqnximage` viennent du SDP). Les
deux options passent donc par la meme licence, que nous n'avons pas. C'est
pourquoi la video montre l'outil de l'hote, et pourquoi le paquet ecrit
`NOT MEASURED` la ou la compilation n'a pas ete mesuree, plutot que de
montrer une sortie simulee.

**3. YouTube** — « must be uploaded to and made publicly visible on YouTube and
a link to the video must be provided on the submission form on the Hackathon
Website ».

*Comment la video le satisfait :* la video est en **anglais** (le reglement
exige l'anglais pour tous les materiaux) et **sans aucune piste audio** —
donc aucune musique, aucune voix off. Le fichier binaire est deja dans le
depot public. Ce qui reste est **une seule action du proprietaire** : le
televerser sur YouTube en video publique, puis coller l'URL dans le champ
video du formulaire. Aucun compte n'a ete cree et aucune video n'a ete
publiee par l'automatisation.

**4. Marques et droits** — « must not include third party trademarks, or
copyrighted music or other material unless the Entrant has permission to use
such material ».

*Comment la video le satisfait :* la video ne contient **aucune piste
audio**, donc aucune musique sous copyright. Le seul code tiers montre est
`examples/blackberry_eventfd_mgr.c`, de BlackBerry Limited, redistribue
**sans modification** sous **Apache-2.0** avec son en-tete de licence intact :
cette licence **est** l'autorisation d'utiliser le materiel, et le fichier
`NOTICE` porte l'attribution. Les phrases de la documentation QNX 8.0 citees
a l'ecran le sont avec la page officielle qui les porte.

**5. Fonctionnement reel** — « must function as depicted in the video ».

*Comment la video le satisfait :* chaque commande de la video est une
commande du depot public, tapee telle quelle, et chaque sortie affichee a
ete produite a l'enregistrement. Le juge peut les rejouer et obtenir les
memes resultats : 27 tests au vert, exit code 0 sur le code correct, exit
code 1 sur la fixture abimee.

**6. Instructions de construction et d'execution** — « Include build and run
instructions specifying the QNX version, the target (hardware or QEMU), and the
toolchain used ».

*Comment la video le satisfait :* l'outil soumis est un outil hote : il n'y a
**rien a construire ni a executer sur une cible**, il ne demande ni le SDK QNX
ni une carte. La version QNX analysee est **8.0** et l'outillage est la
**bibliotheque standard de Python 3**. Les memes trois elements sont ecrits
dans les blocs `BUILD` et `TESTING` de `docs/SUBMISSION-EN.md`, avec le
chemin de construction `qcc` des exemples C, explicitement marque
`NOT MEASURED`.
