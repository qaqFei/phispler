CanvasRenderingContext2D.prototype.drawRotateImage = function(im, x, y, width, height, deg, alpha) { // draw at the position center
    this.save();
    this.globalAlpha *= alpha;
    if (!!deg) {
        this.translate(x, y);
        this.rotate(deg * Math.PI / 180);
        this.drawImage(im, -width / 2, -height / 2, width, height);
    } else {
        this.drawImage(im, x - width / 2, y - height / 2, width, height);
    }
    this.restore();
}

CanvasRenderingContext2D.prototype.drawAnchorESRotateImage = function(im, x, y, width, height, deg, alpha) {
    this.save();
    this.globalAlpha *= alpha;
    if (!!deg) {
        this.translate(x, y);
        this.rotate(deg * Math.PI / 180);
        this.drawImage(im, -width / 2, -height, width, height);
    } else {
        this.drawImage(im, x - width / 2, y - height, width, height);
    }
    this.restore();
}

CanvasRenderingContext2D.prototype.drawScaleImage = function(im, x, y, width, height, xs, ys) {
    x += width / 2; y += height / 2;
    this.save();
    this.translate(x, y);
    this.scale(xs, ys);
    this.drawImage(im, -width / 2, -height / 2, width, height);
    this.restore();
}

CanvasRenderingContext2D.prototype.drawRPEMultipleRotateText = function(text, x, y, deg, fontsize, color, xs, ys) {
    this.save();
    this.translate(x, y);
    this.rotate(deg * Math.PI / 180);
    this.scale(xs, ys);
    this.fillStyle = color;
    this.textAlign = "center";
    this.textBaseline = "middle";
    this.font = `${fontsize}px pgrFont`;

    if (text.includes("\n") && RPEVersion >= 150) {
        let texts = text.split("\n");
        let x = 0.0; let y = 0.0;
        for (let currtext of texts) {
            if (currtext) this.fillText(currtext, x, y);
            let measure = this.measureText(currtext);
            y += (measure.actualBoundingBoxDescent + measure.actualBoundingBoxAscent) * 1.25;
        }
    }
    else {
        this.fillText(text, 0, 0);
    }

    this.restore();
}

CanvasRenderingContext2D.prototype.drawRotateText = function(text, x, y, deg, fontsize, color, xscale, yscale) {
    this.save();
    this.translate(x, y);
    this.rotate(deg * Math.PI / 180);
    this.scale(xscale, yscale);
    this.fillStyle = color;
    this.textAlign = "center";
    this.textBaseline = "middle";
    this.font = `${fontsize}px pgrFont`;
    this.fillText(text, 0, 0);
    this.restore();
}

CanvasRenderingContext2D.prototype.drawAlphaImage = function(im, x, y, width, height, alpha) {
    this.save()
    this.globalAlpha *= alpha;
    this.drawImage(im, x, y, width, height);
    this.restore();
}

CanvasRenderingContext2D.prototype.drawAlphaCenterImage = function(im, x, y, width, height, alpha) {
    this.save()
    this.globalAlpha *= alpha;
    this.drawImage(im, x - width / 2, y - height / 2, width, height);
    this.restore();
}

CanvasRenderingContext2D.prototype.drawTextEx = function(text, x, y, font, color, align, baseline) {
    this.save();
    this.fillStyle = color;
    this.textAlign = align;
    this.textBaseline = baseline;
    this.font = font;
    this.fillText(text, x, y);
    this.restore();
}

CanvasRenderingContext2D.prototype.fillRectEx = function(x, y, w, h, color) {
    this.save();
    this.fillStyle = color;
    this.fillRect(x, y, w, h);
    this.restore();
}

CanvasRenderingContext2D.prototype.fillRectExConvert2LeftCenter = function(x, y, w, h, color) {
    y += h / 2;
    this.save();
    this.fillStyle = color;
    this.beginPath();
    this.moveTo(x, y - h / 2);
    this.lineTo(x + w, y - h / 2);
    this.lineTo(x + w, y + h / 2);
    this.lineTo(x, y + h / 2);
    this.closePath();
    this.fill();
    this.restore();
}

CanvasRenderingContext2D.prototype.fillRectExByRect = function(x0, y0, x1, y1, color) {
    return this.fillRectEx(x0, y0, x1 - x0, y1 - y0, color);
}

CanvasRenderingContext2D.prototype.strokeRectEx = function(x, y, w, h, color, width) {
    this.save();
    this.strokeStyle = color;
    this.lineWidth = width;
    this.strokeRect(x, y, w, h);
    this.restore();
}

CanvasRenderingContext2D.prototype.strokeRectEx = function(x, y, w, h, color, width) {
    this.save();
    this.strokeStyle = color;
    this.lineWidth = width;
    this.strokeRect(x, y, w, h);
    this.restore();
}

CanvasRenderingContext2D.prototype.addRoundRectData = function(x, y, w, h, r) {
    if (this._roundDatas == undefined) this._roundDatas = [];
    this._roundDatas.push({ x: x, y: y, w: w, h: h, r: r });
}

CanvasRenderingContext2D.prototype.drawRoundDatas = function(color) {
    if (this._roundDatas) {
        this.roundRectsEx(color, this._roundDatas);
        this._roundDatas = undefined;
    }
}

CanvasRenderingContext2D.prototype.roundRectsEx = function(color, datas) {
    this.save();
    this.fillStyle = color;
    this.beginPath();
    for (let i of datas) {
        this.roundRect(i.x, i.y, i.w, i.h, i.r);
    }
    this.fill();
    this.restore();
}

CanvasRenderingContext2D.prototype.drawLineEx = function(x1, y1, x2, y2, width, color) {
    this.save();
    this.strokeStyle = color;
    this.lineWidth = width;
    this.beginPath();
    this.moveTo(x1, y1);
    this.lineTo(x2, y2);
    this.stroke();
    this.restore();
}

CanvasRenderingContext2D.prototype.diagonalRectangle = function(x0, y0, x1, y1, power) {
    // x0 = Math.floor(x0);
    // y0 = Math.floor(y0);
    // x1 = Math.floor(x1);
    // y1 = Math.floor(y1);
    this.moveTo(x0 + (x1 - x0) * power, y0);
    this.lineTo(x1, y0);
    this.lineTo(x1 - (x1 - x0) * power, y1);
    this.lineTo(x0, y1);
    this.lineTo(x0 + (x1 - x0) * power, y0);
}

CanvasRenderingContext2D.prototype.clipDiagonalRectangle = function(x0, y0, x1, y1, power) {
    this.beginPath();
    this.diagonalRectangle(x0, y0, x1, y1, power);
    this.clip();
}

CanvasRenderingContext2D.prototype.clipRect = function(x0, y0, x1, y1) {
    this.beginPath();
    this.rect(x0, y0, x1 - x0, y1 - y0);
    this.clip();
}

CanvasRenderingContext2D.prototype.drawClipXText = function(text, x, y, align, baseline, color, font, clipx0, clipx1) {
    this.save();
    this.clipRect(clipx0, 0, clipx1, this.canvas.height);
    this.fillStyle = color;
    this.textAlign = align;
    this.textBaseline = baseline;
    this.font = font;
    this.fillText(text, x, y);
    this.restore();
}

CanvasRenderingContext2D.prototype.drawDiagonalRectangle = function(x0, y0, x1, y1, power, color) {
    this.save();
    this.fillStyle = color;
    this.beginPath();
    this.diagonalRectangle(x0, y0, x1, y1, power);
    this.fill();
    this.restore();
}

CanvasRenderingContext2D.prototype.drawDiagonalRectangleShadow = function(x0, y0, x1, y1, power, color, shadowColor, shadowBlur) {
    this.save();
    this.shadowColor = shadowColor;
    this.shadowBlur = shadowBlur;
    this.fillStyle = color;
    this.beginPath();
    this.diagonalRectangle(x0, y0, x1, y1, power);
    this.fill();
    this.restore();
}

CanvasRenderingContext2D.prototype.drawDiagonalDialogRectangleText = function(x0, y0, x1, y1, power, text1, text2, color, font) {
    this.save();
    this.fillStyle = color;
    this.font = font;
    this.textBaseline = "middle";
    this.textAlign = "left";
    this.fillText(text1, x0 + (x1 - x0) * power * 3.0, y0 + (y1 - y0) * 0.5);
    this.textAlign = "right";
    this.fillText(text2, x1 - (x1 - x0) * power * 2.0, y0 + (y1 - y0) * 0.5);
    this.restore();
}

CanvasRenderingContext2D.prototype.drawDiagonalRectangleClipImage = function(x0, y0, x1, y1, im, imx, imy, imw, imh, power, alpha) {
    if (alpha == 0.0) return;
    this.save();
    this.globalAlpha *= alpha;
    this.beginPath();
    this.diagonalRectangle(x0, y0, x1, y1, power);
    this.clip();
    this.drawImage(im, x0 + imx, y0 + imy, imw, imh);
    this.restore();
}

CanvasRenderingContext2D.prototype.drawDiagonalRectangleCoverClipImage = function(x0, y0, x1, y1, im, power, alpha) {
    if (alpha == 0.0) return;
    this.save();
    this.globalAlpha *= alpha;
    this.beginPath();
    this.diagonalRectangle(x0, y0, x1, y1, power);
    this.clip();
    this.drawCoverFullScreenImage(im, x1 - x0, y1 - y0, x0, y0);
    this.restore();
}

CanvasRenderingContext2D.prototype.drawGrd = function(grdpos, steps, x0, y0, x1, y1) {
    const grd = this.createLinearGradient(...grdpos);
    for (const step of steps) {
        grd.addColorStop(...step);
    }

    // x0 = Math.floor(x0);
    // y0 = Math.floor(y0);
    // x1 = Math.floor(x1);
    // y1 = Math.floor(y1);
    this.save();
    this.fillStyle = grd;
    this.fillRect(x0, y0, x1 - x0, y1 - y0);
    this.restore();
}

CanvasRenderingContext2D.prototype.drawDiagonalGrd = function(x0, y0, x1, y1, power, steps, grdpos) {
    this.save();
    this.beginPath();
    this.diagonalRectangle(x0, y0, x1, y1, power);
    this.clip();
    this.drawGrd(grdpos, steps, x0, y0, x1, y1);
    this.restore();
}

CanvasRenderingContext2D.prototype.drawDiagonalRectangleClipImageOnlyHeight = function(x0, y0, x1, y1, im, imh, power, alpha) {
    const [irw, irh] = [
        im.__drawImage__ ? im.__drawImage__().width : im.width,
        im.__drawImage__ ? im.__drawImage__().height : im.height
    ]

    let imw = imh * irw / irh;

    if (imw < x1 - x0) {
        imw = x1 - x0;
        imh = imw * irh / irw;
    }

    if (isNaN(imw) || isNaN(imh)){
        imw = this.canvas.width;
        imh = this.canvas.height;
    }

    let imx = (x1 - x0) / 2 - imw / 2;
    let imy = (y1 - y0) / 2 - imh / 2;
    return this.drawDiagonalRectangleClipImage(x0, y0, x1, y1, im, imx, imy, imw, imh, power, alpha);
}

CanvasRenderingContext2D.prototype.drawDiagonalRectangleClipImageOnlyWidth = function(x0, y0, x1, y1, im, imw, power, alpha) {
    const [irw, irh] = [
        im.__drawImage__ ? im.__drawImage__().width : im.width,
        im.__drawImage__ ? im.__drawImage__().height : im.height
    ]

    let imh = imw / irw * irh;

    if (imh < y1 - y0) {
        imh = y1 - y0;
        imw = imh / irh * irw;
    }

    if (isNaN(imw) || isNaN(imh)){
        imw = this.canvas.width;
        imh = this.canvas.height;
    }

    let imx = (x1 - x0) / 2 - imw / 2;
    let imy = (y1 - y0) / 2 - imh / 2;
    return this.drawDiagonalRectangleClipImage(x0, y0, x1, y1, im, imx, imy, imw, imh, power, alpha);
}

CanvasRenderingContext2D.prototype.drawRotateText2 = function(text, x, y, deg, color, font, align, baseline) {
    this.save();
    this.translate(x, y);
    this.rotate(deg * Math.PI / 180);
    this.fillStyle = color;
    this.textAlign = align;
    this.textBaseline = baseline;
    this.font = font;
    this.fillText(text, 0, 0);
    this.restore();
}

CanvasRenderingContext2D.prototype.drawTriangleFrame = function(x0, y0, x1, y1, x2, y2, color, width) {
    this.save();
    this.strokeStyle = color;
    this.lineWidth = width;
    this.beginPath();
    this.moveTo(x0, y0);
    this.lineTo(x1, y1);
    this.lineTo(x2, y2);
    this.closePath();
    this.stroke();
    this.restore();
}

CanvasRenderingContext2D.prototype.drawRectMultilineText = function(x0, y0, x1, y1, text, color, font, fontsize, lineOffsetScale) {
    this.save();

    this.font = font;
    this.fillStyle = color;
    this.textBaseline = "top";
    this.textAlign = "left";
    let texts = splitText(x0, y0, x1, y1, text, this);

    this.rect(x0, y0, x1 - x0, y1 - y0);
    let dy = 0.0;

    for (let i = 0; i < texts.length; i++) {
        this.fillText(texts[i], x0, y0 + dy);
        dy += fontsize * lineOffsetScale;
        if (dy >= (y1 - y0)) break;
    }

    this.restore();
    return texts.length * fontsize * lineOffsetScale;
}

CanvasRenderingContext2D.prototype.drawRectMultilineTextDiagonal = function(x0, y0, x1, y1, text, color, font, fontsize, lineDiagonal, lineOffsetScale) {
    this.save();

    this.font = font;
    this.fillStyle = color;
    this.textBaseline = "top";
    this.textAlign = "left";
    let texts = splitText(x0, y0, x1, y1, text, this);

    this.rect(x0, y0, x1 - x0, y1 - y0);
    let dx = 0.0;
    let dy = 0.0;

    for (let i = 0; i < texts.length; i++) {
        if (texts[i]) {
            this.fillText(texts[i], x0 + dx, y0 + dy);
            dy += fontsize * lineOffsetScale;
            dx += lineDiagonal;
        } else {
            dx += lineDiagonal * 0.5;
            dy += fontsize * lineOffsetScale * 0.5;
        }
        if (dy >= (y1 - y0)) break;
    }

    this.restore();
    return texts.length * fontsize * lineOffsetScale;
}

CanvasRenderingContext2D.prototype.drawRectMultilineTextCenter = function(x0, y0, x1, y1, text, color, font, fontsize, lineOffsetScale) {
    this.save();

    this.font = font;
    this.fillStyle = color;
    this.textBaseline = "top";
    this.textAlign = "center";
    let texts = splitText(x0, y0, x1, y1, text, this);

    this.rect(x0, y0, x1 - x0, y1 - y0);
    let dy = 0.0;

    for (let i = 0; i < texts.length; i++) {
        this.fillText(texts[i], x0 + (x1 - x0) / 2, y0 + dy);
        dy += fontsize * lineOffsetScale;
        if (dy >= (y1 - y0)) break;
    }

    this.restore();
    return texts.length * fontsize * lineOffsetScale;
}

CanvasRenderingContext2D.prototype.drawUIItems = function(datas) {
    for (let i of datas) {
        if (i == null) continue;

        if (i.type == "text") {
            this.save();
            this.font = `${i.weight ? `${i.weight} ` : ""}${i.fontsize}px pgrFont`;
            this.textBaseline = i.textBaseline;
            this.textAlign = i.textAlign;
            this.fillStyle = i.color;
            this.translate(i.x + i.dx, i.y + i.dy);
            if (i.sx != 1.0 || i.sy != 1.0) this.scale(i.sx, i.sy);
            if (i.rotate != 0.0) this.rotate(i.rotate * Math.PI / 180);
            this.fillText(i.text, 0, 0);
            this.restore();
        }
        else if (i.type == "image") {
            this.save();
            const img = eval(i.image);
            const [r, g, b, a] = i.color;
            this.translate(i.x + i.dx, i.y + i.dy);
            if (i.rotate != 0.0) this.rotate(i.rotate * Math.PI / 180);
            if (a != 1.0) this.globalAlpha = a;
            if (r != 255 || g != 255 || b != 255) {
                setColorMatrix(r, g, b);
                this.filter = "url(#textureLineColorFilter)";
            }
            this.drawImage(img, 0, 0, i.width, i.height);
            this.restore();
        }
        else if (i.type == "call") {
            this[i.name](...i.args);
        }
        else if (i.type == "pbar") {
            const { w, pw, process } = i;

            this.save();
            // if (i.dx != 0.0 || i.dy != 0.0) this.translate(i.dx, i.dy);
            // if (i.rotate != 0.0) this.rotate(i.rotate * Math.PI / 180);
            // if (i.scale != 0.0) this.scale(i.sx, i.sy);

            const [r, g, b, a] = i.color.split("(")[1].split(")")[0].split(", ");
            this.fillRectExConvert2LeftCenter(0, 0, w * process, pw, `rgba(${145 * r / 255}, ${145 * g / 255}, ${145 * b / 255}, ${0.85 * a})`);
            this.fillRectExConvert2LeftCenter(w * process - w * 0.00175, 0, w * 0.00175, pw, `rgba(${r}, ${g}, ${b}, ${0.9 * a})`);
            this.restore();
        }
    }
}

CanvasRenderingContext2D.prototype.drawCoverFullScreenImage = function (img, w, h, x = 0, y = 0) {
    let [imw, imh] = [img.width, img.height];
    const ratio = w / h;
    const imratio = imw / imh;

    if (imratio > ratio) {
        imh = h;
        imw = imh * imratio;
    } else {
        imw = w;
        imh = imw / imratio;
    }

    const [imx, imy] = [(w - imw) / 2, (h - imh) / 2];

    this.save();
    this.beginPath();
    this.rect(x, y, w, h);
    this.clip();

    this.drawImage(img, x + imx, y + imy, imw, imh);

    this.restore();
    return [imx, imy, imw, imh];
}

CanvasRenderingContext2D.prototype.outOfTransformDrawCoverFullscreenChartBackgroundImage = function (img) {
    this.save();
    this.resetTransform();
    const [imx, imy, imw, imh] = this.drawCoverFullScreenImage(img, this.canvas.width, this.canvas.height);
    this.fillRectEx(imx, imy, imw, imh, `rgba(0.1, 0.1, 0.1, 0.7)`);
    this.restore();
}

CanvasRenderingContext2D.prototype.drawMirrorImage = function (img, x, y, width, height, alpha) {
    this.save();
    this.translate(x + width, y);
    this.scale(-1, 1);
    this.globalAlpha = alpha;
    this.drawImage(img, 0, 0, width, height);
    this.restore();
}

CanvasRenderingContext2D.prototype.drawMirrorRotateImage = function (img, x, y, width, height, rotate, alpha) {
    this.save();
    this.translate(x + width, y);
    this.rotate(rotate * Math.PI / 180);
    this.scale(-1, 1);
    this.globalAlpha = alpha;
    this.drawImage(img, width / 2, -height / 2, width, height);
    this.restore();
}

CanvasRenderingContext2D.prototype.getTextSize = function (text, font) {
    this.save();
    this.font = font;
    const measure = this.measureText(text);
    this.restore();
    return [measure.width, measure.actualBoundingBoxAscent + measure.actualBoundingBoxDescent];
}

CanvasRenderingContext2D.prototype.setShadow = function (color, blur, dx = 0, dy = 0) {
    this.save();
    this.shadowColor = color;
    this.shadowBlur = blur;
    this.shadowOffsetX = dx;
    this.shadowOffsetY = dy;
}

CanvasRenderingContext2D.prototype.mirror = function () {
    this.save();
    this.scale(-1, 1);
    this.translate(-this.canvas.width, 0);
    this.drawImage(this.canvas, 0, 0);
    this.restore();
}

CanvasRenderingContext2D.prototype.drawLeftBottomSkewText = function (text, x, y, font, color, dpower) {
    this.save();
    this.fillStyle = color;
    this.font = font;
    this.textAlign = "left";
    this.textBaseline = "bottom";
    const [text_w, text_h] = this.getTextSize(text, font);
    let skew_ratio = text_w * dpower / text_h;
    this.transform(
        1.0, 0.0, -skew_ratio,
        1.0, x, y
    );
    this.fillText(text, 0, 0);
    this.restore();
}

CanvasRenderingContext2D.prototype.clear = function() {
    this.save();
    this.setTransform(1, 0, 0, 1, 0, 0);
    this.clearRect(0, 0, this.canvas.width, this.canvas.height);
    this.restore();
}
