import { deflateSync } from "node:zlib";
import { writeFileSync } from "node:fs";

const table = new Uint32Array(256);
for (let n = 0; n < 256; n += 1) {
  let c = n;
  for (let k = 0; k < 8; k += 1) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
  table[n] = c >>> 0;
}

function crc32(buffer) {
  let crc = 0xffffffff;
  for (const byte of buffer) crc = table[(crc ^ byte) & 0xff] ^ (crc >>> 8);
  return (crc ^ 0xffffffff) >>> 0;
}

function chunk(type, data) {
  const name = Buffer.from(type);
  const length = Buffer.alloc(4);
  length.writeUInt32BE(data.length);
  const crc = Buffer.alloc(4);
  crc.writeUInt32BE(crc32(Buffer.concat([name, data])));
  return Buffer.concat([length, name, data, crc]);
}

function png(size, pixel) {
  const rows = [];
  for (let y = 0; y < size; y += 1) {
    const row = Buffer.alloc(1 + size * 4);
    for (let x = 0; x < size; x += 1) {
      const [r, g, b, a] = pixel(x, y, size);
      const offset = 1 + x * 4;
      row.set([r, g, b, a], offset);
    }
    rows.push(row);
  }
  const ihdr = Buffer.alloc(13);
  ihdr.writeUInt32BE(size, 0);
  ihdr.writeUInt32BE(size, 4);
  ihdr.set([8, 6, 0, 0, 0], 8);
  return Buffer.concat([
    Buffer.from("89504e470d0a1a0a", "hex"),
    chunk("IHDR", ihdr),
    chunk("IDAT", deflateSync(Buffer.concat(rows))),
    chunk("IEND", Buffer.alloc(0)),
  ]);
}

function isF(x, y, size) {
  const left = x > size * 0.28 && x < size * 0.42 && y > size * 0.2 && y < size * 0.8;
  const top = x > size * 0.28 && x < size * 0.72 && y > size * 0.2 && y < size * 0.34;
  const middle = x > size * 0.28 && x < size * 0.62 && y > size * 0.43 && y < size * 0.56;
  return left || top || middle;
}

writeFileSync("teams_app/color.png", png(192, (x, y, size) =>
  isF(x, y, size) ? [255, 255, 255, 255] : [98, 100, 167, 255]
));
writeFileSync("teams_app/outline.png", png(32, (x, y, size) =>
  isF(x, y, size) ? [255, 255, 255, 255] : [0, 0, 0, 0]
));

