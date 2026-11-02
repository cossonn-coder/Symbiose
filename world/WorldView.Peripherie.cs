// SYMBIOSE — WorldView.Peripherie.cs (partial de WorldView, PÉRIPHÉRIE D73 ⑦)
// La CEINTURE côté vue : recevoir le bloc `ceinture` du snapshot (→ DecorLayer, qui
// cesse d'inventer son décor) et RÉSOUDRE un clic hors jardin en un CÔTÉ cardinal
// (la cible des sept gestes de paysage). Deux faces d'une même responsabilité — « la
// périphérie telle que la vue la voit et la désigne » — d'où un partial dédié plutôt
// que deux ajouts dans Snapshot.cs et ActionDispatch.cs, déjà denses.
//
// 📖 Pédagogie — POURQUOI le décor est cliquable sans être un nœud pickable :
// le picking de WorldView n'utilise PAS l'input de Godot (aucun Area2D, aucun
// _InputEvent par nœud) : il convertit la souris en cm MONDE (ScreenToWorld) puis
// cherche géométriquement ce qui s'y trouve (FindPlot, FindPlant). Le ZIndex négatif
// du décor n'y change donc rien : il suffit d'ajouter une résolution géométrique de
// plus, et le picking des plots du jardin n'est même pas touché (les deux domaines
// sont DISJOINTS — dedans/dehors le carré [0, WorldCm]²).
//
// 📖 Pédagogie — la granularité est le SECTEUR, pas le mètre carré (décision D-1) :
// un geste de paysage vaut pour un bord entier (« j'ouvre une clairière au nord »).
// Le moteur ne connaît que 4 secteurs agrégés : simuler une lisière en arbres réels
// rouvrirait la dette perf D32 sans rien apprendre au joueur. La vue n'a donc à
// désigner qu'un entier, 0..3.

using Godot;
using GDict = Godot.Collections.Dictionary;
using GArray = Godot.Collections.Array;

namespace Symbiose
{
	public partial class WorldView : Node2D
	{
		// Noms des bords, dans l'ordre des index du moteur (`fields/peripherie.
		// NOMS_COTES`) — pour les messages de HUD. Le moteur nomme aussi les bords
		// dans SES messages ; ici c'est pour ce que la vue dit AVANT d'envoyer.
		private static readonly string[] NomsCotes = { "nord", "est", "sud", "ouest" };

		// Profondeur cliquable de la bande, en cm MONDE : la même que la ceinture du
		// moteur (`PROFONDEUR_CM = 900`) et que `DecorLayer.DepthCm`. Au-delà, on est
		// hors décor — un clic perdu dans le vide ne doit pas abattre une forêt.
		private const float PeripherieDepthCm = 900f;

		/// <summary>
		/// Le bloc `ceinture` du snapshot (protocole 0.5.41) → le décor. Lecture
		/// TOLÉRANTE : bloc absent (monde sans périphérie, binaire pré-0.5.41) →
		/// `SetCeinture(null)` rend la main au profil local de `DecorLayer`.
		/// </summary>
		private void ApplyCeinture(GArray ceinture)
		{
			_decorLayer?.SetCeinture(ceinture);
			_foragerLayer?.SetColoniesBord(ceinture);   // LISIÈRE NUE ② : butineurs de bord
		}

		/// <summary>
		/// Le SECTEUR de périphérie sous un point MONDE (cm), ou false si le point
		/// tombe DANS le jardin (c'est alors une affaire de plots) ou trop loin
		/// dehors. Aux coins, c'est le débordement le plus FRANC qui gagne : on
		/// désigne le bord dont on est le plus près de l'axe.
		/// </summary>
		private bool FindSecteur(Vector2 w, out int cote)
		{
			cote = -1;
			// Débordement hors du carré du jardin, bord par bord (0 = dedans).
			float nord = -w.Y, sud = w.Y - WorldCm;
			float ouest = -w.X, est = w.X - WorldCm;
			float best = 0f;
			// Ordre nord, est, sud, ouest = ordre des index moteur ; le `>` strict
			// départage les coins de façon déterministe (le 1er bord gagne à égalité).
			if (nord > best) { best = nord; cote = 0; }
			if (est > best) { best = est; cote = 1; }
			if (sud > best) { best = sud; cote = 2; }
			if (ouest > best) { best = ouest; cote = 3; }
			if (cote < 0 || best > PeripherieDepthCm) { cote = -1; return false; }
			return true;
		}

		/// <summary>Cible d'un geste de paysage : `{cote}`, la désignation qu'attend
		/// `peripherie_route` côté pont. Renvoie null si le clic n'est pas dans la
		/// bande de décor — utilisée telle quelle par `creuser`, qui RETOMBE alors sur
		/// le plot du jardin (un verbe, deux cibles) sans rien annoncer.</summary>
		private GDict CibleSecteur(Vector2 w)
		{
			if (!FindSecteur(w, out int cote)) return null;
			return new GDict { ["cote"] = cote };
		}

		/// <summary>Résolution COMPLÈTE d'un geste de paysage au clic (kind 'L' du
		/// dispatch) : la cible, ou un refus de désignation expliqué. Nomme le bord
		/// visé dans le HUD — l'`Evenement` du carnet ne porte PAS le côté du terrain
		/// (⑥), c'est donc à la vue de le dire ; le verdict du serveur écrase ce
		/// message au retour de l'action.</summary>
		private bool TryCibleSecteur(string nom, Vector2 w, out GDict target)
		{
			target = CibleSecteur(w);
			if (target == null)
			{
				_lastActionMsg = $"{nom} : cliquez le décor autour du jardin "
								 + "(forêt, rivière, falaise, friche)";
				UpdateActionHud();
				FlashActionLabel();
				return false;
			}
			_lastActionMsg = $"{nom} — bord {NomCote(target["cote"].AsInt32())}…";
			return true;
		}

		/// <summary>Nom diégétique d'un bord pour le HUD (« bord nord »).</summary>
		private static string NomCote(int cote) =>
			cote >= 0 && cote < 4 ? NomsCotes[cote] : "?";
	}
}
