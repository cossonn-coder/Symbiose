// SYMBIOSE — BudgetCuisson.cs (sprint RELIQUATS DES PLANTES ① — mémoire de précuisson)
// Le PLAFOND GLOBAL de la mémoire de précuisson (décision E6 de Nico : 1 Go). Il
// couvre les deux postes qui grossissent avec le zoom :
//  • les pages d'atlas des images cuites (AtlasPages.TotalBytes) ;
//  • les planches de codes splat chargées pour cuire (SplatPlanches.OctetsCharges).
// Avant ①, rien ne bornait leur somme : les plafonds PAR PLANTE de PlantBaker
// (2048 px de côté) en tenaient lieu, et une grande plante à ×32 n'était jamais
// cuite — donc jamais en splats (conception §4). Depuis ①, une plante se cuit
// jusqu'à la limite GPU (16 384 px de côté) tant que le total tient sous ce budget.
//
// 📖 Pédagogie (analogie embarqué) : c'est un allocateur avec une politique
// d'éviction, comme un cache de pages en RAM. Quand une cuisson ne tient pas, on
// rend d'abord les images des plantes HORS CHAMP (dans la marge, hors de l'écran),
// puis celles des plantes les PLUS LOINTAINES du centre de l'écran.
// Les PLANCHES ne sont jamais rendues ici : la cuisson qui demande la place va
// presque toujours les relire (même espèce, même palier), et recharger une planche
// ×32 coûte 0,3 à 1,4 s [VM, n=1 par planche]. Mesuré au banc (budget abaissé à
// 80 Mo, n=2 runs) : les rendre ici laissait passer la cuisson, qui les rechargeait
// aussitôt → budget dépassé ET gel. Les planches se régulent seules : SplatPlanches
// rend les plus anciennes quand un CHARGEMENT dépasse le budget. Le budget reste
// donc dépassable de la taille des planches en cours d'usage (au pire quelques
// centaines de Mo à ×32 si beaucoup d'espèces sont cadrées : à lire au rapport).
// L'ordre est STRICT : une plante n'évince jamais une plante plus proche
// qu'elle du centre (clé `Cle`). Pas de ping-pong possible entre deux plantes.
// Une plante qui ne trouve pas de place reste en DESSIN DIRECT (le repli
// d'avant ①, jamais de trou) : elle est journalisée une fois et retentée au
// balayage périodique de la file (BakeQueue), le jour où la caméra a bougé.
//
// On n'évince d'une plante que si cela libère VRAIMENT de la mémoire : une page
// dédiée (grande plante, sa page à sa taille exacte). Rendre un rectangle d'une
// page partagée de 16 Mo ne rend rien au GPU tant que la page n'est pas vide.
//
// Purement visuel, déterministe à état de caméra égal : golden non concerné.

using Godot;
using System.Collections.Generic;

namespace Symbiose
{
	internal static class BudgetCuisson
	{
		// Le budget (E6). Constante UNIQUE, à régler ici : 1 Go sur le PC du F5
		// (HD 4600, mémoire vidéo prise sur la RAM) comme sur le suivant.
		public const long BudgetOctets = 1L << 30;

		/// <summary>Mémoire de précuisson courante (pages + planches), octets.</summary>
		public static long Courant => AtlasPages.TotalBytes + SplatPlanches.OctetsCharges;

		/// <summary>Images évincées pour faire place / replis journalisés (cumuls).</summary>
		public static long Evictions, ReplisTotal;

		// Plantes en repli : true = faute de budget (retentée), false = trop grande
		// pour une texture GPU (jamais retentée tant que rien ne la salit).
		private static readonly Dictionary<PlantRenderer, bool> _replis = new();
		public static int Replis => _replis.Count;

		private const float HorsChamp = 1e6f;   // pousse toute plante hors écran après celles à l'écran
		private static readonly List<(float Cle, PlantRenderer P)> _candidats = new();

		/// <summary>Fait de la place pour `besoin` octets au profit de `d`. false = la
		/// place n'existe pas sans évincer plus proche que `d` → repli.</summary>
		public static bool Reserver(PlantRenderer d, long besoin)
		{
			long trop = Courant + besoin - BudgetOctets;
			if (trop <= 0) return true;
			// Faisabilité AVANT toute éviction : ne rien casser pour finir en repli.
			float kd = Cle(d);
			_candidats.Clear();
			long liberable = 0;
			foreach (var q in BakeQueue.All)
			{
				if (q == d || !GodotObject.IsInstanceValid(q) || q.Baker.InFlight) continue;
				long o = q.Baker.OctetsDedies;
				if (o <= 0) continue;
				float k = Cle(q);
				if (k <= kd) continue;
				_candidats.Add((k, q));
				liberable += o;
			}
			if (liberable < trop) return false;
			_candidats.Sort((a, b) => b.Cle.CompareTo(a.Cle));   // la plus lointaine d'abord
			foreach (var (_, q) in _candidats)
			{
				q.Baker.Release();
				q.QueueRedraw();
				Evictions++;
				Noter(q, "évincée", parBudget: true);
				if (Courant + besoin <= BudgetOctets) return true;
			}
			return Courant + besoin <= BudgetOctets;
		}

		/// <summary>Journalise un repli (une fois par plante tant qu'elle y reste).</summary>
		public static void Noter(PlantRenderer p, string raison, bool parBudget, long besoin = 0)
		{
			if (_replis.ContainsKey(p)) { _replis[p] = parBudget; return; }
			_replis[p] = parBudget;
			ReplisTotal++;
			GD.Print($"[Cuisson] repli {p.Espece ?? p.Name} : {raison}"
				+ (besoin > 0 ? $", besoin {besoin / 1048576.0:F0} Mo" : "")
				+ $" · précuisson {Courant / 1048576.0:F0}/{BudgetOctets / 1048576} Mo · {Replis} en repli");
		}

		/// <summary>La plante est cuite, ou quitte la scène : plus en repli.</summary>
		public static void Sortir(PlantRenderer p) => _replis.Remove(p);

		/// <summary>Balayage périodique (BakeQueue) : les replis faute de budget
		/// redemandent leur cuisson — la caméra a pu bouger, d'autres sortir du champ.</summary>
		public static void Relancer()
		{
			foreach (var (p, parBudget) in _replis)
				if (parBudget && GodotObject.IsInstanceValid(p)) BakeQueue.MarkDirty(p);
		}

		// Priorité d'une plante = distance (px du viewport monde) du centre de
		// l'écran à son emprise ; 0 si l'emprise couvre le centre. Hors écran :
		// + HorsChamp, donc toujours après toutes les plantes à l'écran.
		private static float Cle(PlantRenderer p)
		{
			Rect2 vp = p.GetViewportRect();
			Rect2 e = p.EmpriseCanvas;
			var locale = new Rect2(e.Position - p.Position, e.Size);
			Rect2 r = p.GetGlobalTransformWithCanvas() * locale;
			Vector2 c = vp.GetCenter();
			Vector2 proche = c.Clamp(r.Position, r.End);
			float dist = c.DistanceTo(proche);
			return r.Intersects(vp, includeBorders: true) ? dist : dist + HorsChamp;
		}

		/// <summary>Ligne du rapport perf (touche C) et du F4.</summary>
		public static string Ligne() =>
			$"précuisson {Courant / 1048576.0:F0}/{BudgetOctets / 1048576} Mo "
			+ $"(pages {AtlasPages.TotalBytes / 1048576.0:F0}, planches {SplatPlanches.OctetsCharges / 1048576.0:F0}) "
			+ $"· {Replis} plante(s) en repli · {Evictions} évincée(s)";
	}
}
