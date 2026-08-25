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

function sectionFromPath(path: string) {
  const pathname = path.split(/[?#]/, 1)[0];
  const segments = pathname.split("/").filter(Boolean);

  if (segments[0] !== "en" && segments[0] !== "ar") return null;
  if (segments.length === 1) return "home";
  return navigationSections.has(segments[1]) ? segments[1] : null;
}

export function isNavigationHrefActive(pathname: string, href: string) {
  const targetSection = sectionFromPath(href);
  return targetSection !== null && sectionFromPath(pathname) === targetSection;
}
