import * as QRCode from "qrcode";

export function parseColor(colorStr: string): [number, number, number, number] {
  colorStr = colorStr.trim();
  if (colorStr.startsWith("#")) {
    const hex = colorStr.slice(1);
    if (hex.length === 6) {
      const r = parseInt(hex.slice(0, 2), 16);
      const g = parseInt(hex.slice(2, 4), 16);
      const b = parseInt(hex.slice(4, 6), 16);
      return [r, g, b, 255];
    } else if (hex.length === 8) {
      const r = parseInt(hex.slice(0, 2), 16);
      const g = parseInt(hex.slice(2, 4), 16);
      const b = parseInt(hex.slice(4, 6), 16);
      const a = parseInt(hex.slice(6, 8), 16);
      return [r, g, b, a];
    }
  } else if (colorStr.includes(",")) {
    const parts = colorStr.split(",").map(p => parseInt(p.trim(), 10));
    if (parts.every(p => !isNaN(p))) {
      if (parts.length === 3) {
        return [parts[0], parts[1], parts[2], 255];
      } else if (parts.length === 4) {
        return [parts[0], parts[1], parts[2], parts[3]];
      }
    }
  }
  throw new Error(`Invalid color format: ${colorStr}`);
}

export function colorToSvg(color: [number, number, number, number] | string): string {
  if (typeof color === "string") {
    return color;
  }
  if (color.length >= 3) {
    const [r, g, b, a] = color;
    if (color.length === 4 && a === 0) {
      return "none";
    }
    const hexR = r.toString(16).padStart(2, "0");
    const hexG = g.toString(16).padStart(2, "0");
    const hexB = b.toString(16).padStart(2, "0");
    return `#${hexR}${hexG}${hexB}`;
  }
  return "#000000";
}

export function makeRoundedRectPath(
  x: number,
  y: number,
  w: number,
  h: number,
  r: number,
  corners: [boolean, boolean, boolean, boolean] // [TL, TR, BR, BL]
): string {
  const [c1, c2, c3, c4] = corners;

  let path = `M ${x},${y + (c1 ? r : 0)} `;
  path += `L ${x},${y + h - (c4 ? r : 0)} `;
  if (c4) {
    path += `Q ${x},${y + h} ${x + r},${y + h} `;
  } else {
    path += `L ${x},${y + h} `;
  }

  path += `L ${x + w - (c3 ? r : 0)},${y + h} `;
  if (c3) {
    path += `Q ${x + w},${y + h} ${x + w},${y + h - r} `;
  } else {
    path += `L ${x + w},${y + h} `;
  }

  path += `L ${x + w},{y + (c2 ? r : 0)} `;
  // Let's resolve the variable interpolate syntax error above: y should be ${y}
  path = `M ${x},${y + (c1 ? r : 0)} `;
  path += `L ${x},${y + h - (c4 ? r : 0)} `;
  if (c4) {
    path += `Q ${x},${y + h} ${x + r},${y + h} `;
  } else {
    path += `L ${x},${y + h} `;
  }

  path += `L ${x + w - (c3 ? r : 0)},${y + h} `;
  if (c3) {
    path += `Q ${x + w},${y + h} ${x + w},${y + h - r} `;
  } else {
    path += `L ${x + w},${y + h} `;
  }

  path += `L ${x + w},${y + (c2 ? r : 0)} `;
  if (c2) {
    path += `Q ${x + w},${y} ${x + w - r},${y} `;
  } else {
    path += `L ${x + w},${y} `;
  }

  path += `L ${x + (c1 ? r : 0)},${y} `;
  if (c1) {
    path += `Q ${x},${y} ${x},${y + r} `;
  } else {
    path += `L ${x},${y} `;
  }

  path += "Z";
  return path;
}

export function getLogoChildren(logoSvgStr: string): string {
  const svgContentMatch = logoSvgStr.match(/<svg[^>]*>([\s\S]*)<\/svg>/i);
  if (!svgContentMatch) return "";
  let content = svgContentMatch[1];
  
  // Strip editor metadata tags completely
  content = content.replace(/<sodipodi:namedview[\s\S]*?\/>/gi, "");
  content = content.replace(/<defs[\s\S]*?<\/defs>/gi, "");
  content = content.replace(/<defs[\s\S]*?\/>/gi, "");
  content = content.replace(/<metadata[\s\S]*?<\/metadata>/gi, "");
  content = content.replace(/<metadata[\s\S]*?\/>/gi, "");
  
  // Strip namespace prefixes from all XML attributes (e.g., inkscape:label, sodipodi:docname)
  // This cleans up or removes editor-specific attributes that cause XML namespace-prefix errors
  content = content.replace(/\s*(?:inkscape|sodipodi):[a-z0-9-]+="[^"]*"/gi, "");
  content = content.replace(/\s*(?:inkscape|sodipodi):[a-z0-9-]+='[^']*'/gi, "");
  
  // Also strip any other leftover elements with namespaces if any
  content = content.replace(/<[a-z0-9-]+:[a-z0-9-]+[^>]*\/>/gi, "");
  content = content.replace(/<[a-z0-9-]+:[a-z0-9-]+[\s\S]*?<\/[a-z0-9-]+:[a-z0-9-]+>/gi, "");

  return content.trim();
}

export function getLogoDimensions(logoSvgStr: string): { w: number; h: number } {
  const viewBoxMatch = logoSvgStr.match(/viewBox\s*=\s*["']\s*([-\d.]+)\s+([-\d.]+)\s+([\d.]+)\s+([\d.]+)\s*["']/i);
  if (viewBoxMatch) {
    return { w: parseFloat(viewBoxMatch[3]), h: parseFloat(viewBoxMatch[4]) };
  }
  const widthMatch = logoSvgStr.match(/width\s*=\s*["']\s*([\d.]+)(?:mm|px|em|pt|%)?\s*["']/i);
  const heightMatch = logoSvgStr.match(/height\s*=\s*["']\s*([\d.]+)(?:mm|px|em|pt|%)?\s*["']/i);
  if (widthMatch && heightMatch) {
    return { w: parseFloat(widthMatch[1]), h: parseFloat(heightMatch[1]) };
  }
  return { w: 1, h: 1 };
}

function drawEyePaths(
  row: number,
  col: number,
  mc: number,
  border: number,
  boxSize: number,
  cornersOuter: [boolean, boolean, boolean, boolean],
  cornersInner: [boolean, boolean, boolean, boolean],
  frontColorStr: string
): string {
  let paths = "";

  const x0 = (col + border) * boxSize;
  const y0 = (row + border) * boxSize;
  const wOuter = 7 * boxSize;
  const hOuter = 7 * boxSize;
  
  const halfBox = boxSize / 2;
  const ux0 = x0 + halfBox;
  const uy0 = y0 + halfBox;
  const wOuterInset = wOuter - boxSize;
  const hOuterInset = hOuter - boxSize;
  
  const rOuter = boxSize * 2 - halfBox;
  
  const outerPath = makeRoundedRectPath(ux0, uy0, wOuterInset, hOuterInset, rOuter, cornersOuter);
  paths += `  <path d="${outerPath}" fill="none" stroke="${frontColorStr}" stroke-width="${boxSize}" />\n`;

  const xInner = (col + 2 + border) * boxSize;
  const yInner = (row + 2 + border) * boxSize;
  const wInner = 3 * boxSize;
  const hInner = 3 * boxSize;
  const rInner = boxSize;
  
  const innerPath = makeRoundedRectPath(xInner, yInner, wInner, hInner, rInner, cornersInner);
  paths += `  <path d="${innerPath}" fill="${frontColorStr}" stroke="none" />\n`;

  return paths;
}

export function generateQrSvg(
  data: string,
  frontColor: [number, number, number, number],
  backColor: [number, number, number, number],
  boxSize: number = 100,
  errorCorrection: "L" | "M" | "Q" | "H" = "L",
  withLogo: boolean = false,
  logoScale: number = 1,
  logoMargin: number = 0.15,
  logoSvg?: string
): string {
  const qr = QRCode.create(data, { errorCorrectionLevel: errorCorrection });
  const mc = qr.modules.size;
  const border = 4;
  const pixelSize = (mc + 2 * border) * boxSize;

  const modulesMatrix: boolean[][] = [];
  for (let r = 0; r < mc; r++) {
    modulesMatrix[r] = [];
    for (let c = 0; c < mc; c++) {
      modulesMatrix[r][c] = qr.modules.get(r, c) === 1;
    }
  }

  let start = 0;
  let end = 0;
  let size = 0;
  if (withLogo) {
    size = Math.floor(mc * logoMargin);
    if (size % 2 === 0) {
      size += 1;
    }
    start = Math.floor((mc - size) / 2);
    end = start + size;

    for (let r = start; r < end; r++) {
      for (let c = start; c < end; c++) {
        modulesMatrix[r][c] = false;
      }
    }
  }

  let svg = `<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n`;
  svg += `<svg width="${pixelSize}" height="${pixelSize}" viewBox="0 0 ${pixelSize} ${pixelSize}" xmlns="http://www.w3.org/2000/svg">\n`;

  const bgStr = colorToSvg(backColor);
  if (bgStr !== "none") {
    svg += `  <rect width="${pixelSize}" height="${pixelSize}" fill="${bgStr}" />\n`;
  }

  const frontColorStr = colorToSvg(frontColor);

  const isEye = (r: number, c: number): boolean => {
    return (
      (r < 7 && c < 7) ||
      (r < 7 && c >= mc - 7) ||
      (r >= mc - 7 && c < 7)
    );
  };

  svg += drawEyePaths(0, 0, mc, border, boxSize, [true, true, false, true], [true, true, false, true], frontColorStr);
  svg += drawEyePaths(0, mc - 7, mc, border, boxSize, [true, true, true, false], [true, true, true, false], frontColorStr);
  svg += drawEyePaths(mc - 7, 0, mc, border, boxSize, [true, false, true, true], [true, false, true, true], frontColorStr);

  const verticalShrink = 0.8;
  const shrunkenH = boxSize * verticalShrink;
  const deltaY = (boxSize - shrunkenH) / 2;
  const overlap = boxSize * 0.02;

  for (let r = 0; r < mc; r++) {
    for (let c = 0; c < mc; c++) {
      if (isEye(r, c)) continue;
      if (!modulesMatrix[r][c]) continue;

      const x = (c + border) * boxSize;
      const y = (r + border) * boxSize;

      const isWActive = c > 0 && modulesMatrix[r][c - 1] && !isEye(r, c - 1);
      const isEActive = c < mc - 1 && modulesMatrix[r][c + 1] && !isEye(r, c + 1);

      const leftRounded = !isWActive;
      const rightRounded = !isEActive;

      let ux0 = x;
      let wVal = boxSize;

      if (!leftRounded) {
        ux0 -= overlap;
        wVal += overlap;
      }
      if (!rightRounded) {
        wVal += overlap;
      }

      const rVal = shrunkenH / 2;
      const pathD = makeRoundedRectPath(
        ux0,
        y + deltaY,
        wVal,
        shrunkenH,
        rVal,
        [leftRounded, rightRounded, rightRounded, leftRounded]
      );

      svg += `  <path d="${pathD}" fill="${frontColorStr}" />\n`;
    }
  }

  if (withLogo && logoSvg) {
    const { w: l_w, h: l_h } = getLogoDimensions(logoSvg);

    const ux0 = (start + border) * boxSize;
    const uy0 = (start + border) * boxSize;
    const targetW = size * boxSize;
    const targetH = size * boxSize;

    const scaleX = targetW / l_w;
    const scaleY = targetH / l_h;
    const scale = Math.min(scaleX, scaleY) * logoScale;

    const offX = ux0 + (targetW - l_w * scale) / 2;
    const offY = uy0 + (targetH - l_h * scale) / 2;

    const logoChildren = getLogoChildren(logoSvg);

    svg += `  <g transform="translate(${offX}, ${offY}) scale(${scale})">\n`;
    svg += `    ${logoChildren}\n`;
    svg += `  </g>\n`;
  }

  svg += `</svg>\n`;
  return svg;
}
