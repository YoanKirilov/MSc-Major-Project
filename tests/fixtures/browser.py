"""Reserve loopback listeners without browser-blocked low port assignments."""

import errno
import secrets
import socket

MIN_BROWSER_PORT = 49152
MAX_BROWSER_PORT = 65535
PORT_ATTEMPTS = 64


def assert_page_reflows(page, context="", *, tolerance=1):
    """Keep overflow checks strict and identify the actual oversized elements."""
    layout = page.evaluate(
        """tolerance => ({width: innerWidth, scrollWidth: document.documentElement.scrollWidth,
            overflowing: [...document.querySelectorAll('body *')].flatMap(element => {
                if (!element.getClientRects().length) return [];
                const rect = element.getBoundingClientRect();
                if (rect.right <= innerWidth + tolerance && rect.left >= -tolerance) return [];
                const style = getComputedStyle(element);
                return [{tag: element.tagName, id: element.id,
                    classes: typeof element.className === 'string' ? element.className : '',
                    left: rect.left, right: rect.right, width: rect.width,
                    minWidth: style.minWidth, grid: style.gridTemplateColumns}];
            }).slice(0, 20)})""",
        tolerance,
    )
    assert layout["scrollWidth"] <= layout["width"] + tolerance, f"{context}: {layout}"


def component_boxes(component, *selectors):
    """Sample a component and its children together, before async scrolling moves it."""
    return component.evaluate(
        """(element, selectors) => [element, ...selectors.map(selector => {
            const child = element.querySelector(selector);
            if (!child) throw new Error('Missing component child: ' + selector);
            return child;
        })].map(node => {
            const rect = node.getBoundingClientRect();
            return {x:rect.x, y:rect.y, width:rect.width, height:rect.height};
        })""",
        list(selectors),
    )


def scroll_history_with_keyboard(page):
    """Let the first frame paint, then use native scrolling, not a loading hook."""
    page.locator("#history-status").focus()
    page.evaluate(
        "() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))"
    )
    page.keyboard.press("End")


def browser_listener():
    """Keep the socket reserved through Uvicorn startup; never probe then close.

    The default browser restricted-port lists are below this high ephemeral range.
    Custom enterprise policies are not overridden. Retry address collisions and
    OS-reserved ports only, with a bounded failure if none can be allocated.
    """
    for _ in range(PORT_ATTEMPTS):
        port = MIN_BROWSER_PORT + secrets.randbelow(MAX_BROWSER_PORT - MIN_BROWSER_PORT + 1)
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            listener.bind(("127.0.0.1", port))
        except OSError as exc:
            listener.close()
            if exc.errno not in {errno.EADDRINUSE, errno.EACCES}:
                raise
        else:
            return listener
    raise RuntimeError("No browser-safe loopback test port could be reserved")
