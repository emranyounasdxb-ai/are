import Image from "next/image";

export function AdminBrandLogo({ className }: Readonly<{ className: string }>) {
  return (
    <span className={className}>
      <Image
        alt="ALIYAS Real Estate"
        height={2885}
        preload
        sizes="(max-width: 800px) 44px, 48px"
        src="/brand/aliyas-real-estate-logo.png"
        width={2885}
      />
    </span>
  );
}
