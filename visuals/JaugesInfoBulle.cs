// SYMBIOSE — JaugesInfoBulle.cs (sprint CASSÉ À L'ÉCRAN ②, D112 (e))
// Les JAUGES du mode technique de l'info-bulle (Maj+F3) : une barre fine par
// valeur, dessinée à droite de sa ligne de texte, au lieu de chiffres seuls.
//
// 📖 Pédagogie — une jauge se lit d'un coup d'œil si elle a TOUJOURS le même sens.
// Chaque valeur est donc convertie par l'appelant en « MAL » ∈ [0,1] (0 = tout va
// bien, 1 = au pire) — le « bon » dépend de la valeur, le sens par clé est écrit
// là où la jauge est posée (WorldView.InfoBulle.cs / InfoBulleVivant.cs) :
//   - la barre se remplit de GAUCHE à droite avec le mal, et sa couleur glisse du
//     VERT (bon) au ROUGE (mauvais) — sens fixe, quelle que soit la valeur ;
//   - un REPÈRE vertical marque le seuil de visibilité du signe : à gauche du
//     repère, le dessin ne montre encore rien (le carnet se tait aussi) ;
//   - une PASTILLE à gauche porte la couleur du champ F6 lié (FieldOverlay
//     .Palettes, pôle haut) : même champ = même couleur que la heatmap ;
//   - un mot léger / marqué / grave (MotDe) est écrit dans la ligne, et le
//     chiffre brut y reste (en petit, entre parenthèses) : rien n'est retiré.
// Philo #5 : c'est l'AFFICHAGE TECHNIQUE (mention gardée en tête de bulle).
//
// Le nœud est un enfant du Label de l'info-bulle : il lit son texte et sa police
// pour placer les barres (une colonne alignée sur la plus longue ligne jaugée).
// Aucun calcul de jeu : la vue ne fait que projeter ce que le snapshot donne.

using Godot;
using System.Collections.Generic;

namespace Symbiose
{
	public partial class JaugesInfoBulle : Control
	{
		private const float LargeurPx = 64f;     // longueur d'une jauge à l'écran
		private const float EpaisseurPx = 2f;    // « une ligne de pixels », lisible en 1080p
		private const float RepereHautPx = 6f;   // le repère de seuil dépasse la barre
		private const float PastillePx = 4f;
		private const float MargePx = 8f;        // entre le texte et la colonne de jauges

		private static readonly Color Vert = new("4f9f4f"), Rouge = new("c43a2e");
		private static readonly Color Piste = new(0.15f, 0.15f, 0.17f, 0.8f);
		private static readonly Color Repere = new(0.95f, 0.95f, 0.9f);

		// Une jauge = la ligne du Label qu'elle accompagne, son mal, son seuil
		// (même échelle que le mal, NaN = pas de seuil) et sa pastille de champ.
		private readonly List<(int Ligne, float Mal, float Seuil, Color? Pastille)> _jauges = new();

		public JaugesInfoBulle() { MouseFilter = MouseFilterEnum.Ignore; }

		/// <summary>Mot du mal : sous ⅓ « léger », sous ⅔ « marqué », sinon « grave ».</summary>
		public static string MotDe(float mal) => mal < 1f / 3f ? "léger" : mal < 2f / 3f ? "marqué" : "grave";

		/// <summary>Couleur de pastille du champ F6 `champ` (pôle haut), null si le
		/// champ n'a pas de palette (aucune heatmap à rappeler).</summary>
		public static Color? PastilleDe(string champ)
			=> champ != null && FieldOverlay.APalette(champ) ? FieldOverlay.PaletteOf(champ).High : null;

		public void Vider() { _jauges.Clear(); QueueRedraw(); }

		public void Ajouter(int ligne, float mal, float seuil, Color? pastille)
		{
			_jauges.Add((ligne, Mathf.Clamp(mal, 0f, 1f), seuil, pastille));
			QueueRedraw();
		}

		public override void _Draw()
		{
			if (_jauges.Count == 0 || GetParent() is not Label label) return;
			Font font = label.GetThemeFont("font");
			int taille = label.GetThemeFontSize("font_size");
			float hLigne = font.GetHeight(taille) + label.GetThemeConstant("line_spacing");
			string[] lignes = label.Text.Split('\n');
			// Colonne : à droite de la plus longue ligne JAUGÉE (la mention technique,
			// longue, n'en porte pas → elle ne repousse pas la colonne).
			float x0 = 0f;
			foreach (var j in _jauges)
				if (j.Ligne < lignes.Length)
					x0 = Mathf.Max(x0, font.GetStringSize(lignes[j.Ligne], HorizontalAlignment.Left, -1, taille).X);
			x0 += MargePx;
			foreach (var (ligne, mal, seuil, pastille) in _jauges)
			{
				float y = ligne * hLigne + font.GetHeight(taille) * 0.5f;
				float x = x0;
				if (pastille is Color p)
					DrawRect(new Rect2(x, y - PastillePx * 0.5f, PastillePx, PastillePx), p);
				x += PastillePx + 3f;
				DrawRect(new Rect2(x, y - EpaisseurPx * 0.5f, LargeurPx, EpaisseurPx), Piste);
				if (mal > 0f)
					DrawRect(new Rect2(x, y - EpaisseurPx * 0.5f, Mathf.Max(1f, mal * LargeurPx), EpaisseurPx),
							 Vert.Lerp(Rouge, mal));
				if (!float.IsNaN(seuil))
				{
					float xs = x + Mathf.Clamp(seuil, 0f, 1f) * LargeurPx;
					DrawRect(new Rect2(xs, y - RepereHautPx * 0.5f, 1f, RepereHautPx), Repere);
				}
			}
		}
	}
}
