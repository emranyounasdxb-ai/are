const navigationSections = new Set([
  "about",
  "properties",
  "off-plan",
  "communities",
  "developers",
  "insights",
  "careers",
  "contact",
]);

function navigationTarget(path: string) {
  const [pathname, query = ""] = path.split("?", 2);
  const segments = pathname.split("/").filter(Boolean);

  if (segments[0] !== "en" && segments[0] !== "ar") return null;
  if (segments.length === 1) return { purpose: null, section: "home" };
  if (!navigationSections.has(segments[1])) return null;

  const purpose = segments[1] === "properties"
    ? new URLSearchParams(query).get("purpose") ?? "buy"
    : null;

  return { purpose, section: segments[1] };
}

export function isNavigationHrefActive(pathname: string, href: string) {
  const current = navigationTarget(pathname);
  const target = navigationTarget(href);

  return current !== null
    && target !== null
    && current.section === target.section
    && current.purpose === target.purpose;
}
