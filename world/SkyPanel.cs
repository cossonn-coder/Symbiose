// SYMBIOSE — SkyPanel.cs (encart « état du ciel », sprint effondrement météo ④)
// La FENÊTRE DIÉGÉTIQUE sur le ciel : un petit encart, coin haut-droit, qui condense
// ce que le joueur peut LIRE du ciel de la semaine (bloc `ciel` du snapshot, protocole
// 0.5.43, équivalent Python `sim/ciel.py`). PAS un widget de prévision chiffrée
// (« Semaine +1 : 70 % » = INTERDIT, philo #5) : couleur du fond, bancs de nuages,
// halo laiteux, brume basse — le joueur lit le ciel comme un vrai jardinier. L'encart
// S'ASSOMBRIT VISIBLEMENT (vire au plomb) à l'approche du COMPOSÉ catastrophe (la
// `convergence` de ②) → le préavis dramatique rendu perceptible AVANT la frappe.
//
// Masque de maîtrise (§4.2) : l'encart montre TOUJOURS le ciel (signal parfait) ;
// ce qui dépend du palier météo, c'est s'il le NOMME. Le nommage est déjà gaté CÔTÉ
// MOTEUR (`ciel.nom_compose` n'est joint qu'au palier ≥ seuil) : Godot reste bête, il
// affiche le nom s'il est là, rien sinon. Le libellé PERCEPTIF (« le ciel se plombe »)
// est, lui, toujours montré dès qu'un composé approche.
//
// 📖 Pédagogie Godot — comme WeatherLayer : un CanvasLayer (coordonnées ÉCRAN, ignore
// la caméra) tient un Node2D peintre (le CanvasLayer ne sait pas _Draw) + un Label
// pour le texte net. Positions/nuages dérivés d'un HASH d'indice → stables, jamais de
// Random (philo #3). L'encart ne calcule aucune météo : il PEINT la donnée du pont.

using Godot;
using GDict = Godot.Collections.Dictionary;

namespace Symbiose
{
	public partial class SkyPanel : CanvasLayer
	{
		private SkyVignette _vignette;
		private Label _readLabel;    // perceptif (toujours) — ce que le ciel donne à voir
		private Label _nameLabel;    // interprétation NOMMÉE (gatée maîtrise) — ou vide

		public override void _Ready()
		{
			Layer = 2;   // au-dessus de l'ambiance météo (1) et du monde, avec le HUD
			_vignette = new SkyVignette { Name = "Vignette" };
			AddChild(_vignette);

			// Deux libellés nets SOUS la vignette (le texte dans la grille pixel-art est
			// illisible → on le pose en clair, comme les étiquettes hors SubViewport).
			_readLabel = MakeLabel(20, new Color(0.94f, 0.96f, 1f));
			_nameLabel = MakeLabel(18, new Color(1f, 0.86f, 0.55f));   // ambre = savoir
			AddChild(_readLabel);
			AddChild(_nameLabel);
			LayoutLabels();
		}

		private static Label MakeLabel(int size, Color color)
		{
			var l = new Label
			{
				HorizontalAlignment = HorizontalAlignment.Right,
				AutowrapMode = TextServer.AutowrapMode.WordSmart,
				CustomMinimumSize = new Vector2(SkyVignette.PanelW, 0f),
			};
			l.AddThemeFontSizeOverride("font_size", size);
			l.AddThemeColorOverride("font_color", color);
			l.AddThemeColorOverride("font_outline_color", Colors.Black);
			l.AddThemeConstantOverride("outline_size", 6);
			return l;
		}

		// Ancrage coin haut-droit : la vignette peint à droite (SkyVignette calcule son
		// rect au viewport), les labels s'alignent sous elle sur la même colonne.
		private void LayoutLabels()
		{
			float w = SkyVignette.PanelW, m = SkyVignette.MarginPx;
			float right = GetViewport().GetVisibleRect().Size.X - m - w;
			float top = SkyVignette.TopPx + SkyVignette.PanelH + 6f;
			_readLabel.Position = new Vector2(right, top);
			_readLabel.Size = new Vector2(w, 0f);
			_nameLabel.Position = new Vector2(right, top + 30f);
			_nameLabel.Size = new Vector2(w, 0f);
		}

		/// <summary>
		/// Applique le bloc `ciel` d'un snapshot (0.5.43). Lecture TOLÉRANTE : un binaire
		/// pré-0.5.43 n'appelle jamais ceci (clé absente) → encart neutre, aucun crash.
		/// </summary>
		public void SetSky(GDict ciel)
		{
			float nebul = ciel.ContainsKey("nebulosite")
				? (float)ciel["nebulosite"].AsDouble() : 0.1f;
			float conv = ciel.ContainsKey("convergence")
				? (float)ciel["convergence"].AsDouble() : 0f;
			string evenement = ciel.ContainsKey("evenement_courant")
				? ciel["evenement_courant"].AsString() : "";
			var compose = ciel.ContainsKey("signe_compose")
				? ciel["signe_compose"].AsGodotArray() : new Godot.Collections.Array();
			string nom = ciel.ContainsKey("nom_compose")
						 && ciel["nom_compose"].VariantType != Variant.Type.Nil
				? ciel["nom_compose"].AsString() : null;

			_vignette.SetSky(nebul, conv, evenement, compose.Count > 0);

			// Ligne PERCEPTIVE (toujours) : le libellé intensifié du composé s'il
			// approche (le ciel « se plombe » pour tous, §5), sinon une lecture sobre
			// du fond de ciel (pure observation, jamais un nommage d'événement).
			_readLabel.Text = compose.Count > 0
				? compose[compose.Count / 2].AsString()   // le libellé médian, franc
				: SkyRead(nebul);

			// Ligne NOMMÉE (gatée maîtrise, côté moteur) : le nom du composé si le pont
			// l'a joint ; vide sinon → l'encart reste BRUT sous le palier (§4.2).
			_nameLabel.Text = nom != null ? nom : "";
		}

		// Lecture SOBRE du ciel de fond ∝ nébulosité — observation, pas interprétation
		// (aucun événement nommé ici : le nommage est gaté par la maîtrise).
		private static string SkyRead(float nebul)
		{
			if (nebul < 0.20f) return "ciel dégagé";
			if (nebul < 0.45f) return "ciel voilé";
			if (nebul < 0.70f) return "ciel couvert";
			return "ciel bas et lourd";
		}
	}

	// Le peintre : un cartouche de ciel (fond dégradé + nuages + halo + brume) qui
	// vire au plomb ∝ convergence, en pixels écran. Coin haut-droit, taille fixe.
	public partial class SkyVignette : Node2D
	{
		public const float PanelW = 240f;
		public const float PanelH = 150f;
		public const float MarginPx = 16f;
		public const float TopPx = 100f;   // sous le témoin de version (haut-droit)

		// Pôles de teinte du fond de ciel. Le clair (jour bleu) vire au gris couvert
		// avec la nébulosité, puis au PLOMB (gris-violet sourd) avec la convergence.
		private static readonly Color SkyClear   = new Color(0.53f, 0.72f, 0.92f);
		private static readonly Color SkyOvercast = new Color(0.62f, 0.64f, 0.68f);
		private static readonly Color SkyLeaden  = new Color(0.24f, 0.23f, 0.29f);
		// Convergence de RÉFÉRENCE = seuil du composé (sim/ciel.COMPOSE_SEUIL) : à ce
		// niveau, l'encart est PLEINEMENT au plomb. Calibrage F5 (miroir du seuil moteur).
		private const float ConvRef = 1.8f;

		private float _nebul, _conv;
		private bool _compose;
		private string _evenement = "";

		// Transition douce (comme le voile de WeatherLayer) : les cibles glissent, pas
		// de saut brutal au changement de semaine.
		private float _nebCur, _convCur;

		public void SetSky(float nebul, float conv, string evenement, bool compose)
		{
			_nebul = Mathf.Clamp(nebul, 0f, 1f);
			_conv = Mathf.Max(0f, conv);
			_evenement = evenement ?? "";
			_compose = compose;
			QueueRedraw();
		}

		public override void _Process(double delta)
		{
			float d = (float)delta;
			bool moving = false;
			if (!Mathf.IsEqualApprox(_nebCur, _nebul))
			{ _nebCur = Mathf.MoveToward(_nebCur, _nebul, d * 1.2f); moving = true; }
			float convTarget = Mathf.Clamp(_conv / ConvRef, 0f, 1f);
			if (!Mathf.IsEqualApprox(_convCur, convTarget))
			{ _convCur = Mathf.MoveToward(_convCur, convTarget, d * 0.9f); moving = true; }
			if (moving) QueueRedraw();
		}

		public override void _Draw()
		{
			float vw = GetViewport().GetVisibleRect().Size.X;
			var rect = new Rect2(vw - MarginPx - PanelW, TopPx, PanelW, PanelH);

			// Cadre (pierre sombre) : un liseré qui détache l'encart du jardin.
			DrawRect(rect.Grow(3f), new Color(0.08f, 0.08f, 0.10f, 0.85f));

			// Fond de ciel : dégradé vertical (haut plus clair, horizon plus dense) —
			// approché par quelques bandes horizontales lerp. Teinte = clair→couvert
			// (nébulosité) puis →plomb (convergence).
			Color baseSky = SkyClear.Lerp(SkyOvercast, _nebCur);
			Color sky = baseSky.Lerp(SkyLeaden, _convCur * 0.9f);
			const int bands = 10;
			for (int i = 0; i < bands; i++)
			{
				float t = i / (float)(bands - 1);
				// Horizon (bas) un cran plus sombre → profondeur.
				Color c = sky.Darkened(0.12f * t);
				var band = new Rect2(rect.Position.X, rect.Position.Y + t * PanelH,
									 PanelW, PanelH / bands + 1f);
				DrawRect(band, c);
			}

			// Halo laiteux : un soleil/lune pâle et son anneau diffus quand le ciel est
			// VOILÉ (nébulosité moyenne) — signe météo classique (anneau lunaire, §4).
			if (_nebCur > 0.18f && _nebCur < 0.72f)
			{
				Vector2 sun = rect.Position + new Vector2(PanelW * 0.72f, PanelH * 0.30f);
				float halo = 1f - Mathf.Abs(_nebCur - 0.45f) / 0.27f;   // pic à 0.45
				var pale = new Color(1f, 0.98f, 0.90f, 0.10f + 0.14f * halo);
				DrawCircle(sun, 26f, pale);                // anneau diffus
				DrawCircle(sun, 9f, new Color(1f, 0.99f, 0.93f, 0.55f));   // disque
			}

			// Bancs de nuages : ellipses sombres, plus NOMBREUSES et plus SOURDES avec
			// la nébulosité ET la convergence. Positions par HASH (stables, no Random).
			int nClouds = Mathf.RoundToInt(1 + 7 * Mathf.Clamp(_nebCur + _convCur * 0.5f, 0f, 1f));
			Color cloud = new Color(0.36f, 0.37f, 0.42f).Lerp(SkyLeaden, _convCur);
			cloud.A = 0.35f + 0.45f * Mathf.Clamp(_nebCur + _convCur, 0f, 1f);
			for (int i = 0; i < nClouds; i++)
			{
				uint h = Hash((uint)i);
				float cx = (h & 0xffff) / 65536f * PanelW;
				float cy = ((h >> 16) & 0xff) / 255f * PanelH * 0.6f;   // moitié haute
				float rw = 24f + ((h >> 24) & 0xff) / 255f * 26f;
				DrawEllipse(rect.Position + new Vector2(cx, cy), rw, rw * 0.42f, cloud);
			}

			// Brume basse : une bande translucide qui monte de l'horizon quand le ciel
			// est chargé (nébulosité haute) OU qu'un composé plombe l'air.
			float brume = Mathf.Clamp((_nebCur - 0.4f) / 0.6f + _convCur * 0.5f, 0f, 1f);
			if (brume > 0.02f)
			{
				var haze = new Color(0.80f, 0.82f, 0.85f, 0.30f * brume);
				float hh = PanelH * (0.20f + 0.20f * brume);
				DrawRect(new Rect2(rect.Position.X, rect.End.Y - hh, PanelW, hh), haze);
			}

			// Frappe imminente : liseré rouge sourd qui bat quand un composé approche —
			// l'urgence sans chiffre ni icône (le cadre « respire »).
			if (_compose)
			{
				float pulse = 0.35f + 0.35f * Mathf.Sin(Time.GetTicksMsec() / 260f);
				DrawRect(rect, new Color(0.55f, 0.10f, 0.10f, pulse), filled: false, width: 3f);
				QueueRedraw();   // entretient le battement
			}
		}

		// Ellipse pleine par triangulation en éventail (Godot n'a pas de DrawEllipse
		// rempli natif) : un disque unité mis à l'échelle rx·ry.
		private void DrawEllipse(Vector2 c, float rx, float ry, Color col)
		{
			const int seg = 16;
			var pts = new Vector2[seg + 2];
			pts[0] = c;
			for (int i = 0; i <= seg; i++)
			{
				float a = i / (float)seg * Mathf.Tau;
				pts[i + 1] = c + new Vector2(Mathf.Cos(a) * rx, Mathf.Sin(a) * ry);
			}
			DrawColoredPolygon(pts, col);
		}

		// Hash djb2-xor (même choix que WeatherLayer/LitterLayer : visuel stable).
		private static uint Hash(uint i)
		{
			uint h = 5381u;
			h = ((h << 5) + h) ^ (i & 0xff);
			h = ((h << 5) + h) ^ ((i >> 8) & 0xff);
			return h;
		}
	}
}
