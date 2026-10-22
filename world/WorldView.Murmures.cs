// SYMBIOSE — WorldView.Murmures.cs (partial de WorldView, sol qui respire ⑧)
// L'OVERDOSE : un 2ᵉ psychédélique pendant la vision, et TOUS les êtres parlent
// à la fois. Le pont joint à chaque snapshot la clé `voix` (absente sinon) :
// `{tuile: {plantes: [[x_cm, y_cm, [phrases]]], betes: [[espece, r, c, [..]]],
// champignons: [[espece, r, c, [..]]]}}`. La vue pose la 1ʳᵉ phrase de chaque être
// à l'écran, en petits murmures nets, comme des étiquettes.
//
// 📖 Pédagogie — garde-fou FPS : même mécanique que les étiquettes « Toutes »
// (Etiquettes.cs) — un POOL de Labels réutilisés sur la couche nette, reposés
// SEULEMENT quand la clé de survol change (souris, caméra, snapshot), jamais par
// frame au repos. On en montre au plus MaxMurmures, les plus proches de la
// souris : le regard choisit qui on écoute (et 500 phrases illisibles n'aident
// personne). Les mêmes phrases servent à l'info-bulle sans appel au pont.

using Godot;
using System.Collections.Generic;
using GDict = Godot.Collections.Dictionary;

namespace Symbiose
{
	public partial class WorldView : Node2D
	{
		private const int MaxMurmures = 24;
		// Phrases de l'overdose par clé d'être (cf. Vision.cs) + position MONDE (cm).
		private readonly Dictionary<string, string[]> _voixEtres = new();
		private readonly List<(Vector2 Monde, string Texte)> _murmures = new();
		private readonly List<Label> _murmurePool = new();
		private readonly List<(float D, int I)> _murmureTri = new();

		// Appelée à l'application du snapshot (Snapshot.cs). Clé absente = pas
		// d'overdose → tout se tait.
		private void LireVoix(GDict snap)
		{
			_voixEtres.Clear();
			_murmures.Clear();
			if (snap.ContainsKey("voix"))
				foreach (var (tk, tv) in snap["voix"].AsGodotDictionary())
				{
					string tile = tk.AsString();
					if (!_origins.TryGetValue(tile, out Vector2 o)) continue;
					var bloc = tv.AsGodotDictionary();
					foreach (var pv in bloc["plantes"].AsGodotArray())
					{
						var p = pv.AsGodotArray();
						double x = p[0].AsDouble(), y = p[1].AsDouble();
						Retenir(CleVoixPlante(tile, x, y), p[2].AsGodotArray(),
								o + new Vector2((float)x, (float)y));
					}
					foreach (string groupe in new[] { "betes", "champignons" })
					{
						int rang = 0;
						foreach (var ev in bloc[groupe].AsGodotArray())
						{
							var e = ev.AsGodotArray();
							int r = e[1].AsInt32(), c = e[2].AsInt32();
							// Plusieurs êtres au même plot : décalés en diagonale (lisibles).
							float dec = (rang++ % 4) * 9f;
							Retenir(CleVoixEtre(e[0].AsString(), tile, r, c), e[3].AsGodotArray(),
									o + new Vector2((c + 0.5f) * PlotCm + dec, (r + 0.5f) * PlotCm + dec));
						}
					}
				}
			_cleVersion = -1;   // repose les murmures (et l'info-bulle) à la frame suivante
		}

		private void Retenir(string cle, Godot.Collections.Array phrases, Vector2 monde)
		{
			if (phrases.Count == 0) return;
			var ph = new string[phrases.Count];
			for (int i = 0; i < ph.Length; i++) ph[i] = phrases[i].AsString();
			_voixEtres[cle] = ph;
			_murmures.Add((monde, ph[0]));
		}

		// Appelée chaque frame (_Process) ; travail seulement si la clé de survol a
		// changé. Les MaxMurmures êtres visibles les plus proches de la souris.
		private void UpdateMurmures()
		{
			if (_plantLabels == null || !_survolSale) return;
			int n = 0;
			if (_visionOverdose && _murmures.Count > 0)
			{
				Rect2 ecran = GetViewport().GetVisibleRect();
				_murmureTri.Clear();
				for (int i = 0; i < _murmures.Count; i++)
				{
					Vector2 px = WorldToWindow(WorldToScreen(_murmures[i].Monde.X, _murmures[i].Monde.Y));
					if (ecran.HasPoint(px)) _murmureTri.Add((px.DistanceSquaredTo(_sourisPx), i));
				}
				_murmureTri.Sort((a, b) => a.D.CompareTo(b.D));
				for (; n < _murmureTri.Count && n < MaxMurmures; n++)
				{
					var m = _murmures[_murmureTri[n].I];
					var lbl = MurmureDuPool(n);
					lbl.Text = m.Texte;
					lbl.Position = WorldToWindow(WorldToScreen(m.Monde.X, m.Monde.Y)) + new Vector2(-30f, -26f);
					lbl.Visible = true;
				}
			}
			for (int i = n; i < _murmurePool.Count; i++) _murmurePool[i].Visible = false;
		}

		private Label MurmureDuPool(int i)
		{
			while (_murmurePool.Count <= i)
			{
				var l = new Label();
				l.AddThemeFontSizeOverride("font_size", 11);
				l.AddThemeColorOverride("font_color", new Color(0.93f, 0.85f, 1f, 0.92f));
				l.AddThemeColorOverride("font_outline_color", new Color(0.12f, 0.05f, 0.2f));
				l.AddThemeConstantOverride("outline_size", 4);
				_plantLabels.AddChild(l);
				_murmurePool.Add(l);
			}
			return _murmurePool[i];
		}
	}
}
