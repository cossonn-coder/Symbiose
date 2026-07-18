// SYMBIOSE — PlantRenderer.Organs.cs
// Organes procéduraux (feuilles / fleurs / fruits) — partial de PlantRenderer.
// Portage de tools/render_structure.py §« ORGANES PROCÉDURAUX » (_draw_organs,
// validé visuellement en SVG). Extrait de PlantRenderer.cs au refactor SS⑦.
//
// Constantes et palette IDENTIQUES au prototype ; seul le hash diffère (local
// C#, pas de parité bit-à-bit requise : c'est de la décoration de vue, il faut
// juste la STABILITÉ inter-frames et inter-sessions).

using Godot;
using System.Collections.Generic;

namespace Symbiose
{
	public partial class PlantRenderer : Node2D
	{
		// VERROU « feuille ⟹ segment rendu vert » (④, doc §5.2). Ce seuil DOIT rester
		// ≤ au point de bascule vert→olive de la rampe de lignification (Palette.cs) :
		// `WoodRamp` quitte le vert-tendre quand `Lignification = ThicknessCm /
		// LignifyFullCm` atteint 0.5, soit ThicknessCm = LignifyFullCm * 0.5 = 1.5 cm.
		// Au-delà de 1.5 cm un segment commence à virer olive — il ne serait PLUS vert.
		// On cale donc LeafMaxThickCm = 1.5 (et non l'ancien 1.6, qui laissait la bande
		// [1.5, 1.6] feuillue alors qu'elle commençait à olivir : violation discrète de
		// l'invariant E5). Apex toujours vert pur (Lignification=0). Si LignifyFullCm
		// bouge un jour, ré-aligner ce seuil sur LignifyFullCm * 0.5.
		private const float LeafMaxThickCm = 1.5f; // au-delà = bois structurel, nu
		private const float LeafSpacingCm = 11f;   // une feuille tous les ~11 cm
		private const float LeafOffsetCm = 7f;     // déport latéral p/r à l'axe
		private const float LeafSizeCm = 7f;       // demi-grandeur d'une feuille
		// ⑤ CROISSANCE PROGRESSIVE (doc §4, E1) : une feuille naît petite et grandit
		// sur ~1,5 semaine. On dérive la taille de l'ÂGE RÉEL du segment porteur
		// (`AgeWeeks`, proxy déjà calculé par la morphogénèse, exposé au pont 0.5.5) —
		// pas d'un timer de vue (déterminisme, philo #3 : même âge → même feuille).
		private const float LeafMaturityWeeks = 1.5f; // âge où la feuille atteint sa taille pleine
		private const int MaxFruits = 10;          // plafond anti-fouillis (proxy fleurs)
		private const float MaturiteChute = 1.3f;  // miroir MATURITE_CHUTE moteur : sur-mûr → chute
		// Brun fermenté d'un fruit sur-mûr (④) — vers quoi tire la couleur au-delà du mûr.
		private static readonly Color FruitRotten = new Color("6b4a2f");
		// Sémiologie ③ — canaux TEXTURE sur les feuilles (cf. PlantRenderer.cs).
		private const float DroughtDroopCm = 6f;   // affaissement max d'une feuille flétrie
		private static readonly Color LeafHoleColor = new Color(0.10f, 0.09f, 0.05f, 0.55f); // morsure sombre
		private static readonly Color GelEdgeColor = new Color("2a1d14"); // brun-noir brûlé (gel)
		private static readonly Color LeafSpotColor = Palette16.PustuleMaladie; // pustule cryptogamique brun foncé

		// --- Vrilles / indice d'accroche (grimpantes ⑥) --------------------------
		private string _supportKind;    // null = libre ; sinon type d'appui accroché
		private static readonly Color TendrilColor = new Color("6fb24a"); // vert vrille

		// Reçoit l'état `support` du snapshot (0.5.18) : le TYPE d'appui accroché
		// (tuteur/treillis/pergola/mur/hote), ou null si la plante est libre (non
		// accrochée / non-grimpante). Ne pilote qu'un DÉTAIL de vue (la vrille) ; la
		// grimpe elle-même vient de la géométrie des segments (décision A). Early-out
		// si inchangé (comme SetSkeleton) : pas de redraw inutile.
		public void SetSupport(string kind)
		{
			if (_supportKind == kind) return;
			_supportKind = kind;
			QueueRedraw();
		}

		// Une petite VRILLE en spirale au sommet de la grimpante accrochée : l'organe
		// d'accroche qui « tient » le support. Déterministe (spirale paramétrique,
		// zéro RNG → même tête, même vrille). Posée au tip le PLUS HAUT de la structure
		// (la tête de la grimpe, là où elle saisit). Discrète : ~2 tours, ≈ 6 px.
		private void DrawTendrils(Vector3 collet)
		{
			if (string.IsNullOrEmpty(_supportKind) || _structure == null) return;
			Vector3 top = collet; float maxZ = float.NegativeInfinity;
			foreach (var s in _structure.Segments)
			{
				Vector3 tip = s.Base + s.Dir * s.LengthCm;
				if (tip.Z > maxZ) { maxZ = tip.Z; top = tip; }
			}
			Vector2 head = Iso(top.X - collet.X, top.Y - collet.Y, top.Z);
			const int N = 14;
			Vector2 prev = head;
			for (int i = 1; i <= N; i++)
			{
				float t = i / (float)N;
				float a = t * Mathf.Tau * 2f;                 // 2 tours d'enroulement
				float rad = 1.5f + 4f * t;                    // rayon croissant
				Vector2 p = head + new Vector2(Mathf.Cos(a) * rad, Mathf.Sin(a) * rad)
							- new Vector2(0f, t * 6f);        // léger tirage vers le haut
				DrawLine(prev, p, TendrilColor, 1.2f);
				prev = p;
			}
		}

		// Palette par espèce (= ORGAN_PALETTE du prototype) : feuille, fleur,
		// fruit vert, fruit mûr. Espèce inconnue → défaut.
		private readonly struct OrganPalette
		{
			public readonly Color Leaf, Flower, FruitUnripe, FruitRipe;
			public OrganPalette(string leaf, string flower, string unripe, string ripe)
			{
				Leaf = new Color(leaf); Flower = new Color(flower);
				FruitUnripe = new Color(unripe); FruitRipe = new Color(ripe);
			}
		}
		// Teinte de base par espèce (E3-couleur, doc §3.1). La clé = nom de CLASSE
		// Python (= snapshot `species`, cf. serialize.py `cls.__name__`), comme les
		// deux entrées historiques. CONTENU pur : aucun mécanisme nouveau — la teinte
		// `Leaf` part dans `DrawVolumeEllipse`, qui érige déjà le volume 2 valeurs
		// (E4 garanti), et `LeafColor` lui applique la saison PAR-DESSUS. Une espèce
		// non mappée retombe sur `DefaultPalette` (jamais bloquant, on enrichit au fil).
		// Les 4 couleurs (limbe / fleur / fruit vert / fruit mûr) sont plausibles par
		// espèce ; fruit vert/mûr ne sert qu'aux espèces dont le moteur émet des fruits.
		private static readonly System.Collections.Generic.Dictionary<string, OrganPalette>
			Palettes = new()
			{
				// --- Cultivées potagères --------------------------------------------
				["Tomato"]    = new OrganPalette("3f9e3a", "e8d24a", "5fae3f", "d8392a"), // tomate : vert franc, fleur jaune, fruit rouge
				["Pepper"]    = new OrganPalette("357f33", "f0ead2", "63ad3c", "d4451f"), // poivron : vert sombre, fleur blanche, fruit rouge-orangé
				["Bean"]      = new OrganPalette("4aa845", "eef0e8", "6fb24a", "8aa83f"), // haricot : vert tendre clair, fleur blanchâtre, gousse verte
				["Clover"]    = new OrganPalette("4f9e4b", "d98fb0", "6fb255", "5fa848"), // trèfle : vert vif, fleur rose
				["Sunflower"] = new OrganPalette("3d7a36", "f2c12e", "63953f", "5a4326"), // tournesol : vert mat, capitule jaune d'or, graines brunes
				["Carrot"]    = new OrganPalette("4a9b54", "ecefe2", "6fb060", "c87a2e"), // carotte : vert frais bleuté, ombelle blanche
				["Zucchini"]  = new OrganPalette("3a8c41", "f2cf3a", "5aaa44", "2f7a34"), // courgette : vert profond, fleur jaune, fruit vert sombre
				["CornSalad"] = new OrganPalette("5aa84f", "eef2e6", "74b85e", "6fae50"), // mâche : vert clair en rosette
				["Garlic"]    = new OrganPalette("5a9e6a", "ece6f0", "78b07a", "7aa86a"), // ail : vert glauque, hampe pâle
				["Strawberry"] = new OrganPalette("3f9e4a", "eef0e8", "6fb04f", "d8342a"), // fraisier : vert franc, fleur blanche à cœur jaune, fruit rouge
				// --- Sauvages fleuries (sprint FLORAISON ③ : leur saison est devenue observable) --
				["SweetViolet"] = new OrganPalette("3f7a44", "7a54a8", "6f9a55", "5a4a80"), // violette : feuille cordée sombre, fleur violette (printemps précoce)
				["Mugwort"]    = new OrganPalette("7a8a6a", "b7b06a", "8a9a66", "7a7a4a"), // armoise : feuillage gris-vert argenté, capitules jaune-verdâtre ternes (automne)
				// --- Compagnes / mellifères / engrais verts -------------------------
				["Yarrow"]    = new OrganPalette("4f8a55", "f0efe6", "6fa564", "8a9a66"), // achillée : vert grisé, corymbe blanc
				["Phacelia"]  = new OrganPalette("4a8e58", "8f7fc4", "6aa860", "7a8a66"), // phacélie : vert moyen, fleur mauve-bleu
				["Borage"]    = new OrganPalette("4d8a52", "5f7fc8", "6fa55f", "7a9a60"), // bourrache : vert mat, fleur bleu vif
				["Comfrey"]   = new OrganPalette("3f7d3e", "c47fb0", "5f9a48", "6f9a52"), // consoude : vert sombre poilu, fleur pourpre-rosé
				["Mustard"]   = new OrganPalette("5aa040", "f0d83a", "72b248", "8aa840"), // moutarde : vert jaunissant, fleur jaune
				// --- Aromatiques persistantes (Lamiacées evergreen) -----------------
				["Thyme"]     = new OrganPalette("5a7a4a", "c79fc0", "6f9058", "7a8a55"), // thym : vert-de-gris terne, fleur lilas
				["Lavender"]  = new OrganPalette("6a8270", "8f7fc8", "7a9070", "8a8fa0"), // lavande : feuillage gris-vert, épi violet
				// --- Sous-arbrisseau acidophile -------------------------------------
				["Vaccinium"] = new OrganPalette("3a7a44", "ead8e0", "6f9a55", "30407a"), // myrtille : vert profond, baie bleu-nuit
				// --- Pérennes ligneuses (vergers) -----------------------------------
				["AppleTree"]  = new OrganPalette("3f8e3a", "f3e0e8", "82ae4f", "cc382e"), // pommier : vert mat, fleur rosée, pomme rouge
				["Fig"]        = new OrganPalette("3a7d3c", "e0e6d2", "6f9a48", "5a3a52"), // figuier : grand limbe vert sombre, figue pourpre
				["CherryTree"] = new OrganPalette("3f8a3e", "f2dde2", "7fae50", "a01f28"), // cerisier : vert franc, fleur rose pâle, cerise rouge profond
				["WalnutTree"] = new OrganPalette("4a8240", "dfe2cc", "7aa84f", "4a3a22"), // noyer : vert olive, brou brun
				["OakTree"]    = new OrganPalette("46823c", "d6cf9a", "78a64a", "7a5a2e"), // chêne : vert mat lobé, gland brun
			};
		private static readonly OrganPalette DefaultPalette =
			new OrganPalette("469a3f", "ead85a", "6fae45", "cf3a2e");
		private static readonly Color[] AutumnLeaves =
		{
			new Color("c9a23a"), new Color("c4762a"), new Color("a8392a"),
			new Color("b8902f"), new Color("9c5a22"),
		};
		private static readonly Color FlowerHeart = new Color("e8c63a");
		// Seuil du scalaire moteur `floraison` (désync ②→③) au-delà duquel la plante
		// est jugée FLEURIE côté vue. Remplace le proxy season-gated `Organ=="flower"`
		// (qui faisait fleurir tout le jardin au passage de saison) : chaque pied
		// franchit ce seuil à SA semaine propre, dispersée par son gène `phenologie_florale`.
		// Seuil binaire volontairement sobre (kickoff §B « ne pas sur-concevoir ») :
		// il suffit à casser la synchronie, la silhouette de fleur reste par famille.
		private const float FloraisonSeuil = 0.5f;

		// Hash entier → [0,1) déterministe (mix multiplicatif xorshift). Remplace
		// le _hash_noise(SEED, canal, i, j) du prototype : mêmes ENTRÉES (canal,
		// index segment, index feuille) → même feuille au même endroit à chaque
		// frame ET à chaque session — zéro Random, philo #3.
		private static float Hash01(int channel, int i, int j)
		{
			uint h = (uint)channel * 0x9E3779B1u
				   ^ (uint)i * 0x85EBCA77u ^ (uint)j * 0xC2B2AE3Du;
			h ^= h >> 15; h *= 0x2C1B3C6Du;
			h ^= h >> 12; h *= 0x297A2D39u;
			h ^= h >> 15;
			return (h & 0xFFFFFF) / 16777216f;
		}

		// Couleur d'une feuille (= _leaf_color). DÉSYNC ③ : le décalage automnal n'est
		// PLUS piloté par la SAISON GLOBALE (`WorldView.CurrentSeason`, qui faisait
		// rougir tout le jardin d'un coup au passage de saison) mais par le scalaire
		// moteur `automne ∈ [0,1]` PAR-PLANTE (② `_structure.Automne`) — chaque caduc
		// se colore à SA semaine propre, dispersée par son gène tempo. On interpole
		// continûment la teinte d'été (`pal.Leaf`) vers une teinte automnale piochée
		// dans la palette chaude AU HASH par-feuille (variété inter-limbes conservée) :
		//  · automne = 0 → été plein (identité, comportement estival d'avant) ;
		//  · automne monte → rougissement PROGRESSIF et étalé entre individus ;
		//  · automne = 1 → pleinement automnal, juste avant que FoliageDensity ne
		//    fasse tomber la feuille (l'hiver caduc = densité 0, géré en amont, indep.).
		// Le printemps clair (×1.25) et l'hiver foncé (×0.7) sont abandonnés côté vue :
		// c'étaient des flips saisonniers globaux (la cause du bug) ; le persistant
		// garde simplement sa teinte d'été toute l'année (sobriété, kickoff §C).
		private static Color LeafColor(OrganPalette pal, float automne, float h)
		{
			if (automne <= 0f) return pal.Leaf;   // été (défaut/persistants)
			Color autumn = AutumnLeaves[(int)(h * AutumnLeaves.Length) % AutumnLeaves.Length];
			return pal.Leaf.Lerp(autumn, Mathf.Clamp(automne, 0f, 1f));
		}

		// Un segment porte des feuilles s'il est jeune/fin (rameau) ou un apex —
		// le bois épais (tronc/charpente) reste nu (= _is_leafy).
		private static bool IsLeafy(Segment s) =>
			s.IsApex || s.ThicknessCm <= LeafMaxThickCm;

		// ⑤ Facteur de croissance des feuilles d'un segment (doc §4.2) :
		// `leafGrowth = clamp(AgeWeeks / LeafMaturityWeeks, 0, 1)`, légèrement adouci
		// par une courbe ease-out (démarrage doux, fin qui se pose — §4.2 « optionnel »).
		// Proxy = âge du SEGMENT (déjà calculé), pas de chaque feuille. Établi → 1
		// (feuilles pleines, pas de pop-in au rechargement, §4.3).
		private static float LeafGrowthFactor(Segment s)
		{
			float t = Mathf.Clamp(s.AgeWeeks / LeafMaturityWeeks, 0f, 1f);
			return t * (2f - t);   // ease-out quadratique : 0→0, 1→1, pente douce en fin
		}

		// ---------------------------------------------------------------------------
		// ORGANES — feuilles / fleurs / fruits (t6·A, portage _draw_organs)
		// ---------------------------------------------------------------------------

		private void DrawOrgans(Vector3 collet)
		{
			// Teinte automnale PAR-PLANTE (désync ③) : plus de saison globale, on lit
			// le scalaire moteur `automne` du snapshot (② `_structure.Automne`).
			float automne = _structure.Automne;
			if (!Palettes.TryGetValue(_structure.SpeciesName, out var pal))
				pal = DefaultPalette;

			// --- FEUILLES — densité saisonnière calculée côté Python (caduc
			// hiver → 0, on ne dessine rien). densité < 1 → SOUS-ÉCHANTILLONNAGE
			// au hash (canal 17) : un feuillage léger (0.35) garde ~1 feuille
			// sur 3, toujours LES MÊMES (stabilité inter-frames).
			float density = _structure.FoliageDensity;
			if (density > 0f)
			{
				// Sémiologie `ombre` (T1, étiolement) — DÉCISION DE DESIGN (option a
				// du kickoff) : on RÉDUIT le facteur de calotte éclairée de
				// DrawVolumeEllipse pour les FEUILLES SEULEMENT, le temps de cette
				// boucle. La feuille étiolée a une calotte lumineuse plus petite
				// (limbe anémié). Plancher LitFactorFloor → jamais d'aplat (E4). Le
				// toggle est remis à LitFactorDefault après la boucle pour que les
				// fruits/fleurs (dessinés plus bas) gardent leur calotte normale —
				// `ombre` ne fuit PAS sur le chemin partagé.
				_litFactor = Mathf.Lerp(LitFactorDefault, LitFactorFloor, _ombre);
				// Repli palette T3 (§5) : sur le limbe SEULEMENT, on borne l'amplitude
				// du hue-shift FROID ∝ force du colorant dominant (`_colorAmount`). Un
				// symptôme jaune (chlorose/sénescence) ne reverdira/bleuira plus au
				// point de devenir illisible côté nord. Sain (`_colorAmount=0`) → 1
				// (SS² plein). Remis à 1 après la boucle (branches/fruits/fleurs intacts).
				_coolShiftScale = Mathf.Lerp(1f, ColorCoolShiftFloor, _colorAmount);
				for (int i = 0; i < _structure.Segments.Count; i++)
				{
					var s = _structure.Segments[i];
					if (!IsLeafy(s)) continue;
					// ⑤ Facteur de croissance des feuilles de CE segment (doc §4.2) :
					// rampe linéaire de l'âge du segment, écrêtée à 1. Un segment établi
					// (age ≥ maturité) → 1 = feuilles pleines d'emblée (pas de pop-in au
					// chargement, §4.3) ; seul un segment JEUNE montre la croissance.
					float leafGrowth = LeafGrowthFactor(s);
					int n = Mathf.Max(1, (int)(s.LengthCm / LeafSpacingCm));
					// Perpendiculaire HORIZONTALE à l'axe du rameau (plan sol) —
					// le déport latéral des feuilles, comme le prototype.
					float hmag = new Vector2(s.Dir.X, s.Dir.Y).Length();
					Vector2 perp = hmag > 1e-6f
						? new Vector2(-s.Dir.Y / hmag, s.Dir.X / hmag)
						: new Vector2(1f, 0f);
					for (int j = 0; j < n; j++)
					{
						if (Hash01(17, i, j) >= density) continue;
						float t = (j + 0.5f) / n;
						Vector3 p = s.Base + s.Dir * (s.LengthCm * t);
						float h1 = Hash01(7, i, j);
						float h2 = Hash01(11, i, j);
						float side = h1 < 0.5f ? 1f : -1f;
						float off = LeafOffsetCm * (0.5f + h2);
						float lx = p.X + perp.X * off * side;
						float ly = p.Y + perp.Y * off * side;
						float lz = p.Z + (h2 - 0.5f) * LeafOffsetCm;
						// Sécheresse (canal FORME) : turgescence perdue → la feuille
						// s'affaisse, on l'abaisse ∝ intensité (conception §3/§4).
						lz -= _drought * DroughtDroopCm;
						Vector2 c = Iso(lx - collet.X, ly - collet.Y, lz);
						Color col = SymptomTint(LeafColor(pal, automne, Hash01(13, i, j)));
						col.A = 0.92f;
						// ⑤ Le rayon du limbe est MULTIPLIÉ par leafGrowth : sous le
						// plancher (§1) à l'émergence (1 valeur nue, pas de nervure),
						// il franchit le plancher en grandissant → volume puis nervures.
						// La feuille se construit visuellement, gratuitement (DrawLeafShape).
						float r = LeafSizeCm * WorldView.PxPerCmX * leafGrowth;
						// ④ PÉTIOLE (doc §5.3) — court trait vert reliant le point
						// d'insertion sur l'axe (p) au limbe (c). Tracé AVANT le limbe :
						// le limbe se pose dessus, le pétiole n'affleure qu'à sa base
						// (l'émergence se lit, la feuille n'est pas « posée dans le vide »).
						// ⑤ Le limbe s'éloigne du rameau AVEC sa croissance : on déplace
						// son centre `c` depuis le point d'insertion vers sa position pleine
						// par leafGrowth (à l'émergence le limbe colle au rameau, il s'écarte
						// en grandissant). Le pétiole, tracé jusqu'à ce centre, s'allonge donc
						// de pair (cohérence pétiole↔limbe, doc §4.2).
						Vector2 insert = Iso(p.X - collet.X, p.Y - collet.Y, p.Z);
						c = insert.Lerp(c, leafGrowth);
						DrawPetiole(insert, c, s);
						// ② FORME PAR ESPÈCE : la silhouette (ellipse/lancéolée/cordée/
						// lobée/composée/aiguille) est choisie par espèce dans le
						// catalogue fermé `LeafProfiles` (PlantRenderer.Leaf.cs). Chaque
						// sous-élément reste un volume 2 valeurs (E4) ; plancher de rayon
						// et repli LOD gérés dans DrawLeafShape.
						DrawLeafShape(c, r * 1.15f, r * 0.65f, col, i, j);
						// Canaux TEXTURE additifs (sémiologie ③) : criblage ravageurs/
						// grêle + bords gelés, par-dessus la feuille, stables au hash.
						DrawLeafDamage(c, r, i, j);
					}
				}
			}
			// Fin de la fenêtre feuilles : on REMET la calotte par défaut pour que
			// fleurs/fruits (DrawVolumeCircle, plus bas) ne soient PAS étiolés.
			_litFactor = LitFactorDefault;
			// … et le froid PLEIN pour fruits/fleurs/silhouette (repli T3 limbe-only).
			_coolShiftScale = 1f;

			// --- FLEURS — VRAI état moteur (désync ③) : le scalaire `floraison`
			// par-plante (② `_structure.Floraison`) REMPLACE le proxy season-gated
			// `Organ == "flower"` (qui faisait fleurir tout le jardin d'un coup au
			// passage de saison). Au-delà de FloraisonSeuil la plante est fleurie, à
			// SA semaine propre dispersée par son gène tempo → floraisons étalées.
			// REPLI : un snapshot pré-② n'a pas la clé (`Floraison` = 0) → aucune fleur ;
			// le proxy `Organ` n'est plus consulté (② est le prérequis, un seul chemin).
			// La SILHOUETTE reste par FAMILLE (DrawFlowerShape, PlantRenderer.Flower.cs).
			if (_structure.Floraison >= FloraisonSeuil)
			{
				var sites = OrganSites();
				for (int k = 0; k < sites.Count; k++)
				{
					Vector3 site = sites[k];
					DrawFlowerShape(Iso(site.X - collet.X, site.Y - collet.Y, site.Z),
									pal, 71, k);
				}
			}

			// --- FRUITS — VRAI état moteur (plant.fruits, ③), plus le proxy : la
			// maturité (vert→mûr→brun) et la déplétion par `manger` deviennent
			// OBSERVABLES. Une espèce sans fruit moteur (herbacées) n'en montre
			// donc plus — c'est l'état réel, pas une décoration saisonnière.
			DrawFruits(collet, pal);
		}

		// (La corolle générique 5 pétales a migré vers PlantRenderer.Flower.cs
		// sous le nom DrawSimple — un des 6 archétypes de famille, T2.)

		// Fruits tracés : un disque par entrée de `_structure.Fruits`, ancré au
		// bout de son segment porteur, COULEUR ∝ maturité, TAILLE ∝ masse. Reflet
		// blanc haut-gauche comme le proxy d'avant — continuité visuelle.
		private void DrawFruits(Vector3 collet, OrganPalette pal)
		{
			foreach (var f in _structure.Fruits)
			{
				Vector3 p3 = FruitPoint(f);
				Vector2 c = Iso(p3.X - collet.X, p3.Y - collet.Y, p3.Z);
				// masse → rayon (FRUIT_MASSE=0.15 côté moteur → ~4.5 px ; borné).
				float rad = 3.0f + Mathf.Min(f.Masse, 0.3f) * 10f;
				// SS② : globe en 2 valeurs (croissant d'ombre froide côté nord +
				// face sud éclairée), PUIS le reflet spéculaire blanc d'avant.
				DrawVolumeCircle(c, rad, FruitColor(pal, f.Maturite));
				DrawCircle(c - new Vector2(rad * 0.3f, rad * 0.3f),
						   rad * 0.3f, new Color(1f, 1f, 1f, 0.45f));
			}
		}

		// Couleur d'un fruit selon sa maturité : interpolation vert→mûr sur [0,1],
		// puis mûr→brun fermenté de 1.0 au seuil de chute (1.3 = MATURITE_CHUTE).
		private static Color FruitColor(OrganPalette pal, float mat)
		{
			if (mat <= 1f)
				return pal.FruitUnripe.Lerp(pal.FruitRipe, Mathf.Clamp(mat, 0f, 1f));
			float t = Mathf.Clamp((mat - 1f) / (MaturiteChute - 1f), 0f, 1f);
			return pal.FruitRipe.Lerp(FruitRotten, t);
		}

		// Point 3D (cm tuile-local) où ancrer un fruit = bout de son segment
		// porteur. `SegmentId` est un repère BEST-EFFORT (les indices glissent
		// avec la croissance, cf. moteur) → on borne à un segment valide.
		private Vector3 FruitPoint(FruitData f)
		{
			var segs = _structure.Segments;
			if (segs.Count == 0) return _structure.ColletCm;
			var s = segs[Mathf.Clamp(f.SegmentId, 0, segs.Count - 1)];
			return s.Base + s.Dir * s.LengthCm;
		}

		/// <summary>Index (= ordre du snapshot = clé `manger` moteur) du fruit le
		/// plus proche de `canvasPos`, ou −1 si la plante n'a aucun fruit. MÊME
		/// projection que DrawFruits → on cible exactement ce qu'on voit.</summary>
		public int FindFruitNear(Vector2 canvasPos)
		{
			if (_structure == null || _structure.Fruits.Count == 0) return -1;
			Vector2 local = ToLocal(canvasPos);
			Vector3 collet = _structure.ColletCm;
			int best = -1;
			float bestD = float.MaxValue;
			for (int i = 0; i < _structure.Fruits.Count; i++)
			{
				Vector3 p3 = FruitPoint(_structure.Fruits[i]);
				Vector2 c = Iso(p3.X - collet.X, p3.Y - collet.Y, p3.Z);
				float d = local.DistanceSquaredTo(c);
				if (d < bestD) { bestD = d; best = i; }
			}
			return best;
		}

		// Points 3D (cm, tuile-local) où naissent fleurs/fruits (= _organ_sites) :
		// bouts d'apex (`terminal`) ou bouts des latéraux HORS meneur (`lateral`,
		// le meneur = apex le plus haut, exclu → fructification latérale).
		// Plafonné à MaxFruits par sous-échantillonnage régulier (anti-fouillis).
		private List<Vector3> OrganSites()
		{
			var apex = new List<Segment>();
			foreach (var s in _structure.Segments)
				if (s.IsApex) apex.Add(s);
			if (apex.Count == 0) return new List<Vector3>();
			if (_structure.OrganSite == "lateral" && apex.Count > 1)
			{
				int leader = 0;
				float zMax = float.MinValue;
				for (int i = 0; i < apex.Count; i++)
				{
					float z = apex[i].Base.Z + apex[i].Dir.Z * apex[i].LengthCm;
					if (z > zMax) { zMax = z; leader = i; }
				}
				apex.RemoveAt(leader);
			}
			var tips = new List<Vector3>(apex.Count);
			foreach (var s in apex)
				tips.Add(s.Base + s.Dir * s.LengthCm);
			if (tips.Count > MaxFruits)
			{
				float step = (float)tips.Count / MaxFruits;
				var sampled = new List<Vector3>(MaxFruits);
				for (int i = 0; i < MaxFruits; i++)
					sampled.Add(tips[(int)(i * step)]);
				return sampled;
			}
			return tips;
		}

		// ④ PÉTIOLE (doc §5.3) — court trait de 1-2 px reliant le point d'insertion
		// (`insert`, sur l'axe du rameau) au limbe (`leaf`). COULEUR = teinte verte du
		// RAMEAU LOCAL via la rampe au point d'insertion : `WoodRamp(Lignification(s))`.
		// JAMAIS brune par construction — l'invariant ④ garantit que tout segment
		// feuillu reste sous le point de bascule vert→olive (LeafMaxThickCm ≤
		// LignifyFullCm*0.5), donc cette teinte est vert-tendre→olive, pas brune.
		// ORIENTATION = celle déjà calculée (déport `LeafOffsetCm`, axe rameau →
		// extérieur) : c'est exactement le vecteur insert→leaf. C'est aussi le futur
		// POINT DE RUPTURE de l'abscission (⑥, doc §6.2) : la feuille tombée casse ici.
		//
		// Pleine taille en attendant ⑤ : le facteur de croissance `leafGrowth` (§4)
		// arrivera en ⑤ et allongera le pétiole AVEC la feuille. Le branchement est
		// prêt — il suffira d'interpoler `petTip` sur le segment insert→leaf par
		// `leafGrowth`. Ici on relie pleinement (rendu cohérent sans pré-implémenter ⑤).
		private void DrawPetiole(Vector2 insert, Vector2 leaf, Segment s)
		{
			Color green = WoodRamp(Lignification(s)); // vert local, jamais brun (invariant ④)
			green.A = 0.95f;
			// Largeur 1-2 px selon le zoom (pixel-art : entier, jamais antialiasé).
			float w = WorldView.CurrentZoom >= LeafShapeMinZoom ? 2f : 1f;
			// On s'arrête un peu avant le centre du limbe : le limbe (dessiné juste
			// après) recouvre la jonction, seule la base du pétiole reste visible.
			Vector2 petTip = insert.Lerp(leaf, 0.75f);
			DrawLine(insert, petTip, green, w, antialiased: false);
		}

		// Marques de TEXTURE sur une feuille (canaux additifs, ③), par-dessus le
		// limbe déjà dessiné. Ravageurs + grêle CRIBLENT le limbe (petits trous
		// sombres, nombre ∝ intensité) ; gel NOIRCIT les bords (contour brûlé). Les
		// trous sont placés au hash (i,j,k) → stables inter-frames (philo #3).
		private void DrawLeafDamage(Vector2 c, float r, int i, int j)
		{
			float bite = Mathf.Min(1f, _ravageurs + _grele); // criblage cumulé
			if (bite > 0f)
			{
				int holes = Mathf.CeilToInt(bite * 4f);   // 1 à 4 morsures
				for (int k = 0; k < holes; k++)
				{
					float a = Hash01(23 + k, i, j) * Mathf.Tau;
					float rad = (0.3f + 0.55f * Hash01(29 + k, i, j));
					Vector2 hp = c + new Vector2(Mathf.Cos(a) * rad * r * 1.15f,
												 Mathf.Sin(a) * rad * r * 0.65f);
					DrawCircle(hp, r * 0.22f, LeafHoleColor);
				}
			}
			if (_gel > 0f)
				DrawEllipseOutline(c, r * 1.15f, r * 0.65f, GelEdgeColor,
								   Mathf.Max(1f, _gel * 2.5f));
			// maladie : semis de petites taches brun foncé (pustules cryptogamiques),
			// nombre ∝ intensité. Salt NEUF (37/41) ≠ criblage (23/29) → les taches ne
			// se superposent jamais exactement aux trous ; rayon r*0.12 << r*0.22 du
			// criblage (ponctuation, pas morsure). Canal additif indépendant (D33).
			if (_maladie > 0f)
			{
				int spots = Mathf.CeilToInt(_maladie * 5f);   // 1 à 5 taches
				for (int k = 0; k < spots; k++)
				{
					float a = Hash01(37 + k, i, j) * Mathf.Tau;
					float rad = (0.2f + 0.65f * Hash01(41 + k, i, j));
					Vector2 sp = c + new Vector2(Mathf.Cos(a) * rad * r * 1.15f,
												 Mathf.Sin(a) * rad * r * 0.65f);
					DrawCircle(sp, r * 0.12f, LeafSpotColor);
				}
			}
		}

		// Génère les sommets d'une ellipse alignée écran (partagés entre le plein et
		// le contour) — petit polygone de n points (pixel art, pas de courbe lisse).
		private static Vector2[] EllipsePoints(Vector2 center, float rx, float ry, int n)
		{
			var pts = new Vector2[n];
			for (int i = 0; i < n; i++)
			{
				float a = Mathf.Tau * i / n;
				pts[i] = center + new Vector2(rx * Mathf.Cos(a), ry * Mathf.Sin(a));
			}
			return pts;
		}

		// Ellipse pleine alignée écran (Godot n'a pas de DrawEllipse natif) : 10
		// points — les feuilles se dessinent au SetStructure seulement, le coût par
		// redraw reste trivial (~10 vertices/feuille).
		private void DrawEllipse(Vector2 center, float rx, float ry, Color col) =>
			DrawColoredPolygon(EllipsePoints(center, rx, ry, 10), col);

		// Contour d'ellipse fermé (gel : bords noircis) — polyligne bouclée sur le
		// premier point.
		private void DrawEllipseOutline(Vector2 center, float rx, float ry, Color col, float width)
		{
			var pts = EllipsePoints(center, rx, ry, 10);
			var loop = new Vector2[pts.Length + 1];
			pts.CopyTo(loop, 0);
			loop[pts.Length] = pts[0];
			DrawPolyline(loop, col, width, antialiased: false);
		}
	}
}
