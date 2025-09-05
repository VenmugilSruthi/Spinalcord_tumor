import http.server
import socketserver

PORT = 8000

Handler = http.server.SimpleHTTPRequestHandler

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print("\n=======================================================")
    print(f"  Frontend server is running at http://127.0.0.1:{PORT}")
    print("  Open this URL in your browser to see your app.")
    print("=======================================================\n")
    httpd.serve_forever()

