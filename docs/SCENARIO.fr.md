# Scenario de la demonstration video QX-PROBE

**Statut :** video **v0 FILMEE** (`qx-demo-v0.mp4`, 543 516 octets, md5
`381f7aa6af21ae209e3bbccb1d4bfac0`, 35,92 s, 1920x1080, H.264, 25 fps,
898 images, **sans piste audio**).

Le plan 5 (« la cible QNX 8.0 ») en est **absent** : il depend du SDK QNX 8.0
(licence QNX Everywhere non commerciale, compte myQNX) qui n'existe pas encore.
Conformement a la regle de tournage, ce plan a ete **supprime** de la video, pas
remplace par une capture d'ecran, et aucune sortie de compilateur n'a ete
simulee.

La video v0 couvre donc les plans **1 (partiellement), 2, 4 et 6**.  Les plans
**3** (le faux positif assume) et **5** (la cible QNX 8.0) n'y sont pas.

Format : MP4 H.264, 1920x1080, 25 fps, 35,92 s, sans voix off (le texte a
l'ecran doit suffire).

---

## Plan, plan par plan

### 1. Le probleme (8 s)

* Terminal, invite vide.
* Texte a l'ecran : `Un driver QNX 8.0 se trompe de trois facons tres vite.`
* Puis, une par une, les trois fautes avec leur consequence :
  * `read()` sans `iofunc_read_verify()` -> le client lit ce qu'il ne doit pas.
  * boucle de messages qui bloque sans distribuer -> le client pend.
  * reply qui renvoie plus de parties que l'IOV n'en a -> reponse corrompue.
* Texte final : `Les trois se voient dans le code. Il faut un outil.`

### 2. L'outil (10 s)

* Terminal : `python3 -I qx_probe.py examples/blackberry_eventfd_mgr.c`
* Le code de reference **public de BlackBerry** passe : `0 ERROR, 0 WARN`.
* Texte a l'ecran : `Le code de reference de l'editeur de QNX 8.0 passe sans erreur ni avertissement.`

### 3. Le faux positif, assume (12 s) — le moment le plus important

* Terminal : `python3 -I qx_probe.py examples/qnx80_resmgr_readonly.c`
* Resultat : `0 ERROR, 0 WARN`.
* Texte a l'ecran :
  `Point de montage hors /dev/ et gestionnaire en lecture seule : c'est valide en QNX 8.0.`
  `Une version anterieure de cet outil signalait ces deux cas. Faux positif.`
* Puis la source de la regle, affichee en clair :
  `resmgr_attach() : "puts the path into the general pathname space"`

### 4. La detection (12 s)

* Terminal : `bash scripts/run_tests.sh` (la suite complete).
* Puis une demonstration ciblee : le fichier `examples/qnx80_resmgr_relative_path.c`
  produit exactement un `WARN QX005`, avec la ligne du fichier.
* Texte a l'ecran : `La regle qui mord : un chemin relatif, depend du repertoire courant.`

### 5. La cible QNX 8.0 (25 s) — necessite le SDK

* Terminal : `bash scripts/build_qcc.sh`
  * sortie reelle de `qcc`, sans retouche ;
  * le binaire produit est lance sous QEMU si disponible, sinon la sortie de
    compilation suffit (le rationale du concours est « build, test, analyze »,
    pas « run »).
* Terminal : `cat /proc/mount` (ou la liste des points de montage) — le
  resource manager monte sur `/dev/qxprobe-demo` apparait.
* Un `cat /dev/qxprobe-demo` depuis le shell QNX affiche le caractere renvoye
  par le handler de lecture : la demonstration est **reelle**, pas une capture
  d'ecran de la documentation.

### 6. Le lien avec le concours (8 s)

* Texte a l'ecran :
  `Zero dependance. Zero materiel. Un outil qui tourne dans votre CI.`
  `Licence Apache-2.0. Chaque regle cite sa page de la documentation QNX 8.0.`

---

## Ce que montre exactement la video v0 (mesure, plan par plan)

1. Titre a l'ecran : `QX — QNX 8.0 resource-manager protocol checker`.
2. `QX-PROBE analyse le code source d'un resource-manager QNX et signale
   (l'erreur)` — l'outil est presente en une phrase.
3. `$ head -12 research/shim-demo/eventfd-mgr.c` — extrait du resource manager
   public de BlackBerry (Apache-2.0).
4. « Le probe passe au vert sur un code correct » :
   `python3 -I probe/qx_probe.py research/shim-demo/eventfd-mgr.c`
   → **5 constats, 0 ERROR, 0 WARN, code de sortie 0**.
5. « Le meme code, avec une seule porte d'acces retiree » :
   `python3 -I probe/qx_probe.py proofs/contre-epreuve/eventfd-mgr-qx004.c`
   → **6 constats, 1 ERROR (QX004), 0 WARN, code de sortie 1**.
6. « Le probe est utilisable comme porte de CI : code de sortie different de 0 » :
   `... > /dev/null; echo "code de sortie = $?"` → `code de sortie = 1`.
7. « Zero dependance, zero SDK QNX, executable partout » :
   `python3 -c "import importlib.util as u; print(...)"` →
   `dependances externes : ['pycparser']`.
8. « Fin de la demonstration ».

Les chiffres 4 et 5 ont ete **rejoues** avec la version courante de la sonde :
ils sont identiques.

### Deux reserves honnetes sur la video v0

* **Le plan 7 (dependances) est trompeur tel quel.**  La commande affichee liste
  les modules **presents sur la machine de tournage**, pas ceux qu'utilise
  QX-PROBE.  `qx_probe.py` n'importe que la bibliotheque standard Python
  (`re`, `sys`, `dataclasses`) ; `pycparser` etait installe sur cette machine
  et n'est **pas** utilise par l'outil.  La video v1 doit afficher les imports
  reels.
* **Les commandes filmees montrent des chemins internes** (`research/…`,
  `proofs/…`) qui n'existent pas dans ce depot public.  Les equivalents publics
  sont : `python3 -I qx_probe.py examples/blackberry_eventfd_mgr.c` (fichier
  sain : 5 constats, 0 ERROR, 0 WARN, code de sortie 0) et
  `bash scripts/run_tests.sh` (la suite complete, 11 tests, dont le cas de
  detection `examples/qnx80_resmgr_relative_path.c` : exactement un WARN QX005,
  code de sortie 1).
* La video est **en francais** ; le reglement du concours exige que tout
  materiau soit en anglais, ou qu'une traduction anglaise soit fournie.  La
  traduction anglaise plan par plan de la video v0 est fournie avec le texte de
  soumission.

---

## Regles de tournage

* **Aucune sortie inventee.** Tout ce qui est filme a ete execute. Si le SDK
  manque, le plan 5 est **supprime** de la video, pas remplace par une capture
  d'ecran.
* Chaque plan montre le **code** qui produit le resultat (le fichier est ouvert
  a cote du terminal quand un resultat doit etre cru).
* Les citations de la documentation QNX 8.0 sont affichees avec leur URL, pour
  que le jury puisse les verifier.
* Aucun chemin interne, aucun identifiant de compte, aucune donnee personnelle
  dans les plans.

## Ce qu'il reste a faire (video v1, avec le SDK)

La video **v0** est filmee (voir plus haut).  Ce qui reste :

1. Disposer du SDP 8.0 (host tools Linux x86_64) et d'une licence QNX Everywhere
   non commerciale.
2. Verifier la cible : `qcc -Vgcc_ntoaosdebug` doit compiler les deux exemples.
3. Rejouer `bash scripts/run_tests.sh` et `bash scripts/build_qcc.sh` a jour.
4. Filmer la **v1** : les plans 3 et 5 (le faux positif assume, la cible
   QNX 8.0), une version en anglais ou sous-titree, et un plan « zero
   dependance » qui affiche les imports reels de `qx_probe.py` au lieu des
   modules presents sur la machine de tournage.
5. Televerser sur YouTube en **acces public** (exigence du reglement) et
   fournir l'URL.
