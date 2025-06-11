function render(p) {
    resizeCanvas(32 * p, 32 * p);
    ctx.fillRectEx(0, 0, 16, 16, "white");
    ctx.fillRectEx(16, 0, 16, 16, "rgb(128, 128, 128)");
    ctx.fillRectEx(0, 16, 16, 16, "rgb(128, 128, 128)");
    ctx.fillRectEx(16, 16, 16, 16, "white");
}
