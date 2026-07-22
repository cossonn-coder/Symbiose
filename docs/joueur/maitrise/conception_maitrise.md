# Conception — Paliers de maîtrise (SYMBIOSE) · index

> **Document de conception. Aucun code écrit.** Spec de référence pour le futur
> sprint d'implémentation des paliers de maîtrise.
>
> Issu du **Sprint conception paliers de maîtrise** (2026-06-04). Couvre la
> dette **D12**. Remplit l'interface laissée stubbée par le Sprint Vigueur
> (`sim/vigueur.py:palier_bonus() == 1.0`, cf. `docs/joueur/vigueur/conception_vigueur.md` §2.3/§7).
>
> **Périmètre : le squelette réutilisable seulement** (décision Nico). Ce doc
> conçoit le *modèle* de maîtrise (objet atomique → progression → agrégats →
> ponts). Il **ne câble pas** chaque action ni n'énumère le catalogue d'objets :
> la définition fine du « succès » par axe, la table palier→déblocage et la
> taxonomie des objets sont déclarées comme **sous-sprints suivants** (§8).

> **Scindé au Sprint refactor global (SS①, 2026-06-15)** pour passer sous le
> seuil de taille. Le contenu intégral est réparti en trois parties dans
> [``](), reliées entre elles. Aucune ligne perdue.

## Plan

| Partie | Contenu | Fichier |
|---|---|---|
| §0-8 | **Le modèle** — objet atomique, progression, agrégats, ponts, méta-état, interfaces, sous-sprints | [`01_modele.md`](01_modele.md) |
| §9 | **Le succès** — définition par axe, lecture moteur, transcendance (D12.1) | [`02_succes_par_axe.md`](02_succes_par_axe.md) |
| §10 | **La taxonomie** — catalogue d'objets, table `cout_action` (D12.3) | [`03_taxonomie_objets.md`](03_taxonomie_objets.md) |
