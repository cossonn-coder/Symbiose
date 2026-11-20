// SYMBIOSE — PlantRenderer.Splats.cs (partial, sprint PRÉCUISSON SPLATS ④)
// Les PIÈCES SPLAT à tous les paliers (×4 → ×32 au ④, ×0,5 → ×2 au ⑤bis) : là où un port dessinait une
// feuille, une tête ou un fruit en triangles, la cuisson pose la pièce précuite
// (tools/splat/, chargée par SplatPlanches.cs) :
//  • choisie par FORME (table « nom vue → recette », champ `vue` des manifestes) ;
//  • VUE la plus proche de l'orientation de l'organe AU REPOS dans le repère de la
//    caméra (rotation D35 comprise). Pas la pose de vent : une feuille proche d'une
//    frontière entre deux vues clignoterait d'une pose à l'autre (mesure du ①, saut
//    de 0,81 entre lacets voisins). Le vent déplace toujours le POINT d'attache ;
//  • VARIANTE au hash (philo #3), DEGRÉ DE TROU (D5, ×16-×32) selon les dégâts que
//    la vue lit déjà (`ravageurs`, `grele`) ;
//  • posée à son point d'ATTACHE, au pixel interne entier ;
//  • teintée par le n° de palette que la vue calculait déjà (espèce × saison ×
//    santé × givre × maturité) — rien ne change dans le calcul des couleurs.
// Les couleurs de symptômes (nécrose, taches, givre) restent dessinées (D5).
//
// INTERRUPTEUR : Maj+F11 (WorldView.Controls.cs) ou SYMBIOSE_SPLATS=0 au lancement
// (capture « avant » sur la VM). Éteint, ou hors palette indexée (F11 OFF, dessin
// direct), ou pièce absente : l'ANCIEN dessin vectoriel est tracé, inchangé.
//
// TAILLE : une pièce est cuite à la taille NOMINALE de sa recette (zooms entiers, pas
// de mise à l'échelle) — la longueur de feuille de la vue n'est pas suivie (point F5).
//
// 📖 Pédagogie Godot : un port accumule ses triangles dans un LOT (un seul envoi,
// LotTriangles) peint à la fin. Une pièce est une TEXTURE, hors du lot : pour garder
// l'ordre de peinture (du fond vers l'avant), on vide le lot avant chaque pièce —
// comme on vide un tampon d'écriture avant un accès direct au périphérique.
//
// Déterministe (hash, zéro Random), purement visuel : golden non concerné.

using Godot;

namespace Symbiose
{
	public partial class PlantRenderer
	{
		/// <summary>Pièces splat à tous les paliers (Maj+F11 ; SYMBIOSE_SPLATS=0 = éteint).</summary>
		internal static bool SplatsActifs { get; private set; } =
			System.Environment.GetEnvironmentVariable("SYMBIOSE_SPLATS") != "0";

		/// <summary>Maj+F11 : bascule avant/après ; toutes les plantes recuisent.</summary>
		internal static void BasculerSplats()
		{
			SplatsActifs = !SplatsActifs;
			OublierKit();   // le kit des paliers bas change de source (⑤)
			foreach (var p in BakeQueue.All) p.Invalidate();
			GD.Print($"[Splats] Maj+F11 → pièces splat {(SplatsActifs ? "ON" : "OFF (dessin vectoriel)")}.");
		}

		// Une pièce splat a été posée sur une feuille de ce coup de pinceau : les trous
		// sont alors DANS la pièce, PoserDetailsPrairie ne les re-crible pas (remis à faux
		// à sa fin).
		private bool _feuillesSplat;

		// ⑤bis (D4 « tous les zooms en splats ») : plus de plancher de palier — les ports
		// dessinés aux paliers bas (×0,5-×2 : herbacées, prairie, lianes) posent eux aussi
		// leurs pièces, cuites à ces paliers depuis le ①. Les cas où la pièce devient du
		// bruit restent dessinés, au cas par cas (PlantRenderer.SplatsBas.cs).
		private bool SplatsIci => SplatsActifs && Indexe;

		// --- Formes → recettes (table du champ `vue` des manifestes ②③) -------------

		private static string RecetteFeuille(FormeFeuille f, MarqueFeuille m) => f switch
		{
			FormeFeuille.Dentee => "feuille_dentee",
			FormeFeuille.Spatule => "feuille_spatule",
			FormeFeuille.Lobee => "feuille_lobee",
			FormeFeuille.Ovale => "feuille_ovale",
			FormeFeuille.Cuillere => "feuille_cuillere",
			FormeFeuille.Plume => "feuille_plume",
			FormeFeuille.Ruban => "feuille_ruban",
			FormeFeuille.Coeur => "feuille_coeur",
			FormeFeuille.Scie => m == MarqueFeuille.Gaufre ? "feuille_scie_gaufree" : "feuille_scie",
			FormeFeuille.Lanceolee => m == MarqueFeuille.Gaufre ? "feuille_lanceolee_gaufree" : "feuille_lanceolee",
			FormeFeuille.Palmee => "feuille_palmee",
			FormeFeuille.Paume => "feuille_paume",
			FormeFeuille.Triade => "feuille_triade",
			FormeFeuille.Composee => "feuille_composee",
			FormeFeuille.Lierre => "feuille_lierre",
			_ => null,
		};

		private static string RecetteTete(FormeTete t, bool fleur) => t switch
		{
			FormeTete.Capitule => fleur ? "tete_capitule" : "tete_boule",   // aigrette = boule (③)
			FormeTete.Bouquet => "tete_bouquet",
			FormeTete.Chapelet => "tete_chapelet",
			FormeTete.Epi => "tete_epi",
			FormeTete.Ombelle => "tete_ombelle",
			FormeTete.Boule => "tete_boule",
			FormeTete.Grappe => "tete_grappe",
			FormeTete.Soleil => "tete_soleil",
			FormeTete.Etoile => "tete_etoile",
			FormeTete.Pendante => "tete_pendante",
			FormeTete.Corolle => "tete_corolle",
			FormeTete.Trompette => "tete_trompette",
			FormeTete.Papillon => fleur ? "tete_papillon" : null,   // gousses : PoserGoussesSplat (④bis)
			_ => null,
		};

		// --- Feuilles -----------------------------------------------------------------

		/// <summary>Pose la feuille `fe` en pièce splat ; false = rien posé (le dessin
		/// vectoriel prend le relais).</summary>
		private bool PoserFeuilleSplat(string recette, FeuillePosee fe, Color col)
		{
			if (!SplatsIci || recette == null) return false;
			// Inclinaison au repos : montée du bout (HautZ) sur l'emprise au sol (PointFeuille).
			float sol = Mathf.Max(fe.Long * (1f - 0.6f * fe.Dressee), 0.01f);
			return PoserPieceFeuille(recette, PointFeuille(fe, 0f, 0f), Mathf.RadToDeg(Mathf.Atan2(fe.HautZ, sol)),
				WorldView.WorldToScreenOffset(fe.U.X, fe.U.Y), fe.K, col);
		}

		/// <summary>Pose une feuille-pièce à son attache `ancre` : inclinaison cuite la plus proche
		/// de `incDeg`, lacet de la direction ÉCRAN `dirEcran`, variante et trou au hash de `k`.
		/// Partagé par les ports (PoserFeuilleSplat) et le chemin générique (④bis).</summary>
		private bool PoserPieceFeuille(string recette, Vector2 ancre, float incDeg, Vector2 dirEcran, int k, Color col)
		{
			if (!SplatPlanches.Vues(recette, out int[] incs, out int lacets, out int variantes)) return false;
			int inc = PlusProche(incs, incDeg);
			int lacet = LacetEcran(dirEcran, lacets);
			int trou = TrouFeuille(k);
			int v = trou > 0 ? 0 : Variante(k, variantes);   // trous cuits sur la variante 0 (②)
			float z = WorldView.CurrentZoom;
			if (!SplatPlanches.Trouver(recette, z, 0, inc, lacet, v, trou, out var p)
				&& (trou == 0 || !SplatPlanches.Trouver(recette, z, 0, inc, lacet, v, 0, out p))) return false;
			PoserPieceSplat(p, ancre, PaletteIndexee.Palette(col));
			_feuillesSplat = true;
			return true;
		}

		// Degré de trou (D5) d'une feuille : 0 sain, 1-2 morsure, 3-4 grêle. Seulement aux
		// paliers des symptômes (×16, ×32) ; une feuille sur `intensité` est touchée (hash).
		private int TrouFeuille(int k)
		{
			if (!AuPalier(PalierSymptomesZoom)) return 0;
			float bite = Mathf.Min(1f, _ravageurs + _grele);
			if (bite <= 0f || Hash01(601, k, GraineIndividu) >= bite) return 0;
			return (bite > 0.5f ? 2 : 1) + (_grele > _ravageurs ? 2 : 0);
		}

		// --- Têtes et fruits ------------------------------------------------------

		/// <summary>Tête de port en pièce splat, une palette par couche (③) ; false = rien posé.</summary>
		private bool PoserTeteSplat(FichePort f, Vector2 pied, Vector2 sommet, Color c, bool fleur, int graine)
		{
			string recette = RecetteTete(f.Tete, fleur);
			if (!SplatsIci || recette == null || !SplatPlanches.Vues(recette, out int[] incs, out int lacets, out int variantes))
				return false;
			// Attache de la recette : la base de l'épi (tiers haut de la hampe dans la vue), le
			// foyer des rayons de l'ombelle (≈ 2,75 cm sous le plateau), le sommet ailleurs.
			Vector2 ancre = f.Tete switch
			{
				FormeTete.Epi => pied.Lerp(sommet, 0.66f),
				FormeTete.Ombelle => sommet + new Vector2(0f, 2.75f * WorldView.PxPerCmZ),
				_ => sommet,
			};
			int lacet = (int)(Hash01(605, graine, 0) * lacets) % Mathf.Max(lacets, 1) * 360 / Mathf.Max(lacets, 1);
			return PoserCouches(recette, ancre, PlusProche(incs, 0f), lacet, Variante(graine, variantes), c, fleur);
		}

		/// <summary>Fruit de port en pièce splat (globe, ou long et couché) ; false = rien posé.</summary>
		private bool PoserFruitSplat(Vector2 c, float allonge, Color col, int i)
		{
			string recette = allonge <= 1f ? "fruit_globe" : "fruit_long";
			if (!SplatsIci || !SplatPlanches.Vues(recette, out int[] incs, out int lacets, out int variantes)) return false;
			// Même direction que la capsule vectorielle (PoserFruit) : angle au hash du fruit.
			float a = Mathf.Tau * Hash01(359, GraineIndividu, i);
			int lacet = LacetEcran(new Vector2(Mathf.Cos(a), Mathf.Sin(a) * 0.5f), lacets);
			return PoserCouches(recette, c, PlusProche(incs, 0f), lacet, Variante(i + GraineIndividu, variantes), col, true);
		}

		// Toutes les couches d'une pièce d'organe, chacune avec sa palette.
		private bool PoserCouches(string recette, Vector2 ancre, int inc, int lacet, int v, Color c, bool fleur)
		{
			if (!OrganesSplatIci) return false;   // ⑤bis : têtes et fruits dessinés sous ×2 (SplatsBas.cs)
			string[] couches = SplatPlanches.Couches(recette);
			var pal = PaletteIndividu();
			float z = WorldView.CurrentZoom;
			bool posee = false;
			for (int k = 0; k < couches.Length; k++)
			{
				// Tournesol fané : seul le disque de graines reste (comme PoserSoleil).
				if (recette == "tete_soleil" && !fleur && couches[k] != "coeur") continue;
				if (!SplatPlanches.Trouver(recette, z, k, inc, lacet, v, 0, out var p)) continue;
				PoserPieceSplat(p, ancre, PaletteIndexee.Palette(CouleurCouche(recette, couches[k], c, pal)));
				posee = true;
			}
			return posee;
		}

		// Teinte d'une couche (③ : « une palette par couche, comme CouchePiece »).
		private static Color CouleurCouche(string recette, string couche, Color c, in OrganPalette pal) => couche switch
		{
			"coeur" => recette == "tete_soleil" ? pal.FruitRipe : FlowerHeart,
			"revers" or "sepales" or "pedoncule" => pal.Leaf,
			"rayons" when recette == "tete_ombelle" => pal.Leaf,
			"silicules" => pal.FruitUnripe,
			"fleurs" when recette == "tete_chapelet" => pal.Flower,
			_ => c,
		};

		// --- Outils communs -----------------------------------------------------------

		// Pose une pièce : vide le lot (ordre de peinture), cale le coin sur la grille des
		// px internes, un tracé texture × modulate (n° de palette).
		private void PoserPieceSplat(in SplatPlanches.Piece p, Vector2 ancre, int palette)
		{
			if (_lotPrairie != null && _lotPrairie.Sommets > 0)
			{
				_lotPrairie.DessinerSansMaille(this);
				_lotPrairie.Vider();
			}
			float z = WorldView.CurrentZoom;
			Vector2 coin = ((ancre * z).Round() - (Vector2)p.Attache) / z;
			DrawTextureRectRegion(p.Tex, new Rect2(coin, (Vector2)p.Rect.Size / z), (Rect2)p.Rect,
				PaletteIndexee.ModulatePiece(palette));
		}

		// Lacet cuit (degrés) le plus proche d'une direction ÉCRAN : on défait la projection
		// d'orientation 0 (WorldView.ScreenToWorld) — la direction vue par la caméra, quelle
		// que soit la rotation D35 — puis l'angle trigo vu du dessus (0 = est, 90 = nord,
		// convention de tools/splat/lib/iso.js).
		private static int LacetEcran(Vector2 s, int lacets)
		{
			if (lacets <= 1) return 0;
			float x = s.X / (2f * WorldView.PxPerCmX) + s.Y / (2f * WorldView.PxPerCmY);
			float y = -s.X / (2f * WorldView.PxPerCmX) + s.Y / (2f * WorldView.PxPerCmY);
			float pas = Mathf.Tau / lacets;
			int k = Mathf.PosMod(Mathf.RoundToInt(Mathf.Atan2(-y, x) / pas), lacets);
			return k * 360 / lacets;
		}

		private static int PlusProche(int[] valeurs, float cible)
		{
			int best = valeurs[0];
			foreach (int v in valeurs)
				if (Mathf.Abs(v - cible) < Mathf.Abs(best - cible)) best = v;
			return best;
		}

		private int Variante(int k, int variantes) =>
			Mathf.Min(variantes - 1, (int)(Hash01(603, k, GraineIndividu) * variantes));
	}
}
