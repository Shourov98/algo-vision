import Link from "next/link";

const links = [
  ["Algorithms", "/algorithms"],
  ["Data Structures", "/data-structures"],
  ["Interview Prep", "/problems"],
] as const;

export function Header() {
  return <header className="border-b border-border bg-surface"><nav aria-label="Primary" className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6"><Link className="font-semibold text-accent-strong focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-focus-ring" href="/">AlgoVision</Link><div className="flex items-center gap-1" aria-label="Main navigation">{links.map(([label, href]) => <Link className="rounded-md px-3 py-2 text-sm text-text-muted hover:bg-surface-hover hover:text-foreground focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus-ring" href={href} key={href}>{label}</Link>)}<Link className="rounded-md bg-accent px-3 py-2 text-sm font-medium text-background focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus-ring" href="/dashboard">Dashboard</Link></div></nav></header>;
}
