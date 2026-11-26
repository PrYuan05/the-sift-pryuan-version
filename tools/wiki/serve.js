// Local preview of docs/wiki: node tools/wiki/serve.js [port]  ->  http://127.0.0.1:8765
const http = require("http");
const fs = require("fs");
const path = require("path");
const root = path.resolve(__dirname, "../../docs/wiki");
const port = +(process.argv[2] || 8765);
const types = { ".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".css": "text/css; charset=utf-8",
  ".json": "application/json", ".png": "image/png", ".jpg": "image/jpeg", ".svg": "image/svg+xml" };
http.createServer((req, res) => {
  const rel = decodeURIComponent(req.url.split("?")[0]).replace(/^\/+/, "") || "index.html";
  const file = path.resolve(root, rel);
  if (!file.startsWith(root)) { res.writeHead(403); return res.end(); }
  fs.readFile(file, (err, buf) => {
    if (err) { res.writeHead(404); return res.end("not found"); }
    res.writeHead(200, { "Content-Type": types[path.extname(file)] || "application/octet-stream", "Content-Length": buf.length,
      "Cache-Control": "no-store" });
    res.end(buf);
  });
}).listen(port, "127.0.0.1", () => console.log(`wiki: http://127.0.0.1:${port}`));
