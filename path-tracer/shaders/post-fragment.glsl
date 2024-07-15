#version 300 es
precision highp float;
in vec2 uv;
out vec4 fragColor;

uniform sampler2D tex;



#define ROOT 4.828427



vec3 decodeColor(vec4 pixel) {
	if (pixel.a <= 0.0)
		return vec3(0.0);
	float x = 255.0*pixel.a - 127.0;
	return pow(1.1, x)*pixel.rgb;
}



vec3 linear2Gamma(vec3 color) {
	bvec3 cutoff = lessThan(color.rgb, vec3(0.0031308));
	vec3 higher = vec3(1.055)*pow(color.rgb, vec3(1.0/2.4)) - vec3(0.055);
	vec3 lower = color.rgb * vec3(12.92);
	return mix(higher, lower, cutoff);
}



vec3 doTonemapping(vec3 color, float r) {
	// define ACES-CG
	mat3 srgbToAp1 = mat3(
		0.612494198536834, 0.070594251610915, 0.020727335004178,
		0.338737251923843, 0.917671483736251, 0.106882231793044,
		0.048855526064502, 0.011704306146428, 0.872338062223856
	);
	mat3 ap1ToSrgb = mat3(
		1.707077341393391, -0.1310087341843325, -0.02450960122569158,
		-0.6199617703400125, 1.13899879428281, -0.1248238298364764,
		-0.08728719115306108, -0.007944958796604444, 1.149392018071762
	);
	
	vec3 c = srgbToAp1*color;
	vec3 n = r*r*c*c;
	vec3 u = vec3(1.0);
	vec3 d = (r*c + u)*(r*c + u) + u;
	vec3 t = ap1ToSrgb*(n/d);
	
	return t;
}



void main() {
	vec4 pixel = texture(tex, uv);
	vec3 color = decodeColor(pixel);
	color = doTonemapping(color, ROOT);
	color = linear2Gamma(color);
	fragColor = vec4(color, 1.0);
}