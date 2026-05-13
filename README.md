# So What — Book Landing Page

Landing page for Dr. Meghna Dassani's upcoming book
**_So What: How to Stop Overthinking Your Wins & Losses and Build Unstoppable Momentum_**.

## Stack
Static HTML + Tailwind (CDN) + AOS scroll animations. No build step.

Open `index.html` directly, or deploy the folder as-is to Vercel / Netlify / Cloudflare Pages / GitHub Pages.

## Structure
```
.
├── index.html              # the landing page
├── images/                 # book cover, author photos, logo
└── elements/               # 10 hand-drawn brand graphics (PNG, transparent)
```

## Two conversion paths
1. **Waitlist (free)** — captures email, delivers Chapter 1.
2. **Pre-order (paid)** — Chapter 1 + signed first-print copy + invitation-only launch webinar.

Both forms currently post to FormSubmit.co (`meghna@meghnadassani.com`).

## Before going live
1. **Wire up checkout** — In `index.html`, find the `// TODO: replace this URL with your live checkout` line and swap the fallback `mailto:` redirect for the real Stripe / Shopify / Bookfunnel link.
2. **Pricing** — Add the pre-sale price near the "Reserve My Copy" button in the pre-order card if you want it visible.
3. **Launch date** — Update the FAQ entry that currently says "October" once the date is locked.
4. **Webinar date** — Add the live event date to the webinar bonus section once scheduled.
