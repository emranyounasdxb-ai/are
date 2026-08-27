export async function register() {
  if (process.env.NEXT_RUNTIME === "nodejs" && process.env.NEXT_PHASE !== "phase-production-build") {
    const { validatePrivateFonts } = await import("./lib/private-fonts.mjs");
    try {
      await validatePrivateFonts();
    } catch (error) {
      // Next can retain a listener after a rejected instrumentation hook. A
      // missing mandatory asset must terminate, not leave a half-ready server.
      console.error(error instanceof Error ? error.message : "ARE_FONT_INVALID: startup validation failed");
      process.exit(1);
    }
  }
}
