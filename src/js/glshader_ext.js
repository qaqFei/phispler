(() => {

    const cv = document.createElement("canvas");
    const gl = cv.getContext("webgl") || cv.getContext("experimental-webgl");

    if (gl === null) {
        window["createGLProgram"] = () => null;
        window["GLERR"] = null;
        throw "WebGL not supported";
    }

    gl.enable(gl.BLEND);

    const positions = [
        -1, 1,
        1, 1,
        -1, -1,
        1, -1,
    ];
    const texCoords = [
        0, 1,
        1, 1,
        0, 0,
        1, 0,
    ];
    const vs_s = `
attribute vec2 a_position;
attribute vec2 a_texCoord;
varying vec2 uv;

void main() {
gl_Position = vec4(a_position, 0, 1);
uv = a_texCoord;
}
    `;

    const texture = gl.createTexture();
    gl.bindTexture(gl.TEXTURE_2D, texture);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
    gl.clearColor(0, 0, 0, 0);

    window["createGLProgram"] = (fs_s) => {
        window["GLERR"] = null;

        const vs = gl.createShader(gl.VERTEX_SHADER);
        gl.shaderSource(vs, vs_s);
        gl.compileShader(vs);

        const fs = gl.createShader(gl.FRAGMENT_SHADER);
        gl.shaderSource(fs, fs_s);
        gl.compileShader(fs);

        const program = gl.createProgram();
        if (!gl.getShaderParameter(fs, gl.COMPILE_STATUS)) {
            window["GLERR"] = gl.getShaderInfoLog(fs);
            console.log({
                err: gl.getShaderInfoLog(fs),
                scoure: fs_s
            });
            program.invtag = true;
            return;
        }

        gl.attachShader(program, vs);
        gl.attachShader(program, fs);
        gl.linkProgram(program);
        gl.useProgram(program);

        const positionBuffer = gl.createBuffer();
        gl.bindBuffer(gl.ARRAY_BUFFER, positionBuffer);
        gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(positions), gl.STATIC_DRAW);
        const posAttrLocation = gl.getAttribLocation(program, "a_position");
        gl.vertexAttribPointer(posAttrLocation, 2, gl.FLOAT, false, 0, 0);
        gl.enableVertexAttribArray(posAttrLocation);

        const texCoordBuffer = gl.createBuffer();
        gl.bindBuffer(gl.ARRAY_BUFFER, texCoordBuffer);
        gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(texCoords), gl.STATIC_DRAW);
        const texCoordAttrLocation = gl.getAttribLocation(program, "a_texCoord");
        gl.vertexAttribPointer(texCoordAttrLocation, 2, gl.FLOAT, false, 0, 0);
        gl.enableVertexAttribArray(texCoordAttrLocation);

        const textureLocation = gl.getUniformLocation(program, "screenTexture");
        gl.uniform1i(textureLocation, 0);

        return program;
    };

    const default_program = createGLProgram(`
varying lowp vec2 uv;
uniform sampler2D screenTexture;

void main() {
  gl_FragColor = texture2D(screenTexture, uv);
}
    `);

    const _seted_locations = new Map();

    const _set_location = (location, value) => {
        if (typeof value === "boolean") {
            gl.uniform1i(location, value ? 1 : 0);
        } else {
            gl[`uniform${value.length}fv`](location, value);
        }

        _seted_locations.set(location, value);
    }

    const _reset_locations = () => {
        if (!_seted_locations.size) return;
        _seted_locations.forEach((value, location) => {
            if (typeof value === "boolean") {
                gl.uniform1i(location, 0);
            } else {
                gl[`uniform${value.length}fv`](location, new Array(value.length).fill(0));
            }
        });
        _seted_locations.clear();
    }

    window["drawGL"] = (program, im, uniforms) => {
        if (program.invtag) program = default_program;

        if (uniforms.__enableAlpha) {
            gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);
        }

        gl.useProgram(program);
        for (const uniform_key in uniforms) {
            let value = uniforms[uniform_key];
            if (typeof value === "number") value = [value];
            if (!program[`${uniform_key}_location`]) program[`${uniform_key}_location`] = gl.getUniformLocation(program, uniform_key);
            const location = program[`${uniform_key}_location`];

            _set_location(location, value);
        }
        cv.width = im.width;
        cv.height = im.height;
        gl.viewport(0, 0, im.width, im.height);
        gl.clear(gl.COLOR_BUFFER_BIT);
        gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, im);
        gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);

        _reset_locations(program);

        if (uniforms.__enableAlpha) {
            gl.blendFunc(gl.ONE, gl.ONE_MINUS_SRC_ALPHA);
        }

        return cv;
    };
})();

class ShaderLoader {
    constructor() {
        this.pgs = new Map();
    }

    load(name, glsl) {
        if (this.pgs.has(name)) return;
        let pg = createGLProgram(glsl);
        this.pgs.set(name, pg);
    }

    render(im, name, uniforms) {
        let pg = this.pgs.get(name);
        if (pg === undefined || pg === null) return null;
        return drawGL(pg, im, uniforms);
    }

    renderToCanvas(ctx, name, uniforms) {
        const cv = ctx.canvas;
        uniforms["screenSize"] = [cv.width, cv.height];
        let result = this.render(cv, name, uniforms);
        if (result === null) return;
        ctx.clear();
        ctx.save();
        ctx.translate(cv.width / 2, cv.height / 2);
        ctx.scale(1, -1);
        ctx.drawImage(result, -cv.width / 2, -cv.height / 2);
        ctx.restore();
    }
}
