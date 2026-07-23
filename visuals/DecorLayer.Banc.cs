// SYMBIOSE — DecorLayer.Banc.cs (T4 LISIBILITÉ DÉCOR — banc d'observation F5)
// Partial de DecorLayer : un OUTIL DE DEBUG isolé du rendu (DecorLayer.cs) et des
// arbres (DecorLayer.Arbres.cs). Un fichier = une responsabilité — ici « exposer
// les 4 motifs d'un regard pour valider la lisibilité au F5 », rien d'autre.
//
// 📖 Pédagogie — POURQUOI un TOGGLE et pas un « seed de démo » :
// le kickoff proposait deux pistes (un seed connu produisant les 4 motifs, OU un
// toggle debug). La 1re est IMPOSSIBLE : dans BuildProfile, les 4 côtés d'un même
// seed dérivent d'un hash « decor|seed|cote » qui ne diffère que du DERNIER
// caractère (0..3) → le djb2-xor ne brasse que les bits bas → les 4 rolls %100
// tombent quasi identiques. Résultat : un terrain porte presque toujours un ANNEAU
// UNIFORME d'un seul motif, et la FALAISE — qui exige une rivière clockwise-adjacente
// à une prairie — n'apparaît sur AUCUN seed (vérifié : 0 sur 300 000). Aucun seed
// n'expose donc les 4 motifs. On ne CORRIGE pas BuildProfile ici (cela changerait
// la distribution normale → philo #7, et déborde T4) : c'est consigné en dette.
// Le toggle FORCE un profil de démonstration UNIQUEMENT quand il est activé — la
// distribution par seed reste rigoureusement intacte hors banc.

using Godot;

namespace Symbiose
{
	public partial class DecorLayer : Node2D
	{
		// État du banc (OFF par défaut : le jeu montre toujours le décor par seed).
		private bool _banc;

		/// <summary>Bascule le banc d'observation (WorldView, touche F10). ON = les
		/// 4 motifs côte à côte ; OFF = retour au décor dérivé du seed du terrain.</summary>
		public void ToggleBanc()
		{
			_banc = !_banc;
			Build(_seed);   // reconstruit le profil selon le nouvel état, puis redessine
			GD.Print($"[DecorLayer] F10 → banc décor {(_banc ? "ON (4 motifs)" : "OFF (seed)")}.");
		}

		// Profil de DÉMONSTRATION : un motif par bord cardinal (forêt N, rivière E,
		// falaise S, prairie O). La falaise est en pente Verticale (face bien lisible).
		// Graines de secteur dérivées de HashKey (tracé sinueux stable, zéro Random,
		// philo #3). N'est JAMAIS produit hors banc → la distribution reste intacte.
		private static SurroundingsProfile BancProfile()
		{
			var s = new Secteur[4];
			s[0] = new Secteur { Cote = 0, Motif = Motif.Foret,   Pente = PenteFalaise.Douce,     SeedSecteur = HashKey("banc|foret") };
			s[1] = new Secteur { Cote = 1, Motif = Motif.Riviere, Pente = PenteFalaise.Douce,     SeedSecteur = HashKey("banc|riviere") };
			s[2] = new Secteur { Cote = 2, Motif = Motif.Falaise, Pente = PenteFalaise.Verticale, SeedSecteur = HashKey("banc|falaise") };
			s[3] = new Secteur { Cote = 3, Motif = Motif.Prairie, Pente = PenteFalaise.Douce,     SeedSecteur = HashKey("banc|prairie") };
			return new SurroundingsProfile { Secteurs = s };
		}
	}
}
