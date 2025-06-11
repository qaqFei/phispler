// webgl shader for trigrid

#version 100
precision highp float;

varying lowp vec2 uv;
uniform sampler2D screenTexture;

uniform vec2 tex_size;

uniform vec4 base_color;

uniform vec4 face_color;
uniform float face_brightness;

uniform vec4 grid_color;
uniform float grid_brightness;

uniform vec4 glow_color;
uniform float glow_brightness;

uniform bool always_on;
uniform bool glow_ooroff;

uniform float t;

void main() {
    vec2 uv2 = uv;
    vec2 w = uv2 - 0.5;
    uv2.x += pow(abs(w.y), 2.) * (-w.x);
    uv2.x += tex_size.x / 2.;

    vec2 new_uv = mod(uv2 / tex_size, 1.0);
    vec4 texColor = texture2D(screenTexture, new_uv);

    float k = 0.8;
    float k2 = 1.6;
    float p = max(0., min(1., (
        (sin((uv2.y + t) * k2) - k)
        * (1. / (1. - k))
    )));

    if (always_on) {
        p = 1.;
    }

    float k3 = 2.;
    float k4 = 5.;
    float k5 = 1.;

    float grid_w = 1.;
    float face_w = p * k3;
    float glow_w = p * k4;

    if (glow_ooroff) {
        grid_w *= p;
    }

    vec4 finalColor = 
        base_color +
        (
            grid_color * grid_brightness * texColor.r * grid_w +
            face_color * face_brightness * texColor.b * face_w +
            glow_color * pow(glow_brightness * texColor.g * glow_w, k5)
        );

    finalColor.a = texColor.a * (finalColor.r + finalColor.b + finalColor.g) / 3. * 0.4;

    gl_FragColor = finalColor;
}
