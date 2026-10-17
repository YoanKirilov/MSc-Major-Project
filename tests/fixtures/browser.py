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
        """tolerance => { const root = document.documentElement; const layout = {
            width: innerWidth, scrollWidth: root.scrollWidth,
            overflowing: [...document.querySelectorAll('body *')].flatMap(element => {
                if (!element.getClientRects().length) return [];
                const rect = element.getBoundingClientRect();
                if (rect.right <= innerWidth + tolerance && rect.left >= -tolerance) return [];
                const style = getComputedStyle(element);
                return [{tag: element.tagName, id: element.id,
                    classes: typeof element.className === 'string' ? element.className : '',
                    left: rect.left, right: rect.right, width: rect.width,
                    minWidth: style.minWidth, grid: style.gridTemplateColumns}];
            }).slice(0, 20)};
            if (layout.scrollWidth <= innerWidth + tolerance) return layout;
            layout.scrolling = [...document.querySelectorAll('body *')].flatMap(element => {
                if (element.scrollWidth <= element.clientWidth + tolerance) return [];
                const style = getComputedStyle(element);
                return [{tag: element.tagName, id: element.id, classes: element.className,
                    scroll: element.scrollWidth, client: element.clientWidth,
                    overflow: style.overflowX, display: style.display}];
            }).slice(0, 24);
            layout.textOverflow = [];
            const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
            for (let node; (node = walker.nextNode()) && layout.textOverflow.length < 12;) {
                if (!node.parentElement.getClientRects().length) continue;
                const range = document.createRange(); range.selectNodeContents(node);
                for (const rect of range.getClientRects()) {
                    if (rect.right <= innerWidth + tolerance) continue;
                    layout.textOverflow.push({tag: node.parentElement.tagName,
                        id: node.parentElement.id, left: rect.left, right: rect.right});
                }
            }
            // Probe only the already-failed synthetic page, restore every style,
            // then still fail against the original measurements. Never a repair.
            if (document.getElementById('settings-form')) {
                layout.hiddenSubtreeWidths = {};
                for (const selector of ['.topbar', '#display-preferences', '#settings-form',
                    '#scope-mode', '.settings-advanced', '#check-ai', '.site-footer']) {
                    const node = document.querySelector(selector);
                    if (!node) continue;
                    const hadStyle = node.hasAttribute('style');
                    const saved = node.style.cssText;
                    try { node.style.display = 'none';
                        layout.hiddenSubtreeWidths[selector] = root.scrollWidth;
                    } finally { node.style.cssText = saved;
                        if (!hadStyle) node.removeAttribute('style'); }
                }
                const select = document.getElementById('scope-mode');
                if (select) {
                    layout.nativeSelectProbes = {};
                    const parent = select.parentElement;
                    const selectCss = select.style.cssText, parentCss = parent.style.cssText;
                    const variants = {
                        menuButton: {appearance: 'menulist-button', overflow: 'hidden'},
                        noAppearance: {appearance: 'none', overflow: 'hidden'},
                        zeroIntrinsic: {width: '0px', minWidth: '100%'},
                        sizeContainment: {contain: 'inline-size'},
                        paintContainment: {contain: 'paint'},
                        blockParent: {}, columnFlexParent: {}
                    };
                    try {
                        for (const [name, properties] of Object.entries(variants)) {
                            select.style.cssText = selectCss; parent.style.cssText = parentCss;
                            Object.assign(select.style, properties);
                            if (name === 'blockParent') parent.style.display = 'block';
                            if (name === 'columnFlexParent') {
                                parent.style.display = 'flex';
                                parent.style.flexDirection = 'column';
                            }
                            const style = getComputedStyle(select);
                            layout.nativeSelectProbes[name] = {page: root.scrollWidth,
                                appearance: style.appearance, overflow: style.overflowX,
                                width: select.getBoundingClientRect().width};
                        }
                    } finally {
                        select.style.cssText = selectCss; parent.style.cssText = parentCss;
                    }
                }
            }
            return layout;
        }""",
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
