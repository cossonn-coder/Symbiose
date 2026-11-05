// SYMBIOSE — PlantRenderer.Assemblee.cs (partial, PLANTE ASSEMBLÉE ⑤)
// La PLANTE ASSEMBLÉE des paliers bas (×0,5 · ×1 · ×2), à la place des
// ellipses-blobs (DrawCouronne) : les VRAIS segments en tiges de 1 px (plus si
// le bois est épais), et aux rameaux feuillés des TOUFFES du kit (④,
// PlantRenderer.Kit.cs) de la forme de feuille de l'espèce. On change la FORME,
// pas l'information (conception_rendu_visible.md §4 D4) : la teinte reste celle
// des paliers (espèce + saison dès ×0,5, santé dès ×2, givre), la neige se pose
// sur les touffes, les fleurs deviennent des fleurons du kit dès ×2.
//
//  • TAILLE d'une touffe ∝ palier (3 px à ×0,5, 5 à ×1, 7 à ×2, 9 pour un arbre
//    à ×2), bornée par la taille de la plante (jamais plus grosse qu'elle).
//  • NOMBRE ∝ `foliage_density` : chaque emplacement le long d'un rameau feuillé
//    est gardé si son hash < densité (les MÊMES d'une cuisson à l'autre).
//  • ORDRE : du fond (nord-projeté) vers l'avant — le volume se lit.
//  • LUMIÈRE : le kit est éclairé vers le BAS de la pièce (sud de l'orientation
//    0). Quand la rotation D35 met le sud EN HAUT de l'écran (orientations 2-3),
//    on PERMUTE ombre et lumière dans la rampe au lieu de retourner la pièce : un
//    retournement ferait pendre les feuilles dressées (ail, poireau).
//
// CASSÉ À L'ÉCRAN ③ — PALETTE INDEXÉE (PaletteIndexee.cs) : dans le PINCEAU de
// cuisson, chaque pièce est posée en UN tracé avec la texture des CODES (canal G
// du kit : ton + orientation de face) × modulate = n° de palette de la plante ;
// tiges, neige, fleurons passent aussi par un n° de palette. La lumière (et la
// permutation ombre/lumière selon la rotation D35) est alors l'affaire du shader
// de lecture, côté soleil réel. Le dessin DIRECT (plante pas encore cuite) et F11
// OFF gardent le chemin littéral ci-dessous, inchangé.
//
// 📖 Pédagogie Godot : le kit est en NIVEAUX (indices). Plutôt que créer une
// texture par couleur de plante, on fabrique UNE fois une texture « masques »
// (une bande blanche par niveau) et on dessine chaque pièce niveau par niveau
// avec `modulate` = la couleur de rampe (blanc × couleur = couleur). Comme une
// LUT appliquée au tracé : zéro texture par plante, et tout reste dans la
// cuisson (aucun coût par image, pré-cuisson T2).

using Godot;
using System.Collections.Generic;

namespace Symbiose
{
	public partial class PlantRenderer
	{
		// Taille de base d'une touffe (px internes) par palier, et seuil d'emprise
		// (px internes) au-delà duquel une grande plante passe au cran au-dessus.
		private const float TouffeGrandePx = 64f;
		// Espacement des touffes le long d'un rameau, en fraction de leur taille.
		private const float TouffePas = 0.6f;
		private const int TouffesParSegmentMax = 8;
		// Couronne des arbres (④) : touffes voisines par emplacement, rayon du volume (cm).
		private const int TouffesAutourArbre = 2;
		private const float EtalementTouffesCm = 28f;
		// Semis au sol (port sans rameau feuillé) : une touffe par ~SemisPx2 px².
		private const float SemisPx2 = 30f;
		private const int SemisMax = 12;

		private static ImageTexture _kitMasques, _kitCodes;
		private static int _kitLargeur;

		/// <summary>Vrai pendant le dessin d'un pinceau qui cuit en palette indexée
		/// (③) : les couleurs posées sont des CODES, pas des couleurs. Depuis ④, à
		/// TOUS les paliers (même grammaire ×0,5 → ×32, PlantRenderer.Motifs.cs).</summary>
		private bool Indexe => IsBrush && PaletteIndexee.Active;

		// Couleur littérale → son code de palette quand le pinceau cuit indexé.
		private Color Lit(Color c) => Indexe ? PaletteIndexee.Litterale(c) : c;

		// Graine INDIVIDUELLE (hash de position du pied, _swayPhase) : deux voisins
		// de même structure ne tirent pas les mêmes variantes de touffes (③).
		private int GraineIndividu => (int)(_swayPhase * 9973f);

		private readonly record struct Touffe(float Prof, Vector2 Pos, int Taille, int Variante, int Seg, int K);

		/// <summary>Plante assemblée (feuillée) : tiges, touffes, neige, fleurons.
		/// `c` = teinte du palier (espèce + saison, santé à ×2, givre).</summary>
		private void DrawPlanteAssemblee(Color c, bool sante)
		{
			float z = WorldView.CurrentZoom;
			DrawTigesAssemblees(z);
			Color[] rampe = RampeKit(c);
			if (SouthDir().Y < 0f) (rampe[KitOmbre], rampe[KitLumiere]) = (rampe[KitLumiere], rampe[KitOmbre]);
			int palette = Indexe ? PaletteIndexee.Palette(c) : -1;
			if (!LeafProfiles.TryGetValue(_structure.SpeciesName, out var prof)) prof = DefaultLeaf;
			var touffes = PlacerTouffes(z, TailleTouffe(z));
			touffes.Sort((a, b) => a.Prof.CompareTo(b.Prof));
			foreach (var t in touffes)
			{
				if (palette >= 0) DrawPieceIndexee(KitTouffe(prof.Shape, t.Taille, t.Variante), t.Pos, z, palette, -1);
				else DrawPiece(KitTouffe(prof.Shape, t.Taille, t.Variante), t.Pos, z, rampe, KitContour, KitLumiere);
				if (_snow > 0f && Hash01(77, t.Seg, t.K) < _snow)
				{
					float demi = t.Taille * 0.5f / z;
					DrawSnowCrown(t.Pos, demi, demi * 0.7f);
				}
			}
			if (sante) DrawFleurons(touffes, z);
		}

		// Tiges et fût : chaque segment, du plus épais (dessous) au plus fin, en
		// ligne ≥ 1 px interne, couleur de lignification (vert-tendre → bois),
		// même projection que DrawBoisNu / DrawSegments.
		private void DrawTigesAssemblees(float z)
		{
			Vector3 c = _structure.ColletCm;
			var segs = new List<Segment>(_structure.Segments);
			segs.Sort((a, b) => b.ThicknessCm.CompareTo(a.ThicknessCm));
			bool houppier = Houppier;
			foreach (var s in segs)
			{
				Vector3 tip = s.Base + s.Dir * s.LengthCm;
				float w = Mathf.Max(1f / z, Mathf.Round(s.ThicknessCm * WorldView.PxPerCmX * WoodWidthFactor));
				DrawLine(Iso(s.Base.X - c.X, s.Base.Y - c.Y, s.Base.Z),
						 Iso(tip.X - c.X, tip.Y - c.Y, tip.Z), Lit(AvecEcorce(WoodRamp(LigVue(s, houppier)), s)), w, antialiased: false);
				if (houppier) DrawBoutTendre(s, c);
			}
		}

		// Taille de touffe du palier, bornée par l'emprise de la plante (≤ 60 %).
		private int TailleTouffe(float z)
		{
			float emprise = EmpriseInternePx();
			int i = z < PalierPortZoom ? 0 : z < PalierSanteZoom ? 1 : 2;
			if (emprise >= TouffeGrandePx) i++;
			if (RecetteDeLaPlante(out var recette)) i += recette.CranTouffe;   // grain du feuillage (④)
			i = Mathf.Clamp(i, 0, KitTailles.Length - 1);
			while (i > 0 && KitTailles[i] > emprise * 0.6f) i--;
			return KitTailles[i];
		}

		// Emplacements : le long des segments feuillés (IsLeafy), du bout vers la
		// base, tous les TouffePas × taille ; gardés au hash si < foliage_density.
		// Un sur trois descend d'un cran de taille (grain du feuillage).
		private List<Touffe> PlacerTouffes(float z, int taille)
		{
			var liste = new List<Touffe>();
			Vector3 c = _structure.ColletCm;
			float dens = Mathf.Clamp(_structure.DensiteVisible, 0f, 1f);
			float retombee = RetombeeCm;
			int autour = RecetteDeLaPlante(out _) ? TouffesAutourArbre : 0;
			bool feuille = false;
			foreach (var s in _structure.Segments)
			{
				if (!IsLeafy(s)) continue;
				feuille = true;
				Vector3 tip = s.Base + s.Dir * s.LengthCm;
				Vector2 p1 = Iso(s.Base.X - c.X, s.Base.Y - c.Y, s.Base.Z);
				Vector2 p2 = Iso(tip.X - c.X, tip.Y - c.Y, tip.Z);
				float pas = taille * TouffePas / z;
				int n = Mathf.Min(TouffesParSegmentMax, 1 + (int)(p1.DistanceTo(p2) / pas));
				int cle = CleSegment(s);   // stable : une coupe ailleurs ne déplace rien (HOUPPIER ④)
				for (int k = 0; k < n; k++)
				{
					if (Hash01(71, cle, k) >= dens) continue;
					float u = 1f - k * pas / Mathf.Max(p1.DistanceTo(p2), 1e-4f);
					Vector3 p = s.Base + s.Dir * (s.LengthCm * Mathf.Max(u, 0f));
					liste.Add(NouvelleTouffe(p - c, Iso(p.X - c.X, p.Y - c.Y, p.Z - retombee), taille, cle, k));
					for (int m = 1; m <= autour; m++)
						AjouterTouffeAutour(liste, p, c, retombee, taille, cle, k + m * TouffesParSegmentMax);
				}
			}
			if (!feuille) SemerTouffes(liste, z, taille);
			return liste;
		}

		// Couronne d'un ARBRE aux paliers bas (AUTOMNE VISIBLE ④) : une touffe sur un rameau ne
		// fait que 5-9 px pour une couronne de 100-200 px, on voyait les branches et non un
		// feuillage. Chaque emplacement gardé porte donc des touffes voisines, déportées au hash
		// dans un volume autour du rameau. Clé `kh` propre : même présence d'une cuisson à l'autre.
		private void AjouterTouffeAutour(List<Touffe> liste, Vector3 p, Vector3 c, float retombee,
										 int taille, int i, int kh)
		{
			float a = Mathf.Tau * Hash01(73, i, kh), d = EtalementTouffesCm * Mathf.Sqrt(Hash01(75, i, kh));
			float dz = EtalementTouffesCm * (Hash01(77, i, kh) - 0.5f);
			float x = p.X - c.X + d * Mathf.Cos(a), y = p.Y - c.Y + d * Mathf.Sin(a), z = p.Z + dz;
			if (z < 0f) return;   // pas de feuillage sous le sol
			liste.Add(NouvelleTouffe(new Vector3(x, y, z - c.Z), Iso(x, y, z - retombee), taille, i, kh));
		}

		// Port sans rameau feuillé exploitable (tapis, rosette très plate) : semis
		// de touffes sur l'emprise RÉELLE au sol (disque de rayon _rayonReelCm).
		private void SemerTouffes(List<Touffe> liste, float z, int taille)
		{
			float r = Mathf.Max(_rayonReelCm, 1f);
			float aire = Mathf.Pi * r * WorldView.PxPerCmX * r * WorldView.PxPerCmY * z * z;
			int n = Mathf.Clamp((int)(aire / SemisPx2), 1, SemisMax);
			float dens = Mathf.Clamp(_structure.DensiteVisible, 0f, 1f);
			for (int k = 0; k < n; k++)
			{
				if (k > 0 && Hash01(71, -1, k) >= dens) continue;
				float a = Mathf.Tau * Hash01(73, -1, k), d = r * Mathf.Sqrt(Hash01(75, -1, k));
				var p = new Vector3(d * Mathf.Cos(a), d * Mathf.Sin(a), 0f);
				liste.Add(NouvelleTouffe(p, Iso(p.X, p.Y, 0f), taille, -1, k));
			}
		}

		// Profondeur iso = Y écran de la projection AU SOL (nord-projeté d'abord),
		// la hauteur départageant (le haut d'une même verticale passe devant).
		private Touffe NouvelleTouffe(Vector3 rel, Vector2 pos, int taille, int i, int k)
		{
			float prof = WorldView.WorldToScreenOffset(rel.X, rel.Y).Y + rel.Z * 1e-3f;
			int t = taille, g = GraineIndividu;
			if (t > KitTailles[0] && Hash01(79, i + g, k) < 0.33f)
				t = KitTailles[System.Array.IndexOf(KitTailles, t) - 1];
			int v = Mathf.Min(KitVariantes - 1, (int)(Hash01(81, i, k + g) * KitVariantes));
			return new Touffe(prof, pos, t, v, i, k);
		}

		// Fleurons (×2) : sur une touffe sur ~(floraison) des bouts, posés en haut
		// de la touffe (fleurs terminales) ; taille ∝ touffe. Couleur = fleur de
		// l'espèce, cœur `FlowerHeart` (RampeKit).
		private void DrawFleurons(List<Touffe> touffes, float z)
		{
			if (_structure.Floraison < FloraisonSeuil) return;
			if (!Palettes.TryGetValue(_structure.SpeciesName, out var pal)) pal = DefaultPalette;
			Color[] rampe = RampeKit(pal.Flower);
			int palFleur = Indexe ? PaletteIndexee.Palette(pal.Flower) : -1;
			int palCoeur = Indexe ? PaletteIndexee.Palette(FlowerHeart) : -1;
			foreach (var t in touffes)
			{
				if (Hash01(83, t.Seg, t.K) >= _structure.Floraison * 0.6f) continue;
				Fleuron f = t.Taille >= 9 ? Fleuron.Etoile : t.Taille >= 7 ? Fleuron.Bouton : Fleuron.Point;
				var pos = t.Pos + new Vector2((Hash01(85, t.Seg, t.K) - 0.5f) * t.Taille * 0.5f,
											  -t.Taille * 0.25f) / z;
				if (palFleur >= 0) DrawPieceIndexee(KitFleuron(f), pos, z, palFleur, palCoeur);
				else DrawPiece(KitFleuron(f), pos, z, rampe, KitBase, KitCoeur);
			}
		}

		// Pièce INDEXÉE (③) : un tracé pour le corps (codes du kit × n° de palette),
		// un second pour le cœur d'un fleuron (sa propre palette) si `palCoeur` ≥ 0.
		private void DrawPieceIndexee(Rect2I r, Vector2 centre, float z, int palette, int palCoeur)
		{
			AssurerMasques();
			Vector2 coin = ((centre * z) - (Vector2)r.Size * 0.5f).Round() / z;
			var dst = new Rect2(coin, (Vector2)r.Size / z);
			DrawTextureRectRegion(_kitCodes, dst, (Rect2)r, PaletteIndexee.ModulatePiece(palette));
			if (palCoeur >= 0)
				DrawTextureRectRegion(_kitCodes, dst, new Rect2(r.Position.X + _kitLargeur, r.Position.Y,
					r.Size.X, r.Size.Y), PaletteIndexee.ModulatePiece(palCoeur));
		}

		// Une pièce du kit centrée en `centre` (px canvas locaux), calée sur la
		// grille des px INTERNES, tracée niveau par niveau [n0..n1] en couleur de
		// rampe. Le niveau absent d'une pièce ne pose aucun pixel (masque vide).
		private void DrawPiece(Rect2I r, Vector2 centre, float z, Color[] rampe, int n0, int n1)
		{
			AssurerMasques();
			Vector2 coin = ((centre * z) - (Vector2)r.Size * 0.5f).Round() / z;
			var dst = new Rect2(coin, (Vector2)r.Size / z);
			for (int n = n0; n <= n1; n++)
				DrawTextureRectRegion(_kitMasques, dst,
					new Rect2(r.Position.X + n * _kitLargeur, r.Position.Y, r.Size.X, r.Size.Y), rampe[n]);
		}

		// Texture des masques : l'atlas des niveaux répété en bandes côte à côte,
		// bande n = blanc opaque là où le niveau vaut n. Construite une fois.
		private static void AssurerMasques()
		{
			if (_kitMasques != null) return;
			var niv = KitNiveaux;
			int w = niv.GetWidth(), h = niv.GetHeight();
			var img = Image.CreateEmpty(w * (KitCoeur + 1), h, false, Image.Format.Rgba8);
			for (int y = 0; y < h; y++)
				for (int x = 0; x < w; x++)
				{
					int n = (int)Mathf.Round(niv.GetPixel(x, y).R * 255f);
					if (n > 0) img.SetPixel(n * w + x, y, Colors.White);
				}
			_kitLargeur = w;
			_kitMasques = ImageTexture.CreateFromImage(img);
			// Codes indexés (③) : bande 0 = tout sauf le cœur, bande 1 = le cœur ;
			// texel = (1, 1, code, 1) → × modulate (palette, palette, 1, 1) = pixel encodé.
			var codes = Image.CreateEmpty(w * 2, h, false, Image.Format.Rgba8);
			for (int y = 0; y < h; y++)
				for (int x = 0; x < w; x++)
				{
					Color p = niv.GetPixel(x, y);
					int code = (int)Mathf.Round(p.G * 255f);
					if (code == 0) continue;
					bool coeur = (int)Mathf.Round(p.R * 255f) == KitCoeur;
					codes.SetPixel((coeur ? w : 0) + x, y, new Color(1f, 1f, code / 255f, 1f));
				}
			_kitCodes = ImageTexture.CreateFromImage(codes);
		}
	}
}
