const latinPattern = /[A-Za-z]/;

const intentionalLatinTokens = new Set([
  "DOCX",
  "DOC",
  "EN",
  "LinkedIn",
  "PDF",
  "WhatsApp",
]);

const protectedBrandPattern = /\b(?:ARE|ALIYAS(?: Real Estate)?)\b/;
const urlPattern = /https?:\/\/\S+|www\.\S+/gi;
const emailPattern = /\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b/gi;
const phonePattern = /\+?[0-9][0-9\s()-]{6,}[0-9]/g;
const technicalIdentifierPattern = /\b[a-f0-9]{8}-[a-f0-9-]{27,}\b|\b[a-z0-9]+(?:[_-][a-z0-9]+){2,}\b/gi;

export function unexpectedArabicRouteLatin(value) {
  if (!value || protectedBrandPattern.test(value)) return protectedBrandPattern.test(value) ? value.trim() : null;
  let remainder = value
    .replace(urlPattern, " ")
    .replace(emailPattern, " ")
    .replace(phonePattern, " ")
    .replace(technicalIdentifierPattern, " ");
  for (const token of [...intentionalLatinTokens].sort((a, b) => b.length - a.length)) {
    remainder = remainder.replaceAll(token, " ");
  }
  return latinPattern.test(remainder) ? value.trim() : null;
}

export function unexpectedArabicRouteWesternDigit(value) {
  if (!value) return null;
  const remainder = value
    .replace(urlPattern, " ")
    .replace(emailPattern, " ")
    .replace(phonePattern, " ")
    .replace(technicalIdentifierPattern, " ");
  return /[0-9]/.test(remainder) ? value.trim() : null;
}

export const intentionalArabicRouteLatinExceptions = Object.freeze([...intentionalLatinTokens]);
