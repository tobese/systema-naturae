import { useEffect, useState } from "react";

interface Props {
  src?: string | null;
  alt: string;
  loading?: boolean;
  width?: string | number;
  height?: string | number;
  aspectRatio?: string;
  borderRadius?: number;
  background?: string;
  objectFit?: "cover" | "contain";
  marginTop?: number;
  marginBottom?: number;
}

export default function FadingImage({
  src,
  alt,
  loading = false,
  width = "100%",
  height,
  aspectRatio = "4 / 3",
  borderRadius = 6,
  background = "#1a1a2a",
  objectFit = "cover",
  marginTop,
  marginBottom,
}: Props) {
  const [ready, setReady] = useState(false);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    setReady(false);
    setFailed(false);
  }, [src]);

  if (loading) {
    return (
      <div
        style={{
          width,
          height: height ?? undefined,
          aspectRatio: height ? undefined : aspectRatio,
          marginTop,
          marginBottom,
          background,
          borderRadius,
        }}
      />
    );
  }

  if (!src || failed) {
    return (
      <div
        style={{
          width,
          height: height ?? undefined,
          aspectRatio: height ? undefined : aspectRatio,
          marginTop,
          marginBottom,
          background,
          borderRadius,
        }}
      />
    );
  }

  return (
    <div
      style={{
        width,
        height: height ?? undefined,
        aspectRatio: height ? undefined : aspectRatio,
        marginTop,
        marginBottom,
        overflow: "hidden",
        borderRadius,
        background,
      }}
    >
      <img
        src={src}
        alt={alt}
        onLoad={() => setReady(true)}
        onError={() => setFailed(true)}
        style={{
          display: "block",
          width: "100%",
          height: "100%",
          objectFit,
          opacity: ready ? 1 : 0,
          transition: "opacity 220ms ease-in",
        }}
      />
    </div>
  );
}
