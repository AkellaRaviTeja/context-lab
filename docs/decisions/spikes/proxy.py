"""A proxy that refuses everything and logs what was asked for. Port 8899."""
import socketserver, sys
LOG = sys.argv[1]
class H(socketserver.StreamRequestHandler):
    def handle(self):
        line = self.rfile.readline().decode(errors="replace").strip()
        open(LOG, "a").write(line + "\n")
        self.wfile.write(b"HTTP/1.1 403 Forbidden\r\nContent-Length: 0\r\n\r\n")
socketserver.ThreadingTCPServer.allow_reuse_address = True
socketserver.ThreadingTCPServer(("127.0.0.1", 8899), H).serve_forever()
