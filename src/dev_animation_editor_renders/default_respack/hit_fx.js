const fix_orp = p => p < 0 ? 0 : p > 1 ? 1 : p;
const phi_tween = (p, exp = 10, c = 0.1) => fix_orp(
    (1 - ((1 - p) ** exp + c - p * c) + c)
    / (1 + c)
);

function render(p) {
    const {
        ctx,
    } = this;

    ctx.canvas.style.backgroundColor = "black";
    const $ = x => document.querySelector(x);

    if (!$(".hit_fx_helper")) {
        const helper = document.createElement("canvas");
        helper.classList.add("hit_fx_helper");
        ctx.canvas.parentElement.appendChild(helper);

        this.helper_imgs = [];

        // for (let i = 0; i < 30; i++) {
        for (let i = 0; i < 1; i++) {
            const img = new Image();
            img.loaded = false;
            img.onload = () => (img.loaded = true);
            img.src = `./dev_animation_editor_renders/default_respack/hit_fx_helper_res/${i + 1}.png`;
            this.helper_imgs.push(img);
        }
    }

    const tfs = {
        linear: p => p,
        easeIn: p => 1.0 - phi_tween(1.0 - p),
        easeOut: phi_tween
    }
    const p_slower = fix_orp(p * 0.7);

    const circle = (x, y, r) => {
        ctx.beginPath();
        ctx.arc(x, y, r, 0, 2 * Math.PI);
    }

    const fillCircle = (x, y, r, a = 1.0) => {
        ctx.save();
        ctx.fillStyle = `rgba(255, 255, 255, ${a})`;
        circle(x, y, r);
        ctx.fill();
        ctx.restore();
    }

    const square = (x, y, s) => {
        ctx.beginPath();
        ctx.rect(x - s / 2, y - s / 2, s, s);
    }

    const strokeSquare = (x, y, s, lw, a = 1.0) => {
        ctx.save();
        ctx.strokeStyle = `rgba(255, 255, 255, ${a})`;
        ctx.lineWidth = lw;
        square(x, y, s);
        ctx.stroke();
        ctx.restore();
    }

    const rotatedSquare = (x, y, s, deg) => {
        ctx.save();
        ctx.translate(x, y);
        ctx.rotate(deg * Math.PI / 180);
        square(0, 0, s);
        ctx.restore();
    }

    const strokeRotatedSquare = (x, y, s, deg, lw, a = 1.0) => {
        ctx.save();
        ctx.translate(x, y);
        ctx.rotate(deg * Math.PI / 180);
        ctx.strokeStyle = `rgba(255, 255, 255, ${a})`;
        ctx.lineWidth = lw;
        rotatedSquare(0, 0, s);
        ctx.stroke();
        ctx.restore();
    }

    const arc = (x, y, r, start, dd) => {
        start *= Math.PI / 180;
        ctx.beginPath();
        ctx.arc(x, y, r, start, start + dd * Math.PI / 180);
    }

    const strokeArc = (x, y, r, start, dd, lw, a = 1.0) => {
        ctx.save();
        ctx.strokeStyle = `rgba(255, 255, 255, ${a})`;
        ctx.lineWidth = lw;
        arc(x, y, r, start, dd);
        ctx.stroke();
        ctx.restore();
    }

    const size = 256;
    const real_size = size;
    resizeCanvas(real_size, real_size);
    ctx.scale(real_size, real_size);

    ctx.save();
    ctx.fillStyle = "white";

    const circ_1_size = (0.32 - 0.28 * tfs.easeOut(p, 5, 0.2));
    const circ_2_size = (0.03 + (0.1015625 - 0.03) * tfs.easeOut(p, 3)) * 2;

    const square_1_size = 0.7265625 * tfs.easeOut(p);
    const square_2_size = (0.7265625 * tfs.easeOut(p)) * 1.414 * 1.3;
    const square_2_lw = 0.17 * (1 - tfs.easeOut(p_slower, 5));

    const arc_size = 0.6171875 * tfs.easeOut(p) * 1.05;
    const arc_start = -135;
    const arc_dd = 45 * tfs.easeOut(p, 3);
    const arc_lw = (0.015 + 0.012 * tfs.easeOut(p)) * 0.8;
    const arc_a = p <= 0.6 ? 1 : 1 - (p - 0.6) / 0.4 * 0.3;

    strokeArc(
        0.5, 0.5,
        Math.max(0, arc_size / 2 - arc_lw),
        arc_start + arc_dd,
        90, arc_lw, arc_a
    )

    strokeArc(
        0.5, 0.5,
        Math.max(0, arc_size / 2 - arc_lw),
        arc_start + arc_dd + 180,
        90, arc_lw, arc_a
    )

    strokeSquare(0.5, 0.5, square_1_size, 0.01 - (p <= 0.7 ? 0 : (0.006 * tfs.easeOut((p - 0.7) / 0.3, 2))));
    strokeRotatedSquare(0.5, 0.5, Math.max(0, square_2_size / 2 - square_2_lw), 45, square_2_lw, 0.525);
    fillCircle(0.5, 0.5, circ_2_size / 2, 0.3);
    fillCircle(0.5, 0.5, circ_1_size / 2);

    ctx.restore();

    const imgdata = ctx.getImageData(0, 0, real_size, real_size);
    const getindex = (x, y) => (y * real_size + x) * 4;

    for (let i = 0; i < real_size; i++) {
        for (let j = 0; j < real_size; j++) {
            const index = getindex(i, j);
            const r = imgdata.data[index];
            const g = imgdata.data[index + 1];
            const b = imgdata.data[index + 2];
            const a = imgdata.data[index + 3];

            const p_ = (i + 1) / real_size * (j + 1) / real_size;
            const x = 0.7 + 0.5 * p_;
            const ax_bound = 0.74;

            imgdata.data.set([
                r * x,
                g * x,
                b * x,
                a * (p <= ax_bound ? 1 : 1 - (p - ax_bound) / (1 - ax_bound))
            ], index);
        }
    }

    ctx.putImageData(imgdata, 0, 0);

    const himg = this.helper_imgs[parseInt(p * this.helper_imgs.length)];
    if (himg && himg.loaded) {
        $(".hit_fx_helper").width = real_size;
        $(".hit_fx_helper").height = real_size;
        $(".hit_fx_helper").getContext("2d").drawImage(himg, 0, 0, real_size, real_size);
    }
}