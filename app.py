# app.py
import pathlib
import sys
import traceback
import webview  

from backend import Backend


def main():
    base_dir = pathlib.Path(__file__).parent.resolve()
    index_path = base_dir / "index.html"

    api = Backend()

    window = webview.create_window(
        title="Examination AI",
        url=index_path.as_uri(),
        js_api=api,
        width=1000,
        height=800,
    )

    backends_to_try = ["edgechromium", "qt", None]
    last_exc = None

    for gui in backends_to_try:
        try:
            if gui:
                print(f"Starting pywebview with gui={gui}...", flush=True)
                webview.start(gui=gui, debug=True)
            else:
                print("Starting pywebview with default gui...", flush=True)
                webview.start(debug=True)

            print("pywebview exited.", flush=True)
            return
        except Exception as exc:
            last_exc = exc
            print(f"Failed to start pywebview with gui={gui}: {exc}", file=sys.stderr, flush=True)
            traceback.print_exc()

    raise last_exc


if __name__ == "__main__":
    main()
