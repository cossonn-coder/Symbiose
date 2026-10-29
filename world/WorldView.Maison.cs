// SYMBIOSE — WorldView.Maison.cs (partial de WorldView, T3 RENDU AMBIANCE)
// La MAISON du monde, extraite de WorldView.Monde (garde-fou taille : Monde
// gonflait). Ce partial CALCULE la géométrie de la maison depuis le snapshot
// (`house` : empreinte + hauteur) et l'orientation D35, puis DÉLÈGUE le rendu
// procédural détaillé (granite + ardoise + baies + cheminée) au nœud dédié
// HouseNode (visuals/HouseNode.cs). Il garde aussi l'OMBRE PORTÉE animée telle
// quelle (volet C) et le fantôme de transparence (touche H).
//
// 📖 D35 (façades indexées mur-monde) CONSERVÉ : les 4 coins sont projetés AVEC
// l'orientation courante (WorldToScreen), le coin « avant » = le plus bas écran
// (ancrage YSort), et l'index de mur (0 N, 1 E, 2 S, 3 O) sert l'éclairement
// dans HouseNode. La maison tourne donc proprement sous les 4 orientations, sans
// « sauter » (le fix du 1er F5 t4). Statique : dessinée au build (et rebuild
// rotation), jamais par frame → cohérent avec l'exclusion du vent (D72). Vue
// pure : aucun moteur touché, golden trivialement inchangé.

using Godot;
using GDict = Godot.Collections.Dictionary;

namespace Symbiose
{
	public partial class WorldView : Node2D
	{
		// Ombre portée (maison → nord). L'ombre EXACTE vit dans le champ lumière
		// Python ; ici c'est une enveloppe animée (volet C), teintée depuis Palette16.
		private static readonly Color OmbreColor = Palette16.Ombre;

		private Node2D _house;     // pour le mode transparent (touche H)
		// Ombre maison ANIMÉE (volet C) : le polygone est recalculé quand le
		// soleil bouge — paramètres gardés en champs pour ne pas relire le GDict.
		private Polygon2D _houseShadow;
		private float _hx0, _hy0, _hx1, _hy1, _hWallCm, _hHeightCm;

		// 📖 D112 ② « maison en verre » — trier un GROS objet parmi des petits.
		// "Objects" trie ses enfants par Y (pied = profondeur iso). La maison est
		// ancrée à son coin AVANT (le plus bas à l'écran) : tout ce qui a un pied plus
		// haut passe dessous. Juste DERRIÈRE elle, mais FAUX pour une plante plantée
		// devant un mur latéral : son pied est plus haut que le coin avant, elle
		// serait cachée par un mur qu'elle précède. Remède : la maison ET ce qui est
		// réellement derrière elle vivent un cran plus bas (ZIndex relatif −1, triés
		// entre eux par Y) ; tout le reste (devant, à côté) reste à 0 → toujours
		// dessiné par-dessus la maison. « Derrière » = pied au-dessus (à l'écran) du
		// PIED DES DEUX MURS CÔTÉ CAMÉRA, dans la largeur de la maison (± une marge
		// pour les houppiers qui débordent sur son bord). Pour deux objets dans la
		// même colonne d'écran, celui à ZIndex 0 est toujours le plus proche de
		// l'œil : l'ordre reste cohérent entre plantes.
		private const int ZDerriereMaison = -1;
		private const float MargeDerriereMaisonPx = 80f;   // ≈ 1 m de houppier débordant à ×1
		private Vector2[] _hBordAvant;   // pied des murs côté caméra : 3 coins écran triés en x

		/// <summary>ZIndex relatif d'un enfant de "Objects" dont le pied est au point
		/// MONDE (wx, wy) : ZDerriereMaison s'il est caché derrière la maison, sinon 0.</summary>
		private int ZObjet(float wx, float wy)
		{
			var b = _hBordAvant;
			if (b == null) return 0;
			Vector2 p = WorldToScreen(wx, wy);   // pied au sol, sans relief (comme les coins)
			if (p.X < b[0].X - MargeDerriereMaisonPx || p.X > b[2].X + MargeDerriereMaisonPx) return 0;
			float x = Mathf.Clamp(p.X, b[0].X, b[2].X);
			int i = x <= b[1].X ? 0 : 1;
			float dx = b[i + 1].X - b[i].X;
			float yBord = Mathf.Lerp(b[i].Y, b[i + 1].Y, dx > 0f ? (x - b[i].X) / dx : 0f);
			return p.Y < yBord ? ZDerriereMaison : 0;
		}

		// -------------------------------------------------------------------
		// MAISON — normande granite + ardoise (rendu délégué à HouseNode).
		// On lit l'empreinte au sol + la hauteur du snapshot, on projette les 4
		// coins (D35), on calcule le haut de mur et le FAÎTE (segment, pour un
		// toit à 2 pans + croupe pentu), puis on pose la géométrie sur le nœud.
        // -------------------------------------------------------------------
		private void BuildHouse(GDict world)
		{
			var h = world["house"].AsGodotDictionary();
			var fp = h["footprint_cm"].AsGodotArray();   // [x0, y0, x1, y1]
			float x0 = (float)fp[0].AsDouble(), y0 = (float)fp[1].AsDouble();
			float x1 = (float)fp[2].AsDouble(), y1 = (float)fp[3].AsDouble();
			float heightCm = (float)h["height_cm"].AsDouble();
			float hPx = heightCm * PxPerCmZ;

			// Murs à ~62 % de la hauteur → le toit occupe le reste : forte pente
			// d'ardoise (> 45°) comme au Cotentin (le placeholder était à 66 %,
			// toit plus plat). Le faîte monte à height_cm.
			float wallCm = heightCm * 0.62f;

			// Les 4 coins au sol, cycle HORAIRE monde nw→ne→se→sw, projetés AVEC
			// l'orientation courante. Mur i = entre coins i et i+1 : 0 nord, 1 est,
			// 2 sud, 3 ouest — le MÊME index lit l'éclairement monde dans HouseNode :
			// c'est ce qui fait visiblement tourner la maison. Le coin « avant » =
			// le plus BAS à l'écran (le plus proche caméra) : ancrage YSort.
			Vector2[] scr =
			{
				WorldToScreen(x0, y0), WorldToScreen(x1, y0),
				WorldToScreen(x1, y1), WorldToScreen(x0, y1),
			};
			int front = 0;
			for (int i = 1; i < 4; i++)
				if (scr[i].Y > scr[front].Y) front = i;

			Vector2 anchor = scr[front];
			_house = new Node2D { Name = "House", Position = anchor, ZIndex = ZDerriereMaison };
			// Pied des 2 murs côté caméra = coin avant + ses 2 voisins (cf. ZObjet).
			_hBordAvant = new[] { scr[(front + 3) % 4], scr[front], scr[(front + 1) % 4] };
			System.Array.Sort(_hBordAvant, (a, b) => a.X.CompareTo(b.X));

			// Coins locaux au nœud + vecteur haut-de-mur.
			var c = new Vector2[4];
			for (int i = 0; i < 4; i++) c[i] = scr[i] - anchor;
			Vector2 upWall = new Vector2(0f, -wallCm * PxPerCmZ);

			// FAÎTE = segment horizontal (monde) reliant les milieux des 2 murs
			// PIGNON. Un toit à long pan a son faîte parallèle au faîtage : on le
			// pose sur l'axe le plus LONG de l'empreinte (les pignons sont les
			// petits côtés). Le faîte est à height_cm au-dessus du sol.
			bool longEastWest = (x1 - x0) >= (y1 - y0);
			Vector2 ridgeUp = new Vector2(0f, -hPx);
			Vector2 apexA, apexB;
			if (longEastWest)
			{
				// pignons = murs est/ouest → faîte le long de X, à mi-Y.
				apexA = WorldToScreen(x0, (y0 + y1) / 2f) - anchor + ridgeUp;
				apexB = WorldToScreen(x1, (y0 + y1) / 2f) - anchor + ridgeUp;
			}
			else
			{
				apexA = WorldToScreen((x0 + x1) / 2f, y0) - anchor + ridgeUp;
				apexB = WorldToScreen((x0 + x1) / 2f, y1) - anchor + ridgeUp;
			}

			// Mur-monde OUEST (index 3) porte le pignon essenté d'ardoise (exposé
			// au vent d'ouest). HouseNode gère l'ordre peintre et le détail.
			var node = new HouseNode();
			node.Setup(c, upWall, apexA, apexB, front, westWall: 3);
			_house.AddChild(node);

			_objects.AddChild(_house);
			ApplyHouseGhost();   // ré-applique la transparence après un rebuild

			// Ombre portée ANIMÉE (volet C) : polygone recalculé par
			// UpdateHouseShadow quand le soleil bouge. Posée dans _ground : sous
			// tous les objets, par-dessus les plots, reconstruite avec la rotation.
			_houseShadow = new Polygon2D { Color = OmbreColor };
			_ground.AddChild(_houseShadow);
			(_hx0, _hy0, _hx1, _hy1) = (x0, y0, x1, y1);
			(_hWallCm, _hHeightCm) = (wallCm, heightCm);
			UpdateHouseShadow();

			GD.Print($"[WorldView] maison normande : empreinte "
					 + $"[{x0},{y0}]→[{x1},{y1}] cm, h={heightCm} cm (murs {wallCm} cm).");
		}
	}
}
