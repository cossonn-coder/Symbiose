// SYMBIOSE — PlantRenderer.SplatsOrganes.cs (partial, sprint PRÉCUISSON SPLATS ④bis)
// Les PIÈCES SPLAT des organes que le ④ laissait dessinés, aux paliers ×4 → ×32 :
//  • chaume : épi de blé, épi barbu du seigle, panicule du pâturin ;
//  • haricot hors fleur : les deux gousses qui pendent ;
//  • arbres : chatons, fleurs en corolle et boutons (fleur une à une dès ×4 quand les
//    pièces sont allumées, au lieu des gerbes de fleurs) ; fleurs SNES des plantes à segments ;
//  • prairie : feuilles du plantain, son épi, pompons du trèfle et glomérules du dactyle ;
//  • chemin générique (DrawOrgans, plantes sans fiche) : feuilles ×8+, fleurs, fruits ronds.
// Même outillage que le ④ (PlantRenderer.Splats.cs) : vue la plus proche, variante au hash,
// palette calculée par la vue, MÊME interrupteur (Maj+F11, SYMBIOSE_SPLATS=0). Chaque
// fonction rend false quand elle n'a rien posé : l'ancien dessin vectoriel prend le relais.
//
// Restaient dessinés, faute de recette (cf. 00_etat.md ④bis) : feuilles du trèfle, masses du
// buisson, panicule de la fétuque → pièces depuis RELIQUATS ④ (PlantRenderer.SplatsHerbes.cs).
// Restent dessinés (sprint S2) : brins et rubans des graminées (lanières que le vent plie
// point par point), masses et gerbes d'arbre ×4.
//
// 📖 Pédagogie : une recette d'organe porte DÉJÀ sa pose naturelle (l'épi de seigle est cuit
// penché, la gousse et le chaton pendants). La vue ne choisit donc que le LACET (vers où
// l'organe regarde) ; l'inclinaison reste la plus proche de 0, comme les têtes du ④.
//
// Déterministe (hash, zéro Random), purement visuel : golden non concerné.

using Godot;

namespace Symbiose
{
	public partial class PlantRenderer
	{
		// Centre de la boule de tete_boule au-dessus de son attache : 0,9 × rayon nominal 2 cm (③).
		private const float BouleSurAttacheCm = 1.8f;

		/// <summary>Toutes les couches de `recette` en `ancre` : lacet de la direction ÉCRAN `dirEcran`
		/// (au hash de `graine` si nulle), inclinaison la plus proche de 0, variante au hash, classe
		/// de taille la plus proche de `tailleCm` (RELIQUATS ② ; 0 = taille non suivie → nominale).</summary>
		private bool PoserOrganeSplat(string recette, Vector2 ancre, Vector2 dirEcran, Color c, int graine, float tailleCm = 0f)
		{
			if (!SplatsIci || !SplatPlanches.Vues(recette, out int[] incs, out int lacets, out int variantes)) return false;
			int lacet = dirEcran == Vector2.Zero ? LacetHash(graine, lacets) : LacetEcran(dirEcran, lacets);
			return PoserCouches(recette, ancre, PlusProche(incs, 0f), lacet, Variante(graine, variantes), c, true, tailleCm);
		}

		private int LacetHash(int graine, int lacets)
		{
			lacets = Mathf.Max(lacets, 1);
			return (int)(Hash01(607, graine, GraineIndividu) * lacets) % lacets * 360 / lacets;
		}

		// --- Chaume ---------------------------------------------------------------------

		/// <summary>Épi de chaume de `lenCm` posé à sa base, tourné vers le côté où penche son brin. Le
		/// seigle est cuit retombant (Penche 0,7 dans la recette) ; sans barbe ni largeur : rien.</summary>
		private bool PoserEpiSplat(FicheChaume c, Vector3 base3, Vector2 u, Color teinte, int graine, float lenCm)
		{
			string recette = c.BarbeCm > 0f ? "epi_barbu" : c.EpiLargeCm >= 1f ? "epi_ble" : null;
			return recette != null && PoserOrganeSplat(recette, Iso(base3.X, base3.Y, base3.Z),
				WorldView.WorldToScreenOffset(u.X, u.Y), teinte, graine, lenCm);
		}

		/// <summary>Panicule du pâturin de `lenCm`, posée au sommet du chaume, teinte des épillets verts.</summary>
		private bool PoserPaniculeSplat(Vector3 cime, Color teinte, int graine, float lenCm) =>
			PoserOrganeSplat("panicule", Iso(cime.X, cime.Y, cime.Z), Vector2.Zero, teinte, graine, lenCm);

		// --- Gousses, chatons, fleurs ---------------------------------------------------------

		/// <summary>Les deux gousses du haricot, pendues côte à côte comme PoserGousses.</summary>
		private bool PoserGoussesSplat(Vector2 c, float r, Color col, int graine)
		{
			bool posee = false;
			for (int k = 0; k < 2; k++)
				posee |= PoserOrganeSplat("gousse", c + new Vector2(k * r * 1.6f, 0f), Vector2.Zero, col, graine * 2 + k);
			return posee;
		}

		private bool PoserChatonSplat(Vector2 c, Color col, int k) =>
			PoserOrganeSplat("chaton", c, Vector2.Zero, col, k);

		/// <summary>Corolle à 5 pétales et cœur (tete_corolle : fleur SNES, fleur d'arbre), au rayon
		/// de la fleur SNES de l'ancien dessin (FleurRayonCm).</summary>
		private bool PoserCorolleSplat(Vector2 c, Color col, int k) =>
			PoserOrganeSplat("tete_corolle", c, Vector2.Zero, col, k, FleurRayonCm);

		/// <summary>Une fleur d'arbre des bouquets : bouton fermé (teinte de bouton de l'espèce,
		/// sépales du feuillage) ou corolle ouverte.</summary>
		private bool PoserFleurArbreSplat(Vector2 pos, in FleurArbre f, Color fleur, Color bouton) =>
			f.Bouton ? PoserOrganeSplat("bouton", pos, Vector2.Zero, bouton, f.K) : PoserCorolleSplat(pos, fleur, f.K);

		/// <summary>Boule de fleurons (pompon du trèfle, glomérule du dactyle) de `rayonCm`, centrée en
		/// `c` : la recette a sa tige sous la boule, on l'attache donc 1,8 cm × la classe plus bas.</summary>
		private bool PoserBouleSplat(Vector2 c, Color col, int graine, float rayonCm)
		{
			float k = SplatPlanches.Classe("tete_boule", rayonCm) / 100f;
			return PoserOrganeSplat("tete_boule", c + new Vector2(0f, BouleSurAttacheCm * k * WorldView.PxPerCmZ), Vector2.Zero,
				col, graine, rayonCm);
		}

		// --- Prairie : plantain ---------------------------------------------------------------

		/// <summary>Feuille du plantain plaquée au sol, le bout relevé (feuille_lancéolée).</summary>
		private bool PoserPlantainSplat(Vector2 u, float l, Color col, int k)
		{
			if (!SplatsIci) return false;
			var fe = new FeuillePosee(u, l, l * LargeurPlantain * 2f, 0.1f, LeveePlantainCm, 0f, PaletteIndexee.TonBase, k);
			return PoserFeuilleSplat("feuille_lanceolee", fe, col);
		}

		// --- Chemin générique (DrawOrgans) ----------------------------------------------------

		private static string RecetteLimbe(LeafShape s) => s switch
		{
			LeafShape.Aciculaire => "feuille_aiguille",
			LeafShape.Cordee => "feuille_coeur",
			LeafShape.Composee => "feuille_composee",
			LeafShape.Lanceolee => "feuille_lanceolee",
			LeafShape.Lobee => "feuille_paume",
			_ => "feuille_ovale",
		};

		/// <summary>Feuille du chemin générique (forme par espèce, LeafProfiles) attachée à son point
		/// d'insertion, tournée vers son limbe. Une feuille naissante sous le plancher de rayon
		/// reste dessinée : la pièce, cuite adulte, la grandirait d'un coup.</summary>
		private bool PoserLimbeSplat(Vector2 insert, Vector2 c, float rx, Color col, int i, int j)
		{
			if (!SplatsIci || rx < LeafFloorRadiusPx / WorldView.CurrentZoom) return false;
			if (!LeafProfiles.TryGetValue(_structure.SpeciesName, out var prof)) prof = DefaultLeaf;
			// Longueur : l'ancien limbe est une ellipse de demi-grand axe `rx` tracée à PxPerCmX dans
			// TOUTES les directions, la pièce suit le losange du sol (jusqu'à √2 × PxPerCmX) : même
			// correction √2 que les organes ronds (tools/splat/lib/classes.js).
			float longCm = 2f * rx / (WorldView.PxPerCmX * Mathf.Sqrt2);
			return PoserPieceFeuille(RecetteLimbe(prof.Shape), insert, 0f, c - insert, Melange(i, j) & 0xFFFFF, col, longCm);
		}
	}
}
