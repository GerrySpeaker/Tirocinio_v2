export class Router {
  constructor(contentSelector) {
    this.contentEl = document.querySelector(contentSelector);
    this.attachLinkHandlers();
    this.attachPopStateHandler();
    this.updateActiveLink(location.pathname);
  }

  attachLinkHandlers() {
    document.addEventListener("click", (e) => {
      const link = e.target.closest("a[data-link]");
      if (!link) return;

      const url = link.getAttribute("href");
      if (url.startsWith("http")) return; // ignora link esterni

      e.preventDefault();
      this.navigate(url);
    });
  }

  attachPopStateHandler() {
    window.addEventListener("popstate", () => {
      this.load(location.pathname, false);
    });
  }

  async navigate(url) {
    await this.load(url, true);
  }

  async load(url, push = true) {
    try {
      const response = await fetch(url);
      if (!response.ok) throw new Error(`Errore nel caricamento: ${url}`);

      const html = await response.text();
      const parser = new DOMParser();
      const doc = parser.parseFromString(html, "text/html");
      const newMain = doc.querySelector("main");
      if (!newMain) throw new Error(`Nessun <main> trovato in ${url}`);

      this.contentEl.innerHTML = newMain.innerHTML;
      if (push) history.pushState({}, "", url);

      document.title = doc.title || "Il Mio Sito";
      window.scrollTo({ top: 0 });

      this.updateActiveLink(url);
    } catch (err) {
      console.error(err);
      this.contentEl.innerHTML = `<p>Errore nel caricamento della pagina.</p>`;
    }
  }

  updateActiveLink(url) {
    const links = document.querySelectorAll(".sidebar-nav .nav-link");
    links.forEach((link) => {
      link.classList.remove("active");
      const href = link.getAttribute("href");
      if (
        href === url ||
        (href === "index.html" && (url === "/" || url.endsWith("index.html")))
      ) {
        link.classList.add("active");
      }
    });
  }
}
