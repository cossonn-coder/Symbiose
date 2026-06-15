#!/usr/bin/env python3
"""compte_ldc — compteur de Lignes De Code pur.

Outil *du dépôt* (pas du moteur) : il sert d'instrument de mesure au
Sprint refactor global. La règle de Nico est « ~500 lignes de CODE PUR par
fichier », où *code pur* exclut explicitement :
  - les lignes vides,
  - les lignes de commentaire,
  - les docstrings / lignes dont le seul contenu est une chaîne littérale.

Les commentaires pédagogiques sont au cœur du projet : ils ne doivent JAMAIS
être sacrifiés pour gagner des lignes. Cet outil les compte donc à part, dans
une colonne « comment. », pour qu'on voie d'un coup d'œil qu'un gros fichier
l'est *par sa pédagogie* et non par sa logique.

Usage :
    python3 tools/compte_ldc.py <fichier…>
    python3 tools/compte_ldc.py data/code/sim/*.py
    python3 tools/compte_ldc.py --seuil 500 data/code/**/*.py

Sortie : un tableau « fichier | total | code | comment. », trié par *code*
décroissant, avec un repère ⚠ sur les fichiers qui dépassent le seuil.
"""

import sys
import io
import tokenize


# ─────────────────────────────────────────────────────────────────────────
# Comptage Python — via le module standard `tokenize`
# ─────────────────────────────────────────────────────────────────────────
#
# `tokenize` lit un fichier Python et le découpe en *jetons* (tokens) :
# chaque mot-clé, nom, opérateur, nombre, chaîne, commentaire… arrive avec
# sa position (ligne, colonne) de début et de fin. C'est l'analyseur lexical
# officiel de Python — bien plus fiable qu'une regex, parce qu'il comprend
# vraiment la grammaire (chaînes multi-lignes, f-strings, etc.).
#
# Notre stratégie : une *ligne physique* compte comme « code » dès qu'elle
# porte au moins un jeton « significatif ». Sont jugés NON significatifs :
#   - les commentaires (token COMMENT),
#   - les chaînes seules (token STRING / FSTRING_* → docstrings et littéraux
#     isolés ; si la chaîne fait partie d'une expression, c'est le NOM ou
#     l'opérateur voisin — `x =`, `return …` — qui rend la ligne « code »),
#   - la plomberie de structure (NEWLINE, NL, INDENT, DEDENT, ENCODING…).
#
# Conséquence voulue : une docstring multi-ligne ne compte aucune ligne de
# code ; `x = "abc"` en compte une (grâce au `x =`).

# Jetons qui, à eux seuls, ne « font » pas une ligne de code.
_NON_CODE = {
    tokenize.COMMENT,
    tokenize.STRING,
    tokenize.NL,        # saut de ligne non logique (lignes vides, continuations)
    tokenize.NEWLINE,   # fin d'instruction logique
    tokenize.INDENT,
    tokenize.DEDENT,
    tokenize.ENCODING,
    tokenize.ENDMARKER,
}

# Les f-strings (Python 3.12+) se décomposent en plusieurs jetons dédiés.
# On les traite comme des chaînes : non significatifs en eux-mêmes.
for _nom in ("FSTRING_START", "FSTRING_MIDDLE", "FSTRING_END"):
    _val = getattr(tokenize, _nom, None)
    if _val is not None:
        _NON_CODE.add(_val)


def compte_python(chemin):
    """Retourne (total, code, comment) pour un fichier Python.

    total   = lignes physiques du fichier
    code    = lignes portant au moins un jeton significatif
    comment = lignes non vides qui ne sont pas du code (commentaires +
              docstrings) — déduit par soustraction pour que la somme
              code + comment + vides recolle toujours au total.
    """
    with open(chemin, "rb") as f:
        source = f.read()

    total = _compte_lignes_physiques(source)

    lignes_code = set()
    # tokenize.tokenize veut une fonction `readline` sur des octets.
    jetons = tokenize.tokenize(io.BytesIO(source).readline)
    for tok in jetons:
        if tok.type in _NON_CODE:
            continue
        # Un jeton significatif « allume » toutes les lignes qu'il couvre
        # (utile pour une expression qui s'étale sur plusieurs lignes).
        for ligne in range(tok.start[0], tok.end[0] + 1):
            lignes_code.add(ligne)

    code = len(lignes_code)
    vides = _compte_lignes_vides(source)
    comment = total - code - vides
    return total, code, max(comment, 0)


def _compte_lignes_physiques(source_octets):
    """Nombre de lignes physiques, en tolérant l'absence de \\n final."""
    texte = source_octets.decode("utf-8", errors="replace")
    if texte == "":
        return 0
    n = texte.count("\n")
    # Dernière ligne sans saut de ligne final → +1.
    if not texte.endswith("\n"):
        n += 1
    return n


def _compte_lignes_vides(source_octets):
    texte = source_octets.decode("utf-8", errors="replace")
    return sum(1 for ligne in texte.splitlines() if ligne.strip() == "")


# ─────────────────────────────────────────────────────────────────────────
# Comptage générique (C#, GDScript, …) — repli ligne à ligne
# ─────────────────────────────────────────────────────────────────────────
#
# Pas d'analyseur lexical universel sous la main : on lit ligne à ligne en
# suivant un seul état, « suis-je dans un bloc /* … */ ». C'est volontairement
# simple. Limite connue et assumée : un commentaire en fin de ligne de code
# (`int x = 1; // note`) laisse la ligne classée « code ». Pour notre usage
# (jauger la taille des fichiers), l'approximation est sans conséquence.

def compte_generique(chemin):
    """Retourne (total, code, comment) pour un fichier non-Python."""
    with open(chemin, "r", encoding="utf-8", errors="replace") as f:
        lignes = f.read().splitlines()

    total = len(lignes)
    code = 0
    comment = 0
    dans_bloc = False  # sommes-nous à l'intérieur d'un /* … */ ?

    for brute in lignes:
        ligne = brute.strip()

        if dans_bloc:
            comment += 1
            if "*/" in ligne:
                dans_bloc = False
            continue

        if ligne == "":
            continue  # ligne vide : ni code ni commentaire
        if ligne.startswith("//"):
            comment += 1
            continue
        if ligne.startswith("/*"):
            comment += 1
            # Le bloc peut se refermer sur la même ligne.
            if "*/" not in ligne[2:]:
                dans_bloc = True
            continue

        code += 1

    return total, code, comment


# ─────────────────────────────────────────────────────────────────────────
# Pilotage / affichage
# ─────────────────────────────────────────────────────────────────────────

def compte(chemin):
    """Aiguille vers le bon compteur selon l'extension."""
    if chemin.endswith(".py"):
        return compte_python(chemin)
    return compte_generique(chemin)


def main(argv):
    args = list(argv)
    seuil = 500
    if "--seuil" in args:
        i = args.index("--seuil")
        seuil = int(args[i + 1])
        del args[i:i + 2]

    if not args:
        print(__doc__)
        return 1

    resultats = []
    for chemin in args:
        try:
            total, code, comment = compte(chemin)
        except (OSError, SyntaxError, tokenize.TokenError) as exc:
            print(f"  (ignoré) {chemin} : {exc}", file=sys.stderr)
            continue
        resultats.append((chemin, total, code, comment))

    # Tri sur le code pur décroissant : les plus gros fichiers en tête.
    resultats.sort(key=lambda r: r[2], reverse=True)

    largeur = max((len(r[0]) for r in resultats), default=8)
    print(f"{'fichier':<{largeur}}  {'total':>6}  {'code':>6}  {'comment.':>8}")
    print("─" * (largeur + 26))
    for chemin, total, code, comment in resultats:
        repere = "  ⚠" if code > seuil else ""
        print(f"{chemin:<{largeur}}  {total:>6}  {code:>6}  {comment:>8}{repere}")

    depassements = [r for r in resultats if r[2] > seuil]
    if depassements:
        print(f"\n{len(depassements)} fichier(s) > {seuil} lignes de code pur.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
