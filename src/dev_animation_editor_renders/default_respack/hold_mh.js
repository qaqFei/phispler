function render() {
    const {
        ctx,
        note_deg
    } = this;
    
    const scale = this.note_draw_render_scale;

    const get_dpower = (w, h) => this.get_dpower(w, h, note_deg);

    const [w, h] = [989, 2000];
    const [mh_w, mh_h] = [1250, 2100];
    resizeCanvas(mh_w * scale, mh_h * scale);
    ctx.scale(scale, scale);

    ctx.save();
    ctx.translate((mh_w - w) / 2, (mh_h - h) / 2);

    const end_head_height = 50;
    const body_height = h - end_head_height * 2;

    const head_color = [155, 233, 255, 1];
    const end_color = [255, 255, 255, 0.38];

    const lr_bar_width = 24;
    const lr_bar_item_height = end_head_height;
    const lr_bar_dpower = get_dpower(lr_bar_width, lr_bar_item_height);
    const lr_bar_dpower_width = lr_bar_width * lr_bar_dpower;

    const main_padx = 50 - lr_bar_width;

    ctx.save();
    ctx.beginPath();
    ctx.moveTo(lr_bar_dpower_width, 0);
    ctx.lineTo(lr_bar_dpower_width + lr_bar_width, 0);
    ctx.lineTo(lr_bar_width, end_head_height);
    ctx.lineTo(lr_bar_width, h - end_head_height);
    ctx.lineTo(lr_bar_dpower_width + lr_bar_width, h);
    ctx.lineTo(lr_bar_dpower_width, h);
    ctx.lineTo(0, h - end_head_height);
    ctx.lineTo(0, end_head_height);
    ctx.lineTo(lr_bar_dpower_width, 0);
    ctx.fillStyle = "white";
    ctx.fill();
    ctx.restore();

    ctx.save();
    ctx.beginPath();
    ctx.moveTo(w - lr_bar_dpower_width, 0);
    ctx.lineTo(w - lr_bar_dpower_width - lr_bar_width, 0);
    ctx.lineTo(w - lr_bar_width, end_head_height);
    ctx.lineTo(w - lr_bar_width, h - end_head_height);
    ctx.lineTo(w - lr_bar_dpower_width - lr_bar_width, h);
    ctx.lineTo(w - lr_bar_dpower_width, h);
    ctx.lineTo(w, h - end_head_height);
    ctx.lineTo(w, end_head_height);
    ctx.lineTo(w - lr_bar_dpower_width, 0);
    ctx.fillStyle = "white";
    ctx.fill();
    ctx.restore();
    
    const hold_gradient = ctx.createLinearGradient(0, 0, 0, h);
    hold_gradient.addColorStop(1, `rgba(${head_color.join(",")})`);
    hold_gradient.addColorStop(0, `rgba(${end_color.join(",")})`);

    ctx.save();
    ctx.beginPath();
    ctx.moveTo(lr_bar_dpower_width + lr_bar_width + main_padx, 0);
    ctx.lineTo(w - lr_bar_dpower_width - lr_bar_width - main_padx, 0);
    ctx.lineTo(w - lr_bar_width - main_padx, end_head_height);
    ctx.lineTo(w - lr_bar_width - main_padx, h - end_head_height);
    ctx.lineTo(w - lr_bar_dpower_width - lr_bar_width - main_padx, h);
    ctx.lineTo(lr_bar_dpower_width + lr_bar_width + main_padx, h);
    ctx.lineTo(lr_bar_width + main_padx, h - end_head_height);
    ctx.lineTo(lr_bar_width + main_padx, end_head_height);
    ctx.lineTo(lr_bar_dpower_width + lr_bar_width + main_padx, 0);
    ctx.fillStyle = hold_gradient;
    ctx.fill();
    ctx.restore();

    const temp_cv = document.createElement("canvas");
    temp_cv.width = ctx.canvas.width;
    temp_cv.height = ctx.canvas.height;
    temp_cv.getContext("2d").drawImage(ctx.canvas, 0, 0);

    ctx.clear();

    const shadow_rgb = "255, 255, 102";
    const shadow_loop_count = 2;

    const shadow_radient = ctx.createLinearGradient(0, 0, 0, h);
    shadow_radient.addColorStop(0, `rgba(${shadow_rgb}, 0.05)`);
    shadow_radient.addColorStop(0.7, `rgba(${shadow_rgb}, 0.3)`);
    shadow_radient.addColorStop(1, `rgba(${shadow_rgb}, 1.0)`);

    const rect_shadow = () => {
        ctx.beginPath();

        ctx.save();
        ctx.translate(0, h - end_head_height);
        ctx.moveTo(lr_bar_width + main_padx, 0);
        ctx.lineTo(w - lr_bar_width - main_padx, 0);
        ctx.lineTo(w - lr_bar_width - main_padx - lr_bar_dpower_width, end_head_height);
        ctx.lineTo(lr_bar_width + main_padx + lr_bar_dpower_width, end_head_height);
        ctx.lineTo(lr_bar_width + main_padx, 0);
        ctx.restore();

        ctx.moveTo(lr_bar_width + main_padx + lr_bar_dpower_width, 0);
        ctx.lineTo(w - lr_bar_width - main_padx - lr_bar_dpower_width, 0);
        ctx.lineTo(w - lr_bar_width - main_padx, end_head_height);
        ctx.lineTo(lr_bar_width + main_padx, end_head_height);
        ctx.lineTo(lr_bar_width + main_padx + lr_bar_dpower_width, 0);

        ctx.save();
        ctx.translate(0, end_head_height);
        ctx.moveTo(lr_bar_width + main_padx, 0);
        ctx.lineTo(w - lr_bar_width - main_padx, 0);
        ctx.lineTo(w - lr_bar_width - main_padx, body_height);
        ctx.lineTo(lr_bar_width + main_padx, body_height);
        ctx.lineTo(lr_bar_width + main_padx, 0);
        ctx.restore();
    };

    ctx.save();
    rect_shadow();
    ctx.fillStyle = shadow_radient;
    ctx.shadowColor = `rgba(${shadow_rgb}, 0.776)`;
    ctx.shadowBlur = (w + h) / 79 * scale;
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
    ctx.fillStyle = shadow_radient;
    ctx.fill();
    ctx.restore();

    ctx.resetTransform();
    ctx.drawImage(temp_cv, 0, 0);
    ctx.restore();
}