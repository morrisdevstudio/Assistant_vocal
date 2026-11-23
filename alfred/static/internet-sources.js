window.renderInternetSources = function(sources = []) {
  const list = document.getElementById("internet-sources");
  if (!list) return;
  list.replaceChildren();
  for (const source of sources.slice(0, 5)) {
    try {
      const url = new URL(source.url);
      if (!["https:", "http:"].includes(url.protocol) || url.username || url.password) continue;
      const item = document.createElement("li"), link = document.createElement("a");
      link.href = url.href; link.target = "_blank"; link.rel = "noopener noreferrer";
      link.textContent = source.title || source.publisher || url.hostname;
      item.append(link);
      if (source.date) item.append(document.createTextNode(" · " + source.date));
      list.append(item);
    } catch { /* Un lien invalide n'est jamais inséré. */ }
  }
  list.hidden = !list.childElementCount;
};
