import { Reveal } from "../components/motion/reveal";

export default function PublicFoundationPage() {
  return (
    <main className="grid min-h-dvh place-items-center p-6">
      <Reveal className="w-full max-w-xl">
        <section aria-labelledby="public-foundation-title" className="space-y-4">
          <h1 id="public-foundation-title" className="text-2xl font-semibold">
            ALIYAS Real Estate
          </h1>
          <p className="text-lg">Public website foundation</p>
          <p className="border-s-4 ps-4">
            Development-only placeholder. Approved content and final design are not implemented.
          </p>
        </section>
      </Reveal>
    </main>
  );
}
