"""Read-only standard-library research dashboard server."""

# Import copy for use in this module.
import copy
# Import json for use in this module.
import json
# Import threading for use in this module.
import threading
# Import BaseHTTPRequestHandler, ThreadingHTTPServer from http.server for the operations below.
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
# Import Path from pathlib for the operations below.
from pathlib import Path


# Set LATEST to a dictionary containing payload.
LATEST = {"payload": None}
# Set LOCK to the result of threading.Lock().
LOCK = threading.Lock()
# Set HTML_PATH to the result of Path(__file__).with_name(the text 'debug_dashboard.html').
HTML_PATH = Path(__file__).with_name("debug_dashboard.html")
# Set HTML to the text read from HTML_PATH.
HTML = HTML_PATH.read_text(encoding="utf-8")


# Define Handler to group the state and operations declared below.
# Base classes: BaseHTTPRequestHandler.
# Instances expose the attributes and methods implemented in this class.
class Handler(BaseHTTPRequestHandler):
    # Do GET using the inputs and processing steps below.
    # Output: no explicit value; normal completion returns None.
    # Processing: select branches using the stated conditions.
    def do_GET(self):
        # Run this branch when self.path equals the text '/'.
        if self.path == "/":
            # Call self._send with the supplied arguments.
            self._send(
                # Supply 200 to the enclosing expression.
                200, "text/html; charset=utf-8",
                # Supply the result of HTML.encode(the text 'utf-8') to self._send.
                HTML.encode("utf-8"),
            )
        # Run this branch when self.path equals the text '/api/latest'.
        elif self.path == "/api/latest":
            # Enter LOCK and run the enclosed operations within that context.
            with LOCK:
                # Set payload to the result of copy.deepcopy(LATEST at 'payload').
                payload = copy.deepcopy(LATEST["payload"])
            # Call self._json with the supplied arguments.
            self._json(200, payload or {})
        # Run this alternative branch when the preceding branch does not apply.
        else:
            # Call self._json with the supplied arguments.
            self._json(404, {"error": "not found"})

    # Do POST using the inputs and processing steps below.
    # Output: no explicit value; normal completion returns None.
    # Processing: select branches using the stated conditions, then handle the specified errors.
    def do_POST(self):
        # Run this branch when self.path differs from the text '/simulation/update'.
        if self.path != "/simulation/update":
            # Call self._json with the supplied arguments.
            self._json(404, {"error": "not found"})
            # Return no value to the caller.
            return
        # Attempt the enclosed operations and route matching exceptions to the handlers below.
        try:
            # Set length to an integer built from 'Content-Length' from self.headers; use the text '0' if absent.
            length = int(self.headers.get("Content-Length", "0"))
            # Set payload to the decoded data produced by json.loads from the result of self.rfile.read(length).
            payload = json.loads(self.rfile.read(length))
            # Enter LOCK and run the enclosed operations within that context.
            with LOCK:
                # Set LATEST['payload'] to the result of copy.deepcopy(payload).
                LATEST["payload"] = copy.deepcopy(payload)
            # Call self._json with the supplied arguments.
            self._json(202, {"accepted": True})
        # Handle (ValueError, json.JSONDecodeError) using the recovery steps below.
        except (ValueError, json.JSONDecodeError):
            # Call self._json with the supplied arguments.
            self._json(400, {"error": "invalid JSON"})

    # Json using the inputs and processing steps below.
    # Input status: the supplied status.
    # Input value: the supplied value.
    # Output: no explicit value; normal completion returns None.
    def _json(self, status, value):
        # Call self._send with the supplied arguments.
        self._send(status, "application/json", json.dumps(value).encode())

    # Send using the inputs and processing steps below.
    # Input status: the supplied status.
    # Input content_type: the supplied content type.
    # Input body: the supplied body.
    # Output: no explicit value; normal completion returns None.
    def _send(self, status, content_type, body):
        # Call self.send_response with the supplied arguments.
        self.send_response(status)
        # Call self.send_header with the supplied arguments.
        self.send_header("Content-Type", content_type)
        # Call self.send_header with the supplied arguments.
        self.send_header("Content-Length", str(len(body)))
        # Call self.send_header with the supplied arguments.
        self.send_header("Cache-Control", "no-store")
        # Call self.end_headers with the supplied arguments.
        self.end_headers()
        # Call self.wfile.write with the supplied arguments.
        self.wfile.write(body)

    # Log message using the inputs and processing steps below.
    # Input _format: the supplied format.
    # Input _args: the supplied args.
    # Output: no explicit value; normal completion returns None.
    def log_message(self, _format, *_args):
        # Return no value to the caller.
        return


# Main using the inputs and processing steps below.
# Output: no explicit value; normal completion returns None.
# Processing: handle the specified errors.
def main():
    # Set server to the result of ThreadingHTTPServer(a tuple containing the text 'localhost', 8000, Handler).
    server = ThreadingHTTPServer(("localhost", 8000), Handler)
    # Display the text 'Dashboard: http://localhost:8000'.
    print("Dashboard: http://localhost:8000")
    # Attempt the enclosed operations and route matching exceptions to the handlers below.
    try:
        # Call server.serve_forever with the supplied arguments.
        server.serve_forever()
    # Handle KeyboardInterrupt using the recovery steps below.
    except KeyboardInterrupt:
        # Keep this block syntactically valid without performing an operation.
        pass
    # Run these cleanup steps whether the preceding operations succeed or raise an exception.
    finally:
        # Call server.server_close with the supplied arguments.
        server.server_close()


# Run this branch when __name__ equals the text '__main__'.
if __name__ == "__main__":
    # Call main with the supplied arguments.
    main()
