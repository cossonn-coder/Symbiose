// SYMBIOSE — WorldView.BancSeuil.cs (partial de WorldView, INFO-BULLE DU VIVANT ②)
// BANC VM du SEUIL DE VISIBILITÉ d'un signe (conception_infobulle_vivant.md §2.5) :
// à partir de quelle intensité la teinte d'un symptôme change-t-elle RÉELLEMENT au
// moins un pixel de l'écran ? Le texte de l'info-bulle ne doit dire que ce que le
// dessin montre — c'est ce banc qui fixe les constantes PlantRenderer.SeuilTeinte*.
//
// Deux modes (arguments après `--`, lancés par sprints/…/mesures/mesure_seuil.sh) :
//   --capture-seuil=<cause|toutes>  balayage : pour chaque cause (colorantes +
//       "vitalite" + "automne"), chaque palier ×2/×4/×8 et chaque intensité de
//       SeuilGrille, l'état est posé sur la plante témoin (la plus proche du point
//       visé), puis l'image ÉCRAN est relue et comparée pixel à pixel à celle de
//       i = 0 du même palier → « [Seuil] cause ×Z i=… px=N ». Puis le jeu quitte.
//   --capture-seuil-pose=<cause>,<i>  pose seule à ×4, souris sur la témoin (info-
//       bulle visible), recadrage PNG sauvé dans --capture-seuil-png=<chemin>.
//   --capture-palette=1  palette SNES (F11) allumée : la mesure passe alors par la
//       quantification 34 couleurs + Bayer du shader.
//
// 📖 Pédagogie Godot : GetViewport().GetTexture().GetImage() relit l'écran FINAL
// (monde + shader de palette + HUD) en RAM CPU — lent (bloquant) mais exact : on
// mesure la vraie image, pas un modèle de la chaîne de couleurs. Le HUD et les
// étiquettes ne bougent pas pendant le balayage (planification, temps figé) ; le
// 2ᵉ « i = 0 » de la grille mesure ce bruit (attendu 0 px). `--fixed-fps` rend
// les minuteries déterministes (1 frame = 1/fps s de jeu, quel que soit le CPU).

using Godot;
using System.Collections.Generic;
using System.Globalization;

namespace Symbiose
{
	public partial class WorldView
	{
		private static readonly string CaptureSeuil = ArgCapture("seuil");
		private static readonly string CaptureSeuilPose = ArgCapture("seuil-pose");
		private static readonly string CaptureSeuilPng = ArgCapture("seuil-png");
		private static readonly bool CapturePalette = ArgCapture("palette") == "1";

		// Intensités balayées (le 2ᵉ zéro = contrôle du bruit) et paliers où la teinte
		// de santé est dite visible (PalierSanteZoom ×2 → ×8, au-delà même dessin).
		private static readonly float[] SeuilGrille =
			{ 0f, 0f, 0.005f, 0.01f, 0.02f, 0.03f, 0.05f, 0.075f, 0.1f, 0.15f, 0.2f, 0.3f, 0.5f };
		private static readonly float[] SeuilPaliers = { 2f, 4f, 8f };
		private const float SeuilPasSec = 0.4f;      // tenue d'une intensité (recuisson)
		private const float SeuilPalierSec = 5f;     // tenue au changement de palier

		private PlantRenderer _seuilTemoin;
		private Image _seuilRef;
		private Rect2I _seuilCadre;   // emprise écran de la témoin, figée par palier

		// Appelé en fin d'AppliquerCapture (caméra posée sur le point visé).
		private void LancerBancSeuil()
		{
			if (CapturePalette && !PaletteSnes.Actif) PaletteSnes.Basculer();
			if (CaptureSeuil == null && CaptureSeuilPose == null) return;
			_seuilTemoin = FindPlant(ScreenToWorld(_camera.Position), 1e5f);
			if (_seuilTemoin == null) { GD.Print("[Seuil] aucune plante."); GetTree().Quit(); return; }
			string sp = _seuilTemoin.GetMeta(LectureSnap.Meta("species"), "?").AsString();
			GD.Print($"[Seuil] témoin {sp} en {_seuilTemoin.Position} · palette SNES {(PaletteSnes.Actif ? "ON" : "OFF")}");
			if (CaptureSeuilPose != null) { PoserSeuil(); return; }
			var causes = new List<string>();
			if (CaptureSeuil == "toutes")
			{
				causes.AddRange(PlantRenderer.CausesColorantes);
				causes.Add("vitalite");
				causes.Add("automne");
			}
			else causes.Add(CaptureSeuil);
			var pas = new List<(string Cause, float Zoom, float I)>();
			foreach (var c in causes)
				foreach (var z in SeuilPaliers)
					foreach (var i in SeuilGrille) pas.Add((c, z, i));
			SeuilEtape(pas, 0);
		}

		private void SeuilEtape(List<(string Cause, float Zoom, float I)> pas, int k)
		{
			if (k >= pas.Count || !IsInstanceValid(_seuilTemoin))
			{
				GD.Print("[Seuil] fin du balayage.");
				GetTree().Quit();
				return;
			}
			var (cause, zoom, i) = pas[k];
			bool nouveauPalier = k == 0 || pas[k - 1].Zoom != zoom || pas[k - 1].Cause != cause;
			if (nouveauPalier)
				PoserCamera(System.Array.IndexOf(ZoomSteps, zoom), _seuilTemoin.EmpriseCanvas.GetCenter());
			_seuilTemoin.ForcerEtatBanc(cause, i);
			GetTree().CreateTimer(nouveauPalier ? SeuilPalierSec : SeuilPasSec).Timeout += () =>
			{
				if (nouveauPalier) _seuilCadre = CadreTemoin();
				var img = GetViewport().GetTexture().GetImage().GetRegion(_seuilCadre);
				if (nouveauPalier) _seuilRef = img;
				int px = nouveauPalier ? 0 : PixelsDifferents(_seuilRef, img);
				GD.Print(string.Create(CultureInfo.InvariantCulture,
					$"[Seuil] {cause} ×{zoom} i={i:0.###} px={px}"));
				SeuilEtape(pas, k + 1);
			};
		}

		// Emprise écran de la témoin (+ 2 px), prise à l'état sain du palier et FIGÉE
		// pour tout le palier : les voisines qui finissent leur recuisson n'entrent pas
		// au compte, et les deux images comparées ont la même taille.
		private Rect2I CadreTemoin()
		{
			Rect2 e = _seuilTemoin.EmpriseCanvas;
			Vector2 a = WorldToWindow(e.Position), b = WorldToWindow(e.End);
			return new Rect2I((int)a.X - 2, (int)a.Y - 2, (int)(b.X - a.X) + 4, (int)(b.Y - a.Y) + 4)
				.Intersection(new Rect2I(Vector2I.Zero, (Vector2I)GetViewport().GetTexture().GetSize()));
		}

		// Nombre de pixels dont au moins un canal RVB diffère (format RGB(A)8).
		private static int PixelsDifferents(Image a, Image b)
		{
			byte[] da = a.GetData(), db = b.GetData();
			if (da.Length != db.Length) return -1;
			int pas = a.GetFormat() == Image.Format.Rgba8 ? 4 : 3, n = 0;
			for (int p = 0; p + 2 < da.Length; p += pas)
				if (da[p] != db[p] || da[p + 1] != db[p + 1] || da[p + 2] != db[p + 2]) n++;
			return n;
		}

		// Pose seule (captures avant/après de l'info-bulle) : ×4, souris sur la
		// témoin, puis recadrage 640×400 autour d'elle sauvé en PNG.
		private void PoserSeuil()
		{
			string[] a = CaptureSeuilPose.Split(',');
			float i = a.Length > 1 ? ParseFloat(a[1]) : 0f;
			PoserCamera(System.Array.IndexOf(ZoomSteps, 4f), _seuilTemoin.EmpriseCanvas.GetCenter());
			_seuilTemoin.ForcerEtatBanc(a[0], i);
			GetTree().CreateTimer(SeuilPalierSec).Timeout += () =>
			{
				Vector2 px = WorldToWindow(_seuilTemoin.Position);
				Input.WarpMouse(px);
				ResemerSouris();
				GetTree().CreateTimer(1.0).Timeout += () =>
				{
					var img = GetViewport().GetTexture().GetImage();
					var r = new Rect2I((int)px.X - 320, (int)px.Y - 240, 640, 400)
						.Intersection(new Rect2I(Vector2I.Zero, img.GetSize()));
					if (CaptureSeuilPng != null) img.GetRegion(r).SavePng(CaptureSeuilPng);
					GD.Print($"[Seuil] pose {CaptureSeuilPose} → {CaptureSeuilPng} · info-bulle « {_infoBulle?.Text} »");
					GetTree().Quit();
				};
			};
		}
	}
}
