// SYMBIOSE — MacroPick.cs (INFO-BULLE DU VIVANT ③)
// Ce que le PICKING de la vie macro rend sous le curseur : non plus une simple
// clé (ou un booléen pour les champignons), mais l'entrée la plus proche avec ce
// que le snapshot dit d'elle. Produit par MacroLife / ForagerLayer / CarpophoreLayer
// (`Near`), lu par l'observation (clé) et l'info-bulle (abondance, nourriture,
// rôle, densité) — un seul picking partagé (WorldView.Observation.cs).
//
// 📖 Pédagogie — un `readonly record struct` C# : une petite valeur immuable,
// copiée (pas allouée sur le tas) et comparable champ à champ. L'équivalent d'une
// `struct` C passée par valeur, avec le constructeur et l'égalité écrits par le
// compilateur.

using Godot;

namespace Symbiose
{
	/// <summary>Bête ou carpophore sous le curseur. `Cle` = clé de maîtrise
	/// (espèce animale, ou "champignon"). `Abondance` = nombre d'entrées VIVANTES de
	/// la même clé dans le MÊME plot (ce que la vue affiche). `Nourriture` =
	/// `activite` du snapshot (bête), &lt; 0 si le snapshot n'en donne pas.
	/// `Role` (b/r/h) et `Densite` : carpophore seulement (null / 0 sinon). `Pos` =
	/// ancre MONDE (cm) de l'entrée (banc de capture : y poser la souris).</summary>
	public readonly record struct MacroPick(string Cle, int Abondance, float Nourriture,
											string Role, float Densite, Vector2 Pos);
}
