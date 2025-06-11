function render() {
    const {
        ctx,
        note_deg
    } = this;
    
    const scale = this.note_draw_render_scale;

    const get_dpower = (w, h) => this.get_dpower(w, h, note_deg);

    const [w, h] = [989, 60];
    resizeCanvas(w * scale, h * scale);
    ctx.scale(scale, scale);

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
}