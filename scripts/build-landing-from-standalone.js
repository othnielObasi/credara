const fs = require('fs');

const html = fs.readFileSync('c:/othnielObasi/credara/scripts/_inner.html', 'utf8');
const start = html.indexOf('<div style="font-family:Inter,system-ui,sans-serif');
const endMarker = '© 2026 Credara';
const end = html.indexOf(endMarker);
if (start < 0 || end < 0) {
  console.error('markers missing', start, end);
  process.exit(1);
}

// include through end of footer line
let sliceEnd = html.indexOf('</footer>', end);
if (sliceEnd < 0) {
  // footer may be truncated / self-closing style
  sliceEnd = html.indexOf('\n', end + 40);
}
let fragment = html.slice(start, sliceEnd > 0 ? sliceEnd + '</footer>'.length : end + 80);

// If footer tag missing, close manually
if (!fragment.includes('</footer>')) {
  const footerStart = fragment.lastIndexOf('<footer');
  if (footerStart >= 0 && !fragment.slice(footerStart).includes('</footer>')) {
    fragment += '</footer>';
  }
}

// Close outer wrapper div if present
if (fragment.includes('<div style="font-family:Inter') && (fragment.match(/<div/g) || []).length > (fragment.match(/<\/div>/g) || []).length) {
  fragment += '</div>';
}

fragment = fragment
  .replace(
    /<a href="Credara SME Dashboard\.dc\.html"([^>]*)>Sign in<\/a>/g,
    '<button type="button" data-landing-action="signin"$1>Sign in</button>'
  )
  .replace(
    /<a href="Credara SME Dashboard\.dc\.html"([^>]*)>Sign up<\/a>/g,
    '<button type="button" data-landing-action="signup"$1>Sign up</button>'
  )
  .replace(
    /<a href="Credara SME Dashboard\.dc\.html"([^>]*)>Get started<\/a>/g,
    '<button type="button" data-landing-action="signup"$1>Get started</button>'
  )
  .replace(
    />Start enterprise demo<\/button>/g,
    ' data-landing-action="signup">Start enterprise demo</button>'
  )
  .replace(
    />Run this demo flow<\/button>/g,
    ' data-landing-action="signup">Run this demo flow</button>'
  )
  .replace(
    />See process flow<\/button>/g,
    ' data-landing-action="scroll-workflow">See process flow</button>'
  );

console.log('fragment len', fragment.length);
console.log('Get paid', fragment.includes('Get paid'));
console.log('Build on real API', fragment.includes('Build on real API'));
console.log('Four connected', fragment.includes('Four connected workspaces'));

const embed = `'use client';

import type { MouseEvent } from 'react';

type LandingPageProps = {
  onSignIn: () => void;
  onSignUp: () => void;
};

const MARKUP: string = ${JSON.stringify(fragment)};

export default function LandingPage({ onSignIn, onSignUp }: LandingPageProps) {
  const onClick = (event: MouseEvent<HTMLDivElement>) => {
    const target = event.target as HTMLElement | null;
    const actionEl = target?.closest?.('[data-landing-action]') as HTMLElement | null;
    if (!actionEl) return;
    event.preventDefault();
    const action = actionEl.getAttribute('data-landing-action');
    if (action === 'signin') onSignIn();
    if (action === 'signup') onSignUp();
    if (action === 'scroll-workflow') {
      document.getElementById('sec-workflow')?.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return <div className="landing-page" onClick={onClick} dangerouslySetInnerHTML={{ __html: MARKUP }} />;
}
`;

fs.writeFileSync('c:/othnielObasi/credara/apps/web/components/landing/landing-page.tsx', embed);
fs.writeFileSync('c:/othnielObasi/credara/docs/archive/credara-landing-standalone-correct-fragment.html', fragment);
console.log('wrote landing-page.tsx', embed.length);
