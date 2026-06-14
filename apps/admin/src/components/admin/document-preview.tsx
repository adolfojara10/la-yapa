export function DocumentPreview({ url }: { url: string }) {
  if (!url) {
    return <p className="text-small text-muted">No subido.</p>;
  }

  const lower = url.toLowerCase();
  if (lower.endsWith('.pdf')) {
    return (
      <iframe
        src={url}
        title="Documento"
        className="h-72 w-full rounded-md border border-border bg-background"
      />
    );
  }

  return (
    // eslint-disable-next-line @next/next/no-img-element
    <img
      src={url}
      alt="Documento"
      className="h-72 w-full rounded-md border border-border object-cover"
    />
  );
}
