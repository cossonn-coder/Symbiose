// SYMBIOSE — WorldView.Vision.cs (partial de WorldView, sol qui respire ⑧)
// La VISION côté vue, une semaine après un champignon psychédélique (moteur :
// `sim/vision.py`, pont 0.5.54) :
//   - les couleurs s'avivent (post-traitement plein écran, PaletteSnes.Vision) ;
//   - l'info-bulle PARLE : à l'ENTRÉE du survol d'un être (plante, bête,
//     champignon), la vue demande ses phrases au pont (`parler`) et les ajoute
//     sous la ligne habituelle. Le nom et la comestibilité s'affichent déjà :
//     pendant la vision Python lit `player.appris` au palier transcendant ;
//   - l'OVERDOSE (2ᵉ psychédélique pendant l'effet) : le snapshot porte les
//     phrases de TOUS les êtres (`voix`) → murmures à l'écran (Murmures.cs) ;
//   - à la fin, ce qui RESTE (`player.vision.reste`) est annoncé une fois.
//
// 📖 Pédagogie — pourquoi `parler` est ASYNCHRONE (Task) alors que `observer` est
// synchrone : `parler` arrive pendant le jeu en saison, où un step de semaine
// (~1 s) peut tenir le tube ; un appel synchrone gèlerait la frame jusqu'à sa fin.
// La Task attend son tour sur le verrou du pont, la frame continue ; la réponse
// est consommée plus tard (MajVision) si la souris est toujours sur le même être.
// Un appel par ENTRÉE de survol (clé d'être), jamais par frame : le pont compte
// chaque appel comme un survol (ce qui reste après la vision).

using Godot;
using System.Collections.Generic;
using System.Text;
using System.Threading.Tasks;
using GDict = Godot.Collections.Dictionary;

namespace Symbiose
{
	public partial class WorldView : Node2D
	{
		private bool _visionActive, _visionOverdose;
		// Banc VM (Capture.cs) : `--capture-vision=1|2` impose l'effet d'écran pour
		// le regarder sans manger de champignon. Absent (NaN) = jeu normal.
		private static readonly float CaptureVision = ParseFloat(ArgCapture("vision"));
		// Être survolé courant (clé) et ses phrases (null = pas encore reçues).
		private string _parlerCle;
		private string[] _parlerPhrases;
		// `parler` en vol : clé + Task ; une seule à la fois (la suivante attend).
		private string _parlerEnVolCle;
		private Task<GDict> _parlerEnVol;
		private GDict _parlerEnAttente;   // cible de la dernière entrée non envoyée
		private string _parlerEnAttenteCle;

		// Appelée à l'application du bloc joueur (Snapshot.cs). Tolérante : pont
		// pré-0.5.54 → pas de clé → jamais de vision.
		private void LireVision(GDict pl)
		{
			bool avant = _visionActive;
			_visionActive = _visionOverdose = false;
			if (pl.ContainsKey("vision"))
			{
				var v = pl["vision"].AsGodotDictionary();
				_visionActive = v.ContainsKey("active") && v["active"].AsBool();
				_visionOverdose = _visionActive && v.ContainsKey("overdose") && v["overdose"].AsBool();
				if (v.ContainsKey("reste")) AnnoncerReste(v["reste"].AsGodotArray());
			}
			PaletteSnes.Vision(!float.IsNaN(CaptureVision) ? CaptureVision
							   : _visionOverdose ? 2f : _visionActive ? 1f : 0f);
			if (_visionActive != avant)
			{
				_parlerCle = null; _parlerPhrases = null;   // on reparle au prochain survol
				_cleVersion = -1;
				// Le message du geste (Python) dit déjà ce qu'on ressent : on ne
				// l'écrase pas, on trace seulement la bascule.
				GD.Print($"[WorldView] vision {(_visionActive ? (_visionOverdose ? "OVERDOSE" : "ON") : "OFF")}.");
			}
		}

		// Ce qui reste de la vision (clés gagnées), consommé par le pont → dit une fois.
		private void AnnoncerReste(Godot.Collections.Array reste)
		{
			if (reste.Count == 0) return;
			var noms = new List<string>();
			foreach (var k in reste) noms.Add(k.AsString().Replace('_', ' '));
			_lastActionMsg = "la vision s'est dissipée ; il m'en reste quelque chose : "
							 + string.Join(", ", noms);
			FlashActionLabel();
		}

		// Appelée par UpdateInfoBulle (clé de survol changée), après les lignes
		// habituelles : lance `parler` à l'entrée d'un être et ajoute ses phrases.
		private void LignesVision(StringBuilder sb, PlantRenderer plante, MacroPick? bete)
		{
			if (!_visionActive) return;
			GDict cible = null;
			string cle = null;
			if (plante != null)
			{
				Variant tile = plante.GetMeta(LectureSnap.Meta("tile"), default);
				Variant lx = plante.GetMeta(LectureSnap.Meta("lx"), default);
				Variant ly = plante.GetMeta(LectureSnap.Meta("ly"), default);
				if (tile.VariantType == Variant.Type.Nil) return;
				cle = CleVoixPlante(tile.AsString(), lx.AsDouble(), ly.AsDouble());
				cible = new GDict { ["tile"] = tile, ["x_cm"] = lx, ["y_cm"] = ly };
			}
			else if (bete != null && FindPlot(bete.Value.Pos, out string t, out int r, out int c))
			{
				cle = CleVoixEtre(bete.Value.Cle, t, r, c);
				cible = new GDict { ["espece"] = bete.Value.Cle, ["tile"] = t, ["r"] = r, ["c"] = c };
			}
			if (cle == null) return;
			if (cle != _parlerCle)   // ENTRÉE de survol : un seul `parler`
			{
				_parlerCle = cle;
				_parlerPhrases = _voixEtres.TryGetValue(cle, out var dejaDites) ? dejaDites : null;
				if (_parlerEnVol == null) LancerParler(cle, cible);
				else { _parlerEnAttente = cible; _parlerEnAttenteCle = cle; }
			}
			if (_parlerPhrases == null) return;
			foreach (string ph in _parlerPhrases) Ligne(sb, $"« {ph} »");
		}

		private void LancerParler(string cle, GDict cible)
		{
			_parlerEnVolCle = cle;
			_parlerEnVol = Task.Run(() => _bridge?.Parler(cible));
		}

		// Appelée chaque frame (_Process) : consomme une réponse `parler` arrivée.
		private void MajVision()
		{
			if (_parlerEnVol == null || !_parlerEnVol.IsCompleted) return;
			var t = _parlerEnVol;
			string cle = _parlerEnVolCle;
			_parlerEnVol = null;
			if (!t.IsFaulted && t.Result != null && t.Result.ContainsKey("phrases")
				&& cle == _parlerCle)
			{
				var arr = t.Result["phrases"].AsGodotArray();
				var ph = new string[arr.Count];
				for (int i = 0; i < arr.Count; i++) ph[i] = arr[i].AsString();
				_parlerPhrases = ph;
				_cleVersion = -1;   // l'info-bulle se recompose à la frame suivante
			}
			if (_parlerEnAttente != null)
			{
				var cible = _parlerEnAttente;
				_parlerEnAttente = null;
				LancerParler(_parlerEnAttenteCle, cible);
			}
		}

		// Clés d'être COMMUNES au survol et aux voix d'overdose (Murmures.cs) :
		// plante = position locale au dixième de cm (valeurs JSON identiques des
		// deux côtés), bête/champignon = espèce + plot.
		private static string CleVoixPlante(string tile, double x, double y)
			=> $"p|{tile}|{System.Math.Round(x * 10)}|{System.Math.Round(y * 10)}";

		private static string CleVoixEtre(string espece, string tile, int r, int c)
			=> $"e|{espece}|{tile}|{r}|{c}";
	}
}
