"""One-page chat UI: GET / serves the page, POST /chat {message, images} returns {reply}."""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PAGE = """<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>hackbase</title>
<style>body{font:16px system-ui;max-width:42rem;margin:0 auto;padding:1rem;background:#0e0e0e;color:#eee}
#log div{margin:.5rem 0;padding:.6rem .8rem;border-radius:.5rem;white-space:pre-wrap}.u{background:#222}.a{background:#1b2a14}
form{display:flex;gap:.5rem;flex-wrap:wrap}input[type=text]{flex:1;min-width:10rem}button,input{font:inherit;padding:.5rem}</style>
<h1>hackbase</h1><div id=log></div>
<form id=f><input id=m type=text placeholder="Ask something" autofocus><input id=i type=file accept="image/*"><button>Send</button></form>
<script>
const log=document.getElementById('log');
function add(c,t){const d=document.createElement('div');d.className=c;d.textContent=t;log.append(d);return d}
f.onsubmit=async e=>{e.preventDefault();const text=m.value;if(!text)return;m.value='';add('u',text);
 let images=[];if(i.files[0]){images=[await new Promise(r=>{const x=new FileReader();x.onload=()=>r(x.result.split(',')[1]);x.readAsDataURL(i.files[0])})];i.value=''}
 const w=add('a','...');
 try{const r=await fetch('/chat',{method:'POST',body:JSON.stringify({message:text,images})});w.textContent=(await r.json()).reply}
 catch(err){w.textContent='error: '+err}};
</script>"""


def make_server(agent, host="127.0.0.1", port=8080):
    class H(BaseHTTPRequestHandler):
        def _send(self, code, ctype, data):
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            if self.path == "/":
                self._send(200, "text/html; charset=utf-8", PAGE.encode())
            else:
                self._send(404, "text/plain", b"not found")

        def do_POST(self):
            if self.path != "/chat":
                return self._send(404, "text/plain", b"not found")
            try:
                req = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                reply = agent.run(req["message"], images=req.get("images") or None)
            except Exception as e:
                reply = "error: %s" % e
            self._send(200, "application/json", json.dumps({"reply": reply}).encode())

        def log_message(self, *a):
            pass

    return ThreadingHTTPServer((host, port), H)
