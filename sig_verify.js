// 原版 JS 签名实现（照抄 plasta2steel/dsh-xiaoheihe lib/index.js）用于交叉验证
const crypto = require("crypto");
const ALPHABET = "AB45STUVWZEFGJ6CH01D237IXYPQRKLMN89";
function md5hex(input) {
  return crypto.createHash("md5").update(input, "utf8").digest("hex");
}
function vm(e) { return 128 & e ? 255 & ((e << 1) ^ 27) : e << 1; }
function qm(e) { return vm(e) ^ e; }
function dollarM(e) { return qm(vm(e)); }
function ym(e) { return dollarM(qm(vm(e))); }
function gm(e) { return ym(e) ^ dollarM(e) ^ qm(e); }
function km(e) {
  const t = [0, 0, 0, 0];
  t[0] = gm(e[0]) ^ ym(e[1]) ^ dollarM(e[2]) ^ qm(e[3]);
  t[1] = qm(e[0]) ^ gm(e[1]) ^ ym(e[2]) ^ dollarM(e[3]);
  t[2] = dollarM(e[0]) ^ qm(e[1]) ^ gm(e[2]) ^ ym(e[3]);
  t[3] = ym(e[0]) ^ dollarM(e[1]) ^ qm(e[2]) ^ gm(e[3]);
  e[0] = t[0]; e[1] = t[1]; e[2] = t[2]; e[3] = t[3];
  return e;
}
function av(text, alphabet, offset) {
  let result = "";
  const sliced = alphabet.slice(0, offset);
  for (let i = 0; i < text.length; i++) {
    result += sliced[text.charCodeAt(i) % sliced.length];
  }
  return result;
}
function sv(text, alphabet) {
  let result = "";
  for (let i = 0; i < text.length; i++) {
    result += alphabet[text.charCodeAt(i) % alphabet.length];
  }
  return result;
}
function interleave(arr) {
  let result = "";
  const maxLen = Math.max(...arr.map((s) => s.length));
  for (let i = 0; i < maxLen; i++) {
    for (const s of arr) {
      if (i < s.length) result += s[i];
    }
  }
  return result;
}
function ov(path, timestamp, nonce) {
  const normalizedPath = "/" + path.split("/").filter((s) => s).join("/") + "/";
  const encT = av(String(timestamp), ALPHABET, -2);
  const encP = sv(normalizedPath, ALPHABET);
  const encN = sv(nonce, ALPHABET);
  const interleaved = interleave([encT, encP, encN]).slice(0, 20);
  const hash = md5hex(interleaved);
  const last6 = hash.slice(-6).split("").map((ch) => ch.charCodeAt(0));
  const transformed = km([...last6]);
  let checksum = String(transformed.reduce((sum, val) => sum + val, 0) % 100);
  if (checksum.length < 2) checksum = "0" + checksum;
  const prefix = av(hash.substring(0, 5), ALPHABET, -4);
  return prefix + checksum;
}
// 命令行: node sig_verify.js <path> <timestamp> <nonce>
const [path, ts, nonce] = process.argv.slice(2);
console.log(ov(path, parseInt(ts), nonce));
