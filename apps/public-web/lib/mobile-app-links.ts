export type MobileStoreTarget = Readonly<{
  platform: "ios" | "android";
  storeLabel: string;
  url: string | null;
}>;

export const mobileStoreTargets: ReadonlyArray<MobileStoreTarget> = [
  { platform: "ios", storeLabel: "App Store", url: null },
  { platform: "android", storeLabel: "Google Play", url: null },
];
