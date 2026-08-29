export const arabicBrandName = "علياس العقارية";

const westernDigits = /[0-9]/g;
const latinLetters = /[A-Za-z]/;
const arabicLetters = /[\u0600-\u06ff]/;
const approvedArabicTerms: ReadonlyArray<readonly [string, string]> = [
  ["Sharjah Waterfront City", "مدينة الشارقة للواجهات المائية"],
  ["Al Mamsha Raseel", "الممشى رسيل"],
  ["Al Hamra Village", "قرية الحمراء"],
  ["Al Marjan Island", "جزيرة المرجان"],
  ["Maryam Island", "جزيرة مريم"],
  ["Tilal Properties", "تلال العقارية"],
  ["Sharjah Holding", "الشارقة القابضة"],
  ["Shoumous Properties", "شموس العقارية"],
  ["IFA Hotel & Resorts", "إيفا للفنادق والمنتجعات"],
  ["Diamond Developer", "دايموند للتطوير"],
  ["Mada'in Properties", "مدائن العقارية"],
  ["Mada’in Properties", "مدائن العقارية"],
  ["Arada Developer", "شركة أرادا"],
  ["Eagle Hills", "إيجل هيلز"],
  ["Alef Group", "مجموعة ألف"],
  ["Tiger Group", "مجموعة تايغر"],
  ["Ajmal Makan", "أجمل مكان"],
  ["Naseej District", "حي نسيج"],
  ["residential-plot", "أرض سكنية"],
  ["Tilal City", "مدينة تلال"],
  ["Mina Al Arab", "ميناء العرب"],
  ["Al Zahia", "الزاهية"],
  ["Al Mamzar", "الممزر"],
  ["Aljada", "الجادة"],
  ["Masaar", "مسار"],
  ["Sharjah", "الشارقة"],
  ["Ras Al Khaimah", "رأس الخيمة"],
  ["Shurooq", "شروق"],
  ["Mada", "مدى"],
  ["Q1", "الربع الأول"],
  ["Q2", "الربع الثاني"],
  ["Q3", "الربع الثالث"],
  ["Q4", "الربع الرابع"],
];

export function toArabicIndicDigits(value: string | number): string {
  return String(value).replace(westernDigits, (digit) => "٠١٢٣٤٥٦٧٨٩"[Number(digit)]);
}

export function localizedDisplayText(value: string, locale: "en" | "ar"): string {
  return locale === "ar" ? toArabicIndicDigits(value) : value;
}

export function isArabicUserFacingText(value: string | null | undefined): value is string {
  return Boolean(value?.trim()) && !latinLetters.test(value ?? "");
}

export function localizedArabicList(values: readonly string[] | null | undefined): string[] {
  return (values ?? [])
    .map((value) => value.trim())
    .filter(isArabicUserFacingText)
    .map(toArabicIndicDigits);
}

export function localizedBrand(locale: "en" | "ar"): string {
  return locale === "ar" ? arabicBrandName : "ALIYAS Real Estate";
}

export function normalizeArabicUserFacingText(value: string): string {
  let normalized = value
    .replaceAll("ALIYAS Real Estate", arabicBrandName)
    .replaceAll("ALIYAS", "علياس")
    .replace(/\bARE\b/g, arabicBrandName);
  if (!arabicLetters.test(normalized)) return normalized;
  for (const [english, arabic] of approvedArabicTerms) {
    normalized = normalized.replace(new RegExp(escapeRegExp(english), "gi"), arabic);
  }
  return toArabicIndicDigits(normalized);
}

export function normalizeArabicContent<T>(value: T): T {
  if (typeof value === "string") return normalizeArabicUserFacingText(value) as T;
  if (Array.isArray(value)) return value.map(normalizeArabicContent) as T;
  if (value && typeof value === "object") {
    return Object.fromEntries(
      Object.entries(value).map(([key, item]) => [key, normalizeArabicContent(item)]),
    ) as T;
  }
  return value;
}

function escapeRegExp(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}
