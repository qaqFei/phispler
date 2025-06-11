function render() {
    const {
        ctx,
        note_deg
    } = this;
    
    const scale = this.note_draw_render_scale;

    const get_dpower = (w, h) => this.get_dpower(w, h, note_deg);

    const [w, h] = [989, 60];
    const [mh_w, mh_h] = [1089, 160];
    resizeCanvas(mh_w * scale, mh_h * scale);
    ctx.scale(scale, scale);

    ctx.save();
    ctx.translate((mh_w - w) / 2, (mh_h - h) / 2);

    const lr_bar_width = 24;
    const lr_bar_item_height = h / 2;
    const lr_bar_dpower = get_dpower(lr_bar_width, lr_bar_item_height);
    const lr_bar_dpower_width = lr_bar_dpower * lr_bar_width;

    ctx.save();
    ctx.beginPath();
    ctx.moveTo(lr_bar_dpower_width, 0);
    ctx.lineTo(lr_bar_dpower_width + lr_bar_width, 0);
    ctx.lineTo(lr_bar_dpower_width + lr_bar_width - lr_bar_dpower_width, h / 2);
    ctx.lineTo(lr_bar_dpower_width + lr_bar_width, h);
    ctx.lineTo(lr_bar_dpower_width, h);
    ctx.lineTo(0, h / 2);
    ctx.lineTo(lr_bar_dpower_width, 0);
    ctx.fillStyle = "white";
    ctx.fill();
    ctx.restore();

    ctx.save();
    ctx.beginPath();
    ctx.moveTo(w - lr_bar_dpower_width, 0);
    ctx.lineTo(w, h / 2);
    ctx.lineTo(w - lr_bar_dpower_width, h);
    ctx.lineTo(w - lr_bar_dpower_width - lr_bar_width, h);
    ctx.lineTo(w - lr_bar_width, h / 2);
    ctx.lineTo(w - lr_bar_dpower_width - lr_bar_width, 0);
    ctx.lineTo(w - lr_bar_dpower_width, 0);
    ctx.fillStyle = "white";
    ctx.fill();
    ctx.restore();

    const main_padx = 25;

    ctx.save();
    ctx.beginPath();
    ctx.moveTo(lr_bar_dpower_width + lr_bar_width + main_padx, 0);
    ctx.lineTo(lr_bar_width + main_padx, h / 2);
    ctx.lineTo(lr_bar_dpower_width + lr_bar_width + main_padx, h);
    ctx.lineTo(w - lr_bar_dpower_width - lr_bar_width - main_padx, h);
    ctx.lineTo(w - lr_bar_width - main_padx, h / 2);
    ctx.lineTo(w - lr_bar_dpower_width - lr_bar_width - main_padx, 0);
    ctx.lineTo(lr_bar_dpower_width + lr_bar_width + main_padx, 0);
    ctx.fillStyle = "white";
    ctx.fill();
    ctx.restore();

    const inner_padx = 40;
    const inner_pady = 10;
    const inner_dpower_x = (h - inner_pady * 2) / h;

    ctx.save();
    ctx.beginPath();
    ctx.moveTo((lr_bar_dpower_width * inner_dpower_x) + lr_bar_width + main_padx + inner_padx, inner_pady);
    ctx.lineTo(lr_bar_width + main_padx + inner_padx, h / 2);
    ctx.lineTo((lr_bar_dpower_width * inner_dpower_x) + lr_bar_width + main_padx + inner_padx, h - inner_pady);
    ctx.lineTo(w - (lr_bar_dpower_width * inner_dpower_x) - lr_bar_width - main_padx - inner_padx, h - inner_pady);
    ctx.lineTo(w - lr_bar_width - main_padx - inner_padx, h / 2);
    ctx.lineTo(w - (lr_bar_dpower_width * inner_dpower_x) - lr_bar_width - main_padx - inner_padx, inner_pady);
    ctx.lineTo((lr_bar_dpower_width * inner_dpower_x) + lr_bar_width + main_padx + inner_padx, inner_pady);
    ctx.fillStyle = `rgb(${0xf0}, ${0xed}, ${0x69})`;
    ctx.fill();
    ctx.restore();

    const temp_cv = document.createElement("canvas");
    temp_cv.width = ctx.canvas.width;
    temp_cv.height = ctx.canvas.height;
    temp_cv.getContext("2d").drawImage(ctx.canvas, 0, 0);

    ctx.clear();
    
    const rect_shadow = () => {
        ctx.beginPath();
        ctx.moveTo(lr_bar_dpower_width, 0);
        ctx.lineTo(0, h / 2);
        ctx.lineTo(lr_bar_dpower_width, h);
        ctx.lineTo(w - lr_bar_dpower_width, h);
        ctx.lineTo(w, h / 2);
        ctx.lineTo(w - lr_bar_dpower_width, 0);
    };

    const shadow_rgb = "255, 255, 102";
    const shadow_loop_count = 2;

    ctx.save();
    rect_shadow();
    ctx.fillStyle = `rgb(${shadow_rgb})`;
    ctx.shadowColor = `rgba(${shadow_rgb}, 0.776)`;
    ctx.shadowBlur = (w + h) / 24 * scale;
    ctx.fill();
    ctx.restore();

    for (let i = 0; i < shadow_loop_count; i++) {
        ctx.save();
        ctx.resetTransform();
        ctx.drawImage(ctx.canvas, 0, 0);
        ctx.restore();
    }

    ctx.save();
    rect_shadow();
    ctx.globalCompositeOperation = "destination-out";
    ctx.fill();
    ctx.restore();

    ctx.save();
    rect_shadow();
    ctx.fillStyle = `rgba(${shadow_rgb}, 0.85)`;
    ctx.fill();
    ctx.restore();

    ctx.resetTransform();
    ctx.drawImage(temp_cv, 0, 0);
    ctx.restore();
}