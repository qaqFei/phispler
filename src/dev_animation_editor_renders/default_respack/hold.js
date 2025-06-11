function render() {
    const {
        ctx,
        note_deg
    } = this;
    
    const scale = this.note_draw_render_scale;

    const get_dpower = (w, h) => this.get_dpower(w, h, note_deg);

    const [w, h] = [989, 2000];
    resizeCanvas(w * scale, h * scale);
    ctx.scale(scale, scale);

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
    
    const hold_gradient = ctx.createLinearGradient(0, end_head_height, 0, h - end_head_height);
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
}