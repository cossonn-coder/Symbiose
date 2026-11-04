// SYMBIOSE — PlantRenderer.Bake.cs (partial, sprint JARDIN VIVANT T2 — pré-cuisson)
// Côté PLANTE de la pré-cuisson : au lieu de rejouer chaque frame le dessin
// vectoriel (DrawVector, PlantRenderer.cs), la plante affiche une IMAGE cuite
// d'elle-même (PlantBaker) et ne la refait que quand ce qui est dessiné change.
//
// 📖 Pédagogie (analogie embarqué) : DrawVector est un calcul ; l'image cuite
// est sa table précalculée en RAM vidéo. Un setter ne recalcule plus rien : il
// lève un drapeau « sale » (Invalidate) et la FILE (BakeQueue) recuit quelques
// plantes par frame — jamais tout le jardin d'un coup (exigence Nico).
//
// Trois rôles du même nœud :
//  · PLANTE DU MONDE sans image (naissance, trop grande, hors champ libérée) :
//    dessin vectoriel EN DIRECT, exactement comme avant T2 — jamais de trou.
//  · PLANTE DU MONDE avec image : un seul DrawTextureRect (+ surbrillance de
//    taille en direct, interactive). Une plante sale GARDE son ancienne image.
//  · PINCEAU (IsBrush) : copie d'état posée dans le SubViewport de cuisson ; son
//    _Draw rejoue DrawVector, mesuré (ms de cuisson CPU par plante).

using Godot;
using System.Diagnostics;

namespace Symbiose
{
	public partial class PlantRenderer : Node2D
	{
		/// <summary>Vrai pour le pinceau de cuisson (posé à la construction).</summary>
		internal bool IsBrush { get; init; }

		// Cuiseur de CETTE plante (null tant qu'aucune image n'a été demandée).
		// Une image PAR INSTANCE : deux laitues voisines n'ont jamais la même.
		private PlantBaker _baker;
		internal PlantBaker Baker => _baker ??= new PlantBaker(this);
		internal bool HasBakedImage => _baker != null && _baker.HasImage;
		// Coût estimé d'une cuisson (budget de la file) = nombre de segments.
		internal int BakeCost => _structure?.Segments.Count ?? 0;

		/// <summary>Semaine paresseuse (D106 T4) : la plante est hors marge et sa
		/// dernière donnée n'est pas encore appliquée (WorldView.Attente.cs). La file
		/// de cuisson la saute : on ne cuit pas une image déjà périmée.</summary>
		internal bool EnAttente { get; set; }

		// Emprise projetée (boîte locale, mémoïsée) pour la marge du culling (T4) :
		// recalculée seulement après un Invalidate (ce qui est dessiné a changé),
		// jamais à chaque pan — StraightBounds parcourt tous les segments.
		private Rect2 _emprise;
		private bool _empriseSale = true;

		/// <summary>Emprise de la plante en coordonnées CANVAS (boîte de dessin à
		/// la pose courante, translatée au collet). Taille nulle = juste le collet.</summary>
		internal Rect2 EmpriseCanvas
		{
			get
			{
				if (_empriseSale) { _emprise = StraightBounds(); _empriseSale = false; }
				return new Rect2(Position + _emprise.Position, _emprise.Size);
			}
		}

		// Marge autour de la géométrie projetée (px canvas) : feuilles déportées
		// (≤ ~6 px), limbe (≤ ~3 px), fruits (≤ 6 px), fleurs, vrille, surbrillance.
		// Mesurée large : un organe rogné serait une différence visible.
		private const float BakePadPx = 14f;

		// Seules les VRAIES plantes se cuisent : LeafLitterLayer hérite de
		// PlantRenderer comme simple « stylo » (DrawLitterLeaf) → exclu.
		private bool Bakeable => !IsBrush && GetType() == typeof(PlantRenderer);

		public override void _EnterTree()
		{
			if (!Bakeable) return;
			// L'image cuite est PRÉMULTIPLIÉE (fond transparent) → ce matériau la
			// remet en alpha droit ; sans effet sur le dessin vectoriel direct.
			Material = BakeQueue.Unpremultiply;
			BakeQueue.Register(this);
		}

		public override void _ExitTree()
		{
			if (!Bakeable) return;
			BakeQueue.Unregister(this);
			_baker?.Release();   // rend son rectangle de page et ses pinceaux (②)
		}

		/// <summary>Ce qui est dessiné a changé (croissance, symptôme, palier de
		/// zoom…) : la plante devient « sale ». Si elle a déjà une image, elle la
		/// garde jusqu'à sa re-cuisson ; sinon elle se redessine en direct — sauf au
		/// CHANGEMENT DE PALIER (LEVIERS ③, `changementPalier`) : une plante qui a déjà
		/// un tracé vectoriel enregistré le GARDE (palier précédent, mis à l'échelle
		/// par la caméra, exactement comme une image cuite gardée) jusqu'à ce que la
		/// file la cuise (Commit) ou constate qu'elle est trop grande (Begin raté) —
		/// les deux la redessinent. Mesuré [VM, balayage ①] : à chaque cran, des
		/// centaines de plantes encore sans image retraçaient tout leur vectoriel
		/// dans l'image du cran (« plantes vectoriel » 45-95 ms à ×2→×32).</summary>
		public void Invalidate(bool changementPalier = false)
		{
			_empriseSale = true;   // la boîte de dessin a pu changer (T4)
			PlantShadow.MarquerSale();   // emprise ou tapis ont pu changer → lot d'ombres (③)
			if (!Bakeable) { QueueRedraw(); return; }
			// Tapis par plot (D106 T5, D5) : trop petite pour ce palier → ni image
			// ni dessin propre ni ombre ; c'est le tapis de son plot qui la montre.
			DeciderTapis();
			if (_enTapis)
			{
				_baker?.Release();
				BakeQueue.Retirer(this);
				QueueRedraw();   // efface l'ancienne image / le dessin direct
				return;
			}
			BakeQueue.MarkDirty(this);
			if (!HasBakedImage && !(changementPalier && _traceVecteur)) QueueRedraw();
		}

		// Vrai si le dernier _Draw a enregistré le tracé VECTORIEL direct (pas une
		// image, pas le tapis) : ce tracé peut servir d'attente au palier suivant.
		private bool _traceVecteur;

		// Banc PERF VUE ① : chronométré (PerfPostes), corps inchangé.
		// LEVIERS ③ : le tracé VECTORIEL direct (plante du monde sans image) est compté
		// à part (« plantes vectoriel ») — c'est lui qu'on soupçonne au changement de
		// palier ; « plantes _Draw » garde les images cuites et le reste.
		public override void _Draw()
		{
			bool vecteur = Bakeable && !_enTapis && !HasBakedImage;
			long t0 = PerfPostes.Debut();
			DessinerPlante();
			PerfPostes.Fin(vecteur ? PerfPostes.Poste.PlanteVecteur : PerfPostes.Poste.PlanteDraw, t0);
		}

		private void DessinerPlante()
		{
			if (IsBrush)
			{
				long t0 = Stopwatch.GetTimestamp();
				DrawVector();
				double ms = Stopwatch.GetElapsedTime(t0).TotalMilliseconds;
				BakeQueue.RecordBrushDraw(ms, _structure?.Segments.Count ?? 0);
				if (BakeQueue.TraceCout)
					GD.Print($"[cout] {_structure?.SpeciesName} {ms:F3} {_lotPrairie?.Sommets ?? 0}");
				return;
			}
			// LEVIERS ③ : retient si le tracé enregistré est le vectoriel direct.
			_traceVecteur = !_enTapis && !HasBakedImage;
			if (_enTapis) return;   // rendue par le tapis de son plot (T5)
			// CASSÉ À L'ÉCRAN ③ : une image cuite en palette indexée se lit avec le
			// shader de la LUT (partagé → envois toujours regroupés) ; le dessin
			// direct et les images littérales (paliers hauts, F11 OFF) gardent
			// l'ancien matériau. Affectation seulement au changement.
			Material mat = HasBakedImage && _baker.ImageIndexee ? PaletteIndexee.Materiau : BakeQueue.Unpremultiply;
			if (Material != mat) Material = mat;
			if (!HasBakedImage) { DrawVector(); return; }
			_baker.DrawImage(_pose);   // T3 : la pose de flexion courante (WindWave)
			// Surbrillance de taille : interactive (survol souris) → dessinée EN
			// DIRECT par-dessus l'image, jamais cuite (aucune latence de file).
			if (_structure != null && string.IsNullOrEmpty(_deadStade)
				&& WorldView.CurrentZoom >= SegmentDetailMinZoom)
				DrawHighlight(_structure.ColletCm);
		}

		/// <summary>Recopie l'état DESSINÉ vers le pinceau (références partagées :
		/// la structure est en lecture seule côté vue). Surbrillance exclue.</summary>
		internal void CopyDrawStateTo(PlantRenderer brush)
		{
			brush._structure = _structure;
			brush._spreadCm = _spreadCm;
			brush._heightCm = _heightCm;
			brush._deadStade = _deadStade;
			brush._colorTint = _colorTint;
			brush._colorAmount = _colorAmount;
			brush._ravageurs = _ravageurs;
			brush._gel = _gel;
			brush._grele = _grele;
			brush._drought = _drought;
			brush._ombre = _ombre;
			brush._maladie = _maladie;
			brush._vitalite = _vitalite;
			brush._silhouette = _silhouette;
			brush._strate = _strate;           // port (paliers bas, D106 T5)
			brush._rayonReelCm = _rayonReelCm;
			brush._hauteurReelCm = _hauteurReelCm;
			brush._hauteurLisseeCm = _hauteurLisseeCm;
			brush._epaisseurMaxCm = _epaisseurMaxCm;
			brush._swayPhase = _swayPhase;     // teinte d'automne stable par pied
			brush._heat = _heat;           // variante météo (T4)
			brush._wet = _wet;
			brush._snow = _snow;           // variante froide (T5)
			brush._frost = _frost;
			brush._raideur = _raideur;
			brush._supportKind = _supportKind;
			brush._highlightSegment = -1;
			brush.QueueRedraw();
		}

		/// <summary>Boîte englobante LOCALE (px canvas, origine = collet) de tout
		/// ce que DrawVector peut tracer (à la flexion courante) : extrémités de segments (et leur pied au
		/// sol, pour le squelette couché aplati), couronne des paliers bas (T5),
		/// élargie de BakePadPx pour les organes. Vide si rien à dessiner.</summary>
		private Rect2 StraightBounds()
		{
			if (_structure == null || _structure.Segments.Count == 0) return default;
			if (BoitePrairie(out Rect2 prairie)) return prairie;   // port dessiné (Prairie.cs)
			if (BoitePort(out Rect2 port)) return port;   // port à fiche (Ports.cs)
			Vector3 c = _structure.ColletCm;
			var r = new Rect2(Vector2.Zero, Vector2.Zero);
			foreach (var s in _structure.Segments)
			{
				Vector3 tip = s.Base + s.Dir * s.LengthCm;
				r = r.Expand(Iso(s.Base.X - c.X, s.Base.Y - c.Y, s.Base.Z))
					 .Expand(Iso(tip.X - c.X, tip.Y - c.Y, tip.Z))
					 .Expand(Iso(tip.X - c.X, tip.Y - c.Y, 0f));
			}
			// Paliers bas (T5) : la couronne (tache / port) déborde des segments.
			if (WorldView.CurrentZoom < PaliersHautsMinZoom) r = EtendrePalierBas(r);
			return r.Grow(BakePadPx);
		}
	}
}
