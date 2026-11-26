// SYMBIOSE — chargement_mycelium.gdshader (sprint LISIÈRE & CHARGEMENT ④, décision L3)
// L'écran de chargement : un mycélium qui s'arborise et SERT de barre de progression.
// Deux textures cuites hors ligne (tools/splat/cuire_mycelium.js) :
//   • TEXTURE (960×270) : à gauche le FOND (spore, litière, plantule, racine nue), à droite
//     le MYCÉLIUM seul (hyphes, manteau autour de la racine, carpophore) ;
//   • `ages` (480×270) : l'âge ∈ [0, 1] de chaque pixel du mycélium (alpha 0 ailleurs).
// Un pixel du mycélium se montre quand son âge ≤ `progression` ; sinon on voit le fond.
// FRONT : les pixels nés depuis moins de `front` s'éclairent — la pointe des hyphes, là où
// elles poussent. Aucun temps propre : tout suit la progression RÉELLE du chargement.
//
// 📖 Pédagogie : c'est un « seuil sur une carte des dates » (comme une carte d'isochrones) :
// une seule image dit QUAND chaque pixel apparaît ; l'animation entière tient dans un
// nombre (progression). La comparaison est entière : âge cuit sur 8 bits (1-255), on
// compare au même pas (½ pas de marge) pour ne pas faire clignoter un pixel au seuil.

shader_type canvas_item;

uniform sampler2D ages : filter_nearest;
uniform float progression = 0.0;
uniform float front = 0.035;
uniform vec4 lueur : source_color = vec4(1.0, 0.97, 0.82, 1.0);

void fragment() {
	vec4 fond = texture(TEXTURE, vec2(UV.x * 0.5, UV.y));
	vec4 myc = texture(TEXTURE, vec2(0.5 + UV.x * 0.5, UV.y));
	vec4 a = texture(ages, UV);
	float age = a.r;
	float marge = 0.5 / 255.0;
	if (a.a > 0.5 && age <= progression + marge) {
		// Front : 1 à la pointe (âge = progression), 0 à `front` derrière.
		float k = clamp(1.0 - (progression - age) / front, 0.0, 1.0);
		COLOR = vec4(mix(myc.rgb, lueur.rgb, 0.75 * k * k), 1.0);
	} else {
		COLOR = fond;
	}
}
