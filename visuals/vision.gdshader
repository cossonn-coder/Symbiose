// SYMBIOSE — vision.gdshader (sprint « le sol qui respire » ⑧)
// La VISION après un champignon psychédélique, en post-traitement plein écran du
// monde (posé sur le SubViewportContainer comme la palette SNES, cf.
// PaletteSnes.cs ; HUD et info-bulles, hors SubViewport, restent nets).
// Effet voulu par Nico : « couleurs plus vives, comme un niveau transcendant de
// compréhension ». Donc : saturation et lumière en hausse, et une lente ONDE de
// teinte qui traverse le jardin — douce, jamais stroboscopique.
//
// 📖 Pédagogie : la saturation se règle en mélangeant le pixel avec son gris (sa
// luminance) : mix(gris, couleur, k) avec k > 1 EXTRAPOLE au-delà de la couleur,
// c'est le « boost » classique. L'onde de teinte tourne la couleur autour de
// l'axe gris (rotation de Rodrigues autour de (1,1,1)/√3), d'un angle qui varie
// lentement avec le temps et la position. Purement visuel : aucun état de jeu.

shader_type canvas_item;

uniform float force = 1.0;   // 1 = vision ; 2 = overdose

vec3 tourner_teinte(vec3 c, float a) {
	const vec3 k = vec3(0.57735);
	float co = cos(a);
	return c * co + cross(k, c) * sin(a) + k * dot(k, c) * (1.0 - co);
}

void fragment() {
	vec4 src = texture(TEXTURE, UV);
	float gris = dot(src.rgb, vec3(0.2126, 0.7152, 0.0722));
	vec3 c = mix(vec3(gris), src.rgb, 1.0 + 0.6 * force);
	float onde = sin(TIME * 0.35 + UV.x * 4.0 + UV.y * 2.5);
	c = tourner_teinte(c, 0.14 * force * onde);
	c *= 1.0 + 0.05 * force;
	COLOR = vec4(clamp(c, 0.0, 1.0), src.a);
}
