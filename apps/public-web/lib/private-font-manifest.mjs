// Public runtime contract only: no binaries, purchase records or private locations.
export const fontVersion = 'v1';
export const latinGlyphs = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 .,!?-';
export const arabicGlyphs = 'ابتثجحخدذرزسشصضطظعغفقكلمنهويءآأإؤئىة٠١٢٣٤٥٦٧٨٩،؟';
export const privateFonts = [
  { id: 'h1-regular.woff2', family: 'Hennigar', weight: 400, italic: false, glyphs: latinGlyphs, sha256: 'c65aa0f0d2538d0922fa25a12e2d01873e0d4cc3206f017ecb076d0b3f8f7236' },
  { id: 'h1-italic.woff2', family: 'Hennigar', legacyFullName: 'Hennigar Italic Webfont', weight: 400, italic: true, glyphs: latinGlyphs, sha256: '21a50170a9afb5ffc148544c8ba404dc964182f1f280e486df25fb8f08102b30' },
  { id: 'headings.ttf', family: 'Aeternus Nano Thin', range: [100, 856], glyphs: latinGlyphs, sha256: '64766cf89ac85830461b07b806f5e5d7b37a7d3d00ef968f534aeba96c60caaf' },
  { id: 'body.woff2', family: 'Auren', range: [100, 800], glyphs: latinGlyphs, sha256: '44e28750eec225dae69e0877971a158b5f588680479769d2dc061055edb3e603' },
  { id: 'decorative.ttf', family: 'Aeternus Tall Thin', range: [100, 856], glyphs: latinGlyphs, sha256: '4b03b94e5edb184b5ca4314dda21d06be59cc5501316eb0691cf079e4f03b1ca' },
  { id: 'signature.woff2', family: 'Hoftman', weight: 400, italic: false, glyphs: latinGlyphs, sha256: 'c5bb0980d81e6827c3f21652546f55e45b3aeaa443119496366dc40904caca53' },
  { id: 'arabic-h1.woff2', family: 'True Arabic', weight: 700, italic: false, glyphs: arabicGlyphs, sha256: '7b2e686724e358198656ee310b39c01b85a7d74d5bc382863e74acb69b8b24a7' },
];
