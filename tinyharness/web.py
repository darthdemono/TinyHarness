"""One-page chat UI: GET / serves the page, POST /chat {sid, message, images} streams NDJSON {t: token}."""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PAGE = """<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>tinyharness</title>
<style>body{font:16px system-ui;max-width:42rem;margin:0 auto;padding:1rem;background:#0e0e0e;color:#eee}
#log div{margin:.5rem 0;padding:.6rem .8rem;border-radius:.5rem;white-space:pre-wrap}.u{background:#222}.a{background:#1b2a14}
form{display:flex;gap:.5rem;flex-wrap:wrap}input[type=text]{flex:1;min-width:10rem}button,input{font:inherit;padding:.5rem}</style>
<h1>tinyharness</h1><div id=log></div>
<form id=f><input id=m type=text placeholder="Ask something" autofocus><input id=i type=file accept="image/*"><button>Send</button></form>
<script>
const log=document.getElementById('log'),sid=Math.random().toString(36).slice(2);
function add(c,t){const d=document.createElement('div');d.className=c;d.textContent=t;log.append(d);return d}
f.onsubmit=async e=>{e.preventDefault();const text=m.value;if(!text)return;m.value='';add('u',text);
 let images=[];if(i.files[0]){images=[await new Promise(r=>{const x=new FileReader();x.onload=()=>r(x.result.split(',')[1]);x.readAsDataURL(i.files[0])})];i.value=''}
 const w=add('a','...');
 try{const r=await fetch('/chat',{method:'POST',body:JSON.stringify({sid,message:text,images})});
  const rd=r.body.getReader(),dec=new TextDecoder();let buf='',out='';
  for(;;){const {done,value}=await rd.read();if(done)break;buf+=dec.decode(value,{stream:true});
   const lines=buf.split('\n');buf=lines.pop();
   for(const l of lines){if(!l)continue;const m=JSON.parse(l);if(m.t){out+=m.t;w.textContent=out}else if(m.error){w.textContent='error: '+m.error}}}}
 catch(err){w.textContent='error: '+err}};
</script>"""


MAX_SESSIONS = 50


def make_server(factory, host="127.0.0.1", port=8080):
    """factory() -> a fresh Agent. Each browser tab gets its own conversation (oldest evicted past 50)."""
    agents = {}

    def agent_for(sid):
        if sid not in agents:
            if len(agents) >= MAX_SESSIONS:
                agents.pop(next(iter(agents)))
            agents[sid] = factory()
        return agents[sid]

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
            self.send_response(200)
            self.send_header("Content-Type", "application/x-ndjson")
            self.end_headers()  # no Content-Length: the body streams until the connection closes
            try:
                req = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                agent_for(str(req.get("sid", ""))).run(
                    req["message"], images=req.get("images") or None, on_token=lambda t: self._line({"t": t})
                )
            except Exception as e:
                self._line({"error": str(e)})

        def _line(self, obj):
            self.wfile.write((json.dumps(obj) + "\n").encode())
            self.wfile.flush()

        def log_message(self, *a):
            pass

    return ThreadingHTTPServer((host, port), H)
