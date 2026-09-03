# Cabinet Layer A (normal-user UI) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the 1.67 cabinet on `https://panel.rookari.com` feel like production for a normal customer: Persian first paint, Jalali dates, user wording, RTL-safe amounts/URLs, and subscription first-connect UX — without rewriting upstream pages or building the partner sales desk.

**Architecture:** Overlay on `/opt/cabinet` `prod-cutover` (1.67.0 + M5/M6-T5). New small helpers (`formatDate.ts`, `LtrIsolate`, `TrafficUsageText`, `ConfigDeliverySheet`). Surgical patches to `i18n.ts`, `index.html`, `uiLocale.ts`, `fa.json` (merge keys, never replace file), `Subscription.tsx`, and `SubscriptionListCard.tsx`. Donor behavior is `/opt/remnabot/cabinet` (READ-ONLY). Layer B (bot `PricingEngine`) is untouched. Layer C (`/sales`) is out of this plan.

**Tech Stack:** Vite + React + TypeScript, i18next, vitest, Biome. Work tree: `/opt/cabinet`. Branch: `prod-cutover`.

## Global Constraints

- Spec: `docs/superpowers/specs/2026-09-03-cabinet-b2-overlay-design.md` (operator تایید 2026-09-03).
- Tree: `/opt/cabinet` only. Do not edit `/opt/remnabot1` app code. Do not edit `/opt/remnabot`.
- Do **not** start M7-T1, touch DNS, production token, or remnabot1 ORM/API.
- Do **not** replace `Referral.tsx`, `TariffPurchaseForm.tsx`, or whole `fa.json`.
- Do **not** add `/sales`, Earn tabs, wholesale admin, or `PartnerCheckoutFields`.
- Do **not** copy `DisableSubscriptionSheet` — 1.67 `Subscription` type has no `user_disabled`; that needs Layer C / bot later.
- Toman skipFx already on 1.67 (`c5b1ca9a`). Do not change `useCurrency.ts` / `format.ts` FX in this plan.
- English digits in new fa strings (0-9, not ۰-۹).
- After each commit: `cd /opt/cabinet && npm test` and `npx biome check` on touched files. `npm run type-check` at the end of the last code task.
- One concern per commit. Commit on `prod-cutover`. Do not force-push.
- Do not rebuild `remnawave_bot`. Cabinet-only image/recreate is allowed after the user-smoke task, not mid-plan unless needed to verify.

## File map

| File | Responsibility |
|---|---|
| `/opt/cabinet/src/i18n.ts` | Default `fa`, localStorage-only detect, no Telegram auto-lang |
| `/opt/cabinet/index.html` | First paint `lang="fa" dir="rtl"` |
| `/opt/cabinet/src/utils/uiLocale.ts` | fa → `fa-IR-u-ca-persian-nu-latn` |
| `/opt/cabinet/src/utils/formatDate.ts` | Explicit Jalali/Gregorian helper |
| `/opt/cabinet/src/utils/ltrIsolate.tsx` | `dir="ltr"` + `unicode-bidi: isolate` wrapper |
| `/opt/cabinet/src/styles/globals.css` | `.url-ltr` class |
| `/opt/cabinet/src/components/subscription/TrafficUsageText.tsx` | LTR traffic amounts |
| `/opt/cabinet/src/components/subscription/ConfigDeliverySheet.tsx` | QR/copy sheet (new) |
| `/opt/cabinet/src/utils/subscriptionDisplayLabel.ts` | Hide `user_unknown_*` if field present later |
| `/opt/cabinet/src/locales/fa.json` | User-path terminology + onboarding keys |
| `/opt/cabinet/src/pages/Subscription.tsx` | Wire traffic isolate, URL class, checklist, delivery sheet |
| `/opt/cabinet/src/components/subscription/SubscriptionListCard.tsx` | `formatUserDate` for end date |

---

### Task 1: Default Persian + first-paint RTL

**Files:**
- Modify: `/opt/cabinet/src/i18n.ts`
- Modify: `/opt/cabinet/index.html` (html tag only)
- Test: `/opt/cabinet/src/i18n.defaults.test.ts`

**Interfaces:**
- Consumes: existing i18next init in `i18n.ts`
- Produces: `DEFAULT_LNG = 'fa'`; `applyTelegramLanguage()` must not switch language when `cabinet_language` is unset (stay on `fa`)

- [ ] **Step 1: Write the failing test**

Create `/opt/cabinet/src/i18n.defaults.test.ts`:

```ts
import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';

describe('cabinet default language (Layer A)', () => {
  it('index.html first-paints fa rtl', () => {
    const html = readFileSync(new URL('../index.html', import.meta.url), 'utf8');
    expect(html).toMatch(/<html[^>]*lang="fa"/);
    expect(html).toMatch(/dir="rtl"/);
  });

  it('i18n.ts pins DEFAULT_LNG fa and localStorage-only detection', () => {
    const src = readFileSync(new URL('./i18n.ts', import.meta.url), 'utf8');
    expect(src).toMatch(/const DEFAULT_LNG = 'fa'/);
    expect(src).toMatch(/fallbackLng:\s*\[DEFAULT_LNG,\s*FALLBACK_LNG,\s*'en'\]/);
    expect(src).toMatch(/order:\s*\['localStorage'\]/);
    expect(src).not.toMatch(/order:\s*\['localStorage',\s*'navigator'\]/);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /opt/cabinet && npx vitest run src/i18n.defaults.test.ts
```

Expected: FAIL (`lang="ru"` / no `DEFAULT_LNG`).

- [ ] **Step 3: Minimal implementation**

In `/opt/cabinet/index.html` change the opening html tag from `lang="ru"` to:

```html
<html lang="fa" dir="rtl" class="dark">
```

In `/opt/cabinet/src/i18n.ts`:

1. After `SUPPORTED_LANGS`, add:

```ts
/** Deployment default — matches bot DEFAULT_LANGUAGE (fa). */
const DEFAULT_LNG = 'fa';
```

2. Change `i18n.init` to:

```ts
  .init({
    lng: DEFAULT_LNG,
    fallbackLng: [DEFAULT_LNG, FALLBACK_LNG, 'en'],
    supportedLngs: SUPPORTED_LANGS,
    partialBundledLanguages: true,

    detection: {
      order: ['localStorage'],
      caches: ['localStorage'],
      lookupLocalStorage: 'cabinet_language',
    },
```

3. Change startup load to always load fa + ru:

```ts
const detectedLng = i18n.language?.split('-')[0] || DEFAULT_LNG;
const langsToLoad = [
  DEFAULT_LNG,
  FALLBACK_LNG,
  ...(detectedLng !== DEFAULT_LNG && detectedLng !== FALLBACK_LNG ? [detectedLng] : []),
];
Promise.all(langsToLoad.map(loadLanguage));
```

4. Update the comment that says `index.html ships with lang="ru"` to `lang="fa"`.

5. Replace `applyTelegramLanguage` so Telegram client language is **not** auto-applied (donor pattern). Keep the export so `main.tsx` still compiles:

```ts
/**
 * Explicit LanguageSwitcher choice wins. Otherwise stay on DEFAULT_LNG (fa).
 * Telegram client language is not auto-applied (Layer A).
 */
export function applyCabinetLanguagePreference(preferred?: string | null): void {
  try {
    if (localStorage.getItem(LANGUAGE_STORAGE_KEY)) return;
  } catch {
    return;
  }
  const raw = preferred?.split('-')[0]?.toLowerCase();
  const code = raw && SUPPORTED_LANGS.includes(raw) ? raw : DEFAULT_LNG;
  if (i18n.language?.split('-')[0] !== code) {
    i18n.changeLanguage(code);
  }
}

/** @deprecated Use applyCabinetLanguagePreference — Telegram client lang is not auto-applied. */
export function applyTelegramLanguage(): void {
  applyCabinetLanguagePreference();
}
```

Do not remove the `getTelegramLanguageCode` import if still unused — if unused after this change, remove the import (Biome unused import).

- [ ] **Step 4: Run tests**

```bash
cd /opt/cabinet && npx vitest run src/i18n.defaults.test.ts
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
cd /opt/cabinet
git add src/i18n.ts index.html src/i18n.defaults.test.ts
git commit -m "$(cat <<'EOF'
fix(i18n): default fa and rtl first paint (Layer A)

EOF
)"
```

---

### Task 2: Jalali dates (uiLocale + formatDate)

**Files:**
- Create: `/opt/cabinet/src/utils/formatDate.ts`
- Modify: `/opt/cabinet/src/utils/uiLocale.ts`
- Modify: `/opt/cabinet/src/utils/uiLocale.test.ts`
- Test: `/opt/cabinet/src/utils/formatDate.test.ts`
- Modify: `/opt/cabinet/src/components/subscription/SubscriptionListCard.tsx` (local `formatDate` that uses `i18n.language` without calendar)

**Interfaces:**
- Consumes: i18next language
- Produces: `uiLocale()` for `fa` returns `fa-IR-u-ca-persian-nu-latn`; `formatUserDate(iso, lang)` / `formatUserDateTime(iso, lang)` as in donor

Pages that already call `toLocaleDateString(uiLocale())` (Profile, Balance, Gift, Support, Wheel, Merge, Subscription) pick up Jalali **without** a bulk rewrite once `uiLocale` changes.

- [ ] **Step 1: Write the failing tests**

Create `/opt/cabinet/src/utils/formatDate.test.ts`:

```ts
import { describe, expect, it } from 'vitest';
import { formatUserDate, formatUserDateTime } from './formatDate';

const ANCHOR = '2026-07-09T12:00:00Z';

describe('formatUserDate', () => {
  it('returns em dash for null', () => {
    expect(formatUserDate(null)).toBe('—');
  });

  it('uses Persian calendar and Latin digits for fa', () => {
    const rendered = formatUserDate(ANCHOR, 'fa');
    expect(rendered).toMatch(/1405/);
    expect(rendered).toMatch(/04/);
    expect(rendered).toMatch(/18/);
    expect(rendered).not.toMatch(/[۰-۹]/);
  });

  it('stays Gregorian for en', () => {
    const rendered = formatUserDate(ANCHOR, 'en');
    expect(rendered).toMatch(/2026/);
  });
});

describe('formatUserDateTime', () => {
  it('includes a time part for fa', () => {
    const rendered = formatUserDateTime(ANCHOR, 'fa');
    expect(rendered.length).toBeGreaterThan(formatUserDate(ANCHOR, 'fa').length);
  });
});
```

In `/opt/cabinet/src/utils/uiLocale.test.ts`, change the fa expectation:

```ts
    await i18next.changeLanguage('fa');
    expect(uiLocale()).toBe('fa-IR-u-ca-persian-nu-latn');
```

Add:

```ts
  it('fa dates use Persian calendar with Latin digits', async () => {
    await i18next.changeLanguage('fa');
    const date = new Date('2026-07-09T12:00:00Z');
    const rendered = date.toLocaleDateString(uiLocale(), { timeZone: 'UTC' });
    expect(rendered).toMatch(/1405/);
    expect(rendered).not.toMatch(/[۰-۹]/);
  });
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /opt/cabinet && npx vitest run src/utils/formatDate.test.ts src/utils/uiLocale.test.ts
```

Expected: FAIL (`Module not found: formatDate` and `fa-IR` !== `fa-IR-u-ca-persian-nu-latn`).

- [ ] **Step 3: Minimal implementation**

Create `/opt/cabinet/src/utils/formatDate.ts` (donor `/opt/remnabot/cabinet/src/utils/formatDate.ts` verbatim):

```ts
const LOCALE_MAP: Record<string, string> = {
  ru: 'ru-RU',
  en: 'en-US',
  zh: 'zh-CN',
  fa: 'fa-IR-u-nu-latn',
};

function resolveLocale(lang?: string): string | undefined {
  if (!lang) return undefined;
  const code = lang.split('-')[0].toLowerCase();
  return LOCALE_MAP[code] ?? lang;
}

function isJalaliLanguage(lang?: string): boolean {
  return (lang ?? '').split('-')[0].toLowerCase() === 'fa';
}

export function formatUserDate(
  iso: string | null | undefined,
  lang?: string,
  options: Intl.DateTimeFormatOptions = {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  },
): string {
  if (!iso) return '—';
  try {
    const normalized = iso.endsWith('Z') || iso.includes('+') ? iso : `${iso}Z`;
    const date = new Date(normalized);
    if (Number.isNaN(date.getTime())) return '—';

    const locale = resolveLocale(lang);
    const jalali = isJalaliLanguage(lang);

    return date.toLocaleDateString(locale, jalali ? { ...options, calendar: 'persian' } : options);
  } catch {
    return '—';
  }
}

export function formatUserDateTime(
  iso: string | null | undefined,
  lang?: string,
): string {
  return formatUserDate(iso, lang, {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}
```

In `/opt/cabinet/src/utils/uiLocale.ts` change the fa row:

```ts
  fa: 'fa-IR-u-ca-persian-nu-latn',
```

In `/opt/cabinet/src/components/subscription/SubscriptionListCard.tsx`:

- Add `import { formatUserDate } from '../../utils/formatDate';`
- Delete the local `function formatDate(...)`.
- Replace `{formatDate(subscription.end_date, i18n.language)}` with `{formatUserDate(subscription.end_date, i18n.language)}`.

- [ ] **Step 4: Run tests**

```bash
cd /opt/cabinet && npx vitest run src/utils/formatDate.test.ts src/utils/uiLocale.test.ts
```

Expected: PASS (Jalali string is `1405/04/18` on this host).

- [ ] **Step 5: Commit**

```bash
cd /opt/cabinet
git add src/utils/formatDate.ts src/utils/formatDate.test.ts src/utils/uiLocale.ts src/utils/uiLocale.test.ts src/components/subscription/SubscriptionListCard.tsx
git commit -m "$(cat <<'EOF'
feat(i18n): Jalali dates with Latin digits for fa

EOF
)"
```

---

### Task 3: RTL isolate for amounts and subscription URLs

**Files:**
- Create: `/opt/cabinet/src/utils/ltrIsolate.tsx`
- Test: `/opt/cabinet/src/utils/ltrIsolate.test.tsx` (node + react-dom/server) **or** keep it CSS-only if jsdom is painful — prefer a static class test + TrafficUsageText unit test that does not need jsdom
- Create: `/opt/cabinet/src/components/subscription/TrafficUsageText.tsx`
- Test: `/opt/cabinet/src/components/subscription/TrafficUsageText.test.ts`
- Modify: `/opt/cabinet/src/styles/globals.css` (`@layer components` block, add `.url-ltr`)
- Modify: `/opt/cabinet/src/pages/Subscription.tsx` (traffic span + subscription URL)

**Interfaces:**
- Consumes: `formatTraffic` from `/opt/cabinet/src/utils/formatTraffic.ts`
- Produces: `LtrIsolate` props `{ children, className?: string }`; `TrafficUsageText({ usedGb, limitGb?, isUnlimited?, className?, style? })`; CSS class `url-ltr`

`TrafficUsageText.test.ts` can assert the exported function exists by rendering to a string via `react-dom/server` if available; simpler: test `formatTraffic` is used by importing the component and using `react-dom/server.renderToStaticMarkup` — check package has `react-dom`. It does.

- [ ] **Step 1: Write failing tests**

`/opt/cabinet/src/components/subscription/TrafficUsageText.test.ts`:

```ts
import { describe, expect, it } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';
import { createElement } from 'react';
import { TrafficUsageText } from './TrafficUsageText';

describe('TrafficUsageText', () => {
  it('sets dir=ltr and unicode-bidi isolate', () => {
    const html = renderToStaticMarkup(
      createElement(TrafficUsageText, { usedGb: 0, limitGb: 10, isUnlimited: false }),
    );
    expect(html).toContain('dir="ltr"');
    expect(html).toMatch(/unicode-bidi:isolate|unicode-bidi: isolate/);
  });
});
```

`/opt/cabinet/src/utils/ltrIsolate.test.ts`:

```ts
import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';

describe('url-ltr css', () => {
  it('defines isolate for RTL URL fields', () => {
    const css = readFileSync(new URL('../styles/globals.css', import.meta.url), 'utf8');
    expect(css).toMatch(/\.url-ltr\s*\{/);
    expect(css).toMatch(/unicode-bidi:\s*isolate/);
  });
});
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /opt/cabinet && npx vitest run src/components/subscription/TrafficUsageText.test.ts src/utils/ltrIsolate.test.ts
```

Expected: FAIL (module / class missing).

- [ ] **Step 3: Minimal implementation**

Create `/opt/cabinet/src/utils/ltrIsolate.tsx`:

```tsx
import type { ReactNode } from 'react';

export function LtrIsolate({
  children,
  className = '',
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <span dir="ltr" className={`inline-block [unicode-bidi:isolate] ${className}`}>
      {children}
    </span>
  );
}
```

Create `/opt/cabinet/src/components/subscription/TrafficUsageText.tsx`:

```tsx
import { formatTraffic } from '../../utils/formatTraffic';

interface TrafficUsageTextProps {
  usedGb: number;
  limitGb?: number;
  isUnlimited?: boolean;
  className?: string;
  style?: React.CSSProperties;
}

/** LTR-isolated traffic amounts for RTL layouts (e.g. 0 MB / 10.0 GB). */
export function TrafficUsageText({
  usedGb,
  limitGb,
  isUnlimited = false,
  className = '',
  style,
}: TrafficUsageTextProps) {
  const text =
    isUnlimited || limitGb === undefined
      ? formatTraffic(usedGb)
      : `${formatTraffic(usedGb)} / ${formatTraffic(limitGb)}`;

  return (
    <span
      dir="ltr"
      className={`inline-block font-mono tabular-nums [unicode-bidi:isolate] ${className}`}
      style={style}
    >
      {text}
    </span>
  );
}
```

In `/opt/cabinet/src/styles/globals.css` inside `@layer components {` after the opening (before `.bento-card` is fine):

```css
  /* URL / deep-link fields in RTL (fa) UI — show https:// start, not the tail */
  .url-ltr {
    direction: ltr;
    text-align: left;
    unicode-bidi: isolate;
  }
```

In `/opt/cabinet/src/pages/Subscription.tsx`:

- Add `import { TrafficUsageText } from '../components/subscription/TrafficUsageText';`
- Replace the traffic amount `<span className="font-mono text-[11px] text-dark-50/30">` block (~lines 934–938) with:

```tsx
                    <span className="font-mono text-[11px] text-dark-50/30">
                      <TrafficUsageText
                        usedGb={usedGb}
                        limitGb={subscription.traffic_limit_gb}
                        isUnlimited={isUnlimited}
                      />
                    </span>
```

- Find where `subscription.subscription_url` is shown as text (copy/link field). Add `className="url-ltr"` (or append it) on that element. If the URL is only used as `navigate(...)` and not displayed as a string, wrap the visible copy-target if any. At minimum, any `<code>` or input showing the URL must include `url-ltr`.

Also wrap the list-card traffic numbers in `SubscriptionListCard.tsx` (the `${trafficUsed.toFixed(1)} / ${trafficLimit}` span) with `dir="ltr"` + `[unicode-bidi:isolate]` or `TrafficUsageText` if `usedGb` is in GB already (`trafficUsed` is fine to pass as `usedGb` if it is already GB).

- [ ] **Step 4: Run tests**

```bash
cd /opt/cabinet && npx vitest run src/components/subscription/TrafficUsageText.test.ts src/utils/ltrIsolate.test.ts
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
cd /opt/cabinet
git add src/utils/ltrIsolate.tsx src/utils/ltrIsolate.test.ts src/components/subscription/TrafficUsageText.tsx src/components/subscription/TrafficUsageText.test.ts src/styles/globals.css src/pages/Subscription.tsx src/components/subscription/SubscriptionListCard.tsx
git commit -m "$(cat <<'EOF'
fix(ui): isolate traffic amounts and subscription URLs in RTL

EOF
)"
```

---

### Task 4: User-facing fa terminology (دستگاه / تعرفه)

**Files:**
- Modify: `/opt/cabinet/src/locales/fa.json` (merge only)
- Test: `/opt/cabinet/src/locales/fa-user-terminology.test.ts`

**Interfaces:**
- Consumes: donor `/opt/remnabot/cabinet/src/locales/fa.json` (read-only)
- Produces: user-root keys without `دستگاه` / user `تعرفه` where donor already says `سرویس` or `کاربر`; **admin.** keys unchanged

User roots (prefix of dotted path): `common`, `subscription`, `dashboard`, `gift`, `balance`, `profile`, `support`, `wheel`, `merge`, `quickPurchase`, `purchase`, `traffic`, `devices`, `nav` — **exclude** any path starting with `admin.`.

- [ ] **Step 1: Write the failing test**

```ts
import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';

const USER_ROOTS = new Set([
  'common',
  'subscription',
  'dashboard',
  'gift',
  'balance',
  'profile',
  'support',
  'wheel',
  'merge',
  'quickPurchase',
  'purchase',
  'traffic',
  'devices',
  'nav',
]);

function walk(obj: unknown, prefix: string, visit: (path: string, value: string) => void): void {
  if (typeof obj === 'string') {
    visit(prefix, obj);
    return;
  }
  if (obj && typeof obj === 'object' && !Array.isArray(obj)) {
    for (const [k, v] of Object.entries(obj as Record<string, unknown>)) {
      walk(v, prefix ? `${prefix}.${k}` : k, visit);
    }
  }
}

describe('fa user terminology', () => {
  const fa = JSON.parse(readFileSync(new URL('./fa.json', import.meta.url), 'utf8')) as unknown;

  it('user roots do not say دستگاه', () => {
    const hits: string[] = [];
    walk(fa, '', (path, value) => {
      const root = path.split('.')[0];
      if (root === 'admin') return;
      if (!USER_ROOTS.has(root)) return;
      if (value.includes('دستگاه')) hits.push(path);
    });
    expect(hits).toEqual([]);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /opt/cabinet && npx vitest run src/locales/fa-user-terminology.test.ts
```

Expected: FAIL with a list of paths (today ~dozens under `subscription` / `dashboard`).

- [ ] **Step 3: Overlay donor values (do not replace the file)**

Run this **once** from `/opt/cabinet` (script is throwaway; do not commit the script unless it is useful — prefer inline node):

```bash
cd /opt/cabinet && node --input-type=module <<'EOF'
import { readFileSync, writeFileSync } from 'node:fs';

const USER_ROOTS = new Set([
  'common','subscription','dashboard','gift','balance','profile','support',
  'wheel','merge','quickPurchase','purchase','traffic','devices','nav',
]);

const a = JSON.parse(readFileSync('/opt/remnabot/cabinet/src/locales/fa.json', 'utf8'));
const b = JSON.parse(readFileSync('./src/locales/fa.json', 'utf8'));

function get(obj, path) {
  return path.split('.').reduce((acc, k) => (acc == null ? acc : acc[k]), obj);
}
function set(obj, path, value) {
  const parts = path.split('.');
  let cur = obj;
  for (let i = 0; i < parts.length - 1; i++) {
    if (cur[parts[i]] == null || typeof cur[parts[i]] !== 'object') cur[parts[i]] = {};
    cur = cur[parts[i]];
  }
  cur[parts[parts.length - 1]] = value;
}
function walk(obj, prefix, visit) {
  if (typeof obj === 'string') { visit(prefix, obj); return; }
  if (obj && typeof obj === 'object' && !Array.isArray(obj)) {
    for (const [k, v] of Object.entries(obj)) walk(v, prefix ? `${prefix}.${k}` : k, visit);
  }
}

walk(b, '', (path, bVal) => {
  const root = path.split('.')[0];
  if (root === 'admin' || !USER_ROOTS.has(root)) return;
  const aVal = get(a, path);
  if (typeof aVal !== 'string') return;
  const dirty = bVal.includes('دستگاه') || (bVal.includes('تعرفه') && !bVal.includes('تعرفه.') );
  if (dirty && aVal !== bVal) set(b, path, aVal);
});

writeFileSync('./src/locales/fa.json', JSON.stringify(b, null, 2) + '\n');
EOF
```

Then add **missing** onboarding keys from donor if absent (`subscription.volumeEmptyHint`, `subscription.firstConnectChecklist`, `subscription.configDelivery`) with **ASCII digits**:

```json
    "volumeEmptyHint": "هنوز مصرفی ثبت نشده — کل حجم در دسترس است",
    "firstConnectChecklist": {
      "title": "راهنمای اولین اتصال",
      "step1": "1. «دریافت کانفیگ» را بزنید (QR همین‌جا)",
      "step2": "2. «راهنمای اتصال» → برنامه را انتخاب و نصب کنید",
      "step3": "3. وصل شوید"
    },
    "configDelivery": {
      "title": "کانفیگ شما آماده است",
      "subtitle": "لینک را کپی کنید یا QR را اسکن کنید",
      "copyConfig": "کپی کانفیگ",
      "copied": "کانفیگ کپی شد!",
      "getConfig": "دریافت کانفیگ",
      "qrHint": "با دوربین گوشی اسکن کنید",
      "openGuide": "راهنمای اتصال (نصب برنامه)"
    }
```

Insert under the existing `subscription` object in `fa.json` (pretty-print must remain valid JSON). Do not add `earn.*` keys.

If donor overlay still leaves `دستگاه` in a user root, replace remaining `دستگاه‌ها` → `تعداد کاربر` and `دستگاه` → `کاربر` only in those leftover user paths, then re-run the test.

Keep `admin.*` untouched.

- [ ] **Step 4: Run test**

```bash
cd /opt/cabinet && npx vitest run src/locales/fa-user-terminology.test.ts
python3 -c "import json; json.load(open('/opt/cabinet/src/locales/fa.json'))"
```

Expected: vitest PASS; JSON parses.

- [ ] **Step 5: Commit**

```bash
cd /opt/cabinet
git add src/locales/fa.json src/locales/fa-user-terminology.test.ts
git commit -m "$(cat <<'EOF'
i18n(fa): user terminology overlay from production cabinet

EOF
)"
```

---

### Task 5: Subscription first-connect UX (no file replace)

**Files:**
- Create: `/opt/cabinet/src/components/subscription/ConfigDeliverySheet.tsx` (copy donor)
- Create: `/opt/cabinet/src/utils/subscriptionDisplayLabel.ts`
- Test: `/opt/cabinet/src/utils/subscriptionDisplayLabel.test.ts`
- Modify: `/opt/cabinet/src/pages/Subscription.tsx`
- Modify: `/opt/cabinet/src/components/subscription/SubscriptionListCard.tsx` (title via display label)

**Interfaces:**
- Consumes: `subscription_url`, `traffic_used_gb`, `id`; optional `panel_username?: string` on list items (1.67 type may omit it — helper must accept a structural type, not require a bot API change)
- Produces: `getSubscriptionDisplayLabel(sub, t)`; `ConfigDeliverySheet` props as donor

Skip `DisableSubscriptionSheet` (no `user_disabled` on 1.67 types).

- [ ] **Step 1: Write the failing test**

```ts
import { describe, expect, it } from 'vitest';
import { getSubscriptionDisplayLabel } from './subscriptionDisplayLabel';

const t = (_key: string, fallback: string) => fallback;

describe('getSubscriptionDisplayLabel', () => {
  it('hides user_unknown prefix', () => {
    const label = getSubscriptionDisplayLabel(
      { tariff_name: 'Moon', panel_username: 'user_unknown_abc' },
      t,
    );
    expect(label).toBe('Moon');
    expect(label).not.toMatch(/user_unknown/);
  });

  it('uses panel username when real', () => {
    expect(
      getSubscriptionDisplayLabel({ tariff_name: 'Moon', panel_username: 'mobile_x_1001' }, t),
    ).toBe('mobile_x_1001');
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /opt/cabinet && npx vitest run src/utils/subscriptionDisplayLabel.test.ts
```

Expected: FAIL (module not found).

- [ ] **Step 3: Implementation**

Create `/opt/cabinet/src/utils/subscriptionDisplayLabel.ts`:

```ts
export type SubscriptionLabelSource = {
  tariff_name?: string | null;
  panel_username?: string | null;
  account_sequence?: number | null;
};

const USER_UNKNOWN_PREFIX = 'user_unknown_';

export function getSubscriptionDisplayLabel(
  sub: SubscriptionLabelSource,
  t: (key: string, fallback: string) => string,
  isMultiTariff = false,
): string {
  let panel = (sub.panel_username ?? '').trim();
  if (panel.startsWith(USER_UNKNOWN_PREFIX)) {
    panel = '';
  }
  if (panel) return panel;

  const defaultName = t('subscription.defaultName', 'Подписка');
  if (isMultiTariff && sub.account_sequence) {
    return `${sub.tariff_name || defaultName} #${sub.account_sequence}`;
  }
  return sub.tariff_name || defaultName;
}
```

Copy `/opt/remnabot/cabinet/src/components/subscription/ConfigDeliverySheet.tsx` to `/opt/cabinet/src/components/subscription/ConfigDeliverySheet.tsx` unchanged (uses existing `@/components/primitives/Sheet` and `qrcode.react` already in 1.67).

In `/opt/cabinet/src/pages/Subscription.tsx`:

1. Import `ConfigDeliverySheet`, `useState` already present.
2. Add state: `const [configSheetOpen, setConfigSheetOpen] = useState(false);`
3. After the traffic block, if `usedGb === 0` (or `traffic_used_gb === 0`), render:

```tsx
<p className="mb-3 text-[11px] text-dark-50/40">{t('subscription.volumeEmptyHint')}</p>
```

4. Add first-connect checklist (once per detail view, above the connect button):

```tsx
<div className="mb-4 rounded-[14px] p-3 text-[12px] text-dark-50/70">
  <div className="mb-1 font-semibold">{t('subscription.firstConnectChecklist.title')}</div>
  <ul className="list-disc space-y-1 ps-4">
    <li>{t('subscription.firstConnectChecklist.step1')}</li>
    <li>{t('subscription.firstConnectChecklist.step2')}</li>
    <li>{t('subscription.firstConnectChecklist.step3')}</li>
  </ul>
</div>
```

5. Change the connect button `onClick` so it opens the sheet instead of only navigating:

```tsx
onClick={() => {
  if (isAtDeviceLimit) {
    haptic.notification('error');
    return;
  }
  setConfigSheetOpen(true);
}}
```

6. Mount at the end of the detail return (next to other sheets):

```tsx
<ConfigDeliverySheet
  open={configSheetOpen}
  onClose={() => setConfigSheetOpen(false)}
  configUrl={subscription.subscription_url}
  subscriptionId={subscription.id}
/>
```

In `SubscriptionListCard.tsx`, replace the title text `subscription.tariff_name || t('subscription.defaultName', ...)` with `getSubscriptionDisplayLabel(subscription, t)`.

- [ ] **Step 4: Run tests + type-check**

```bash
cd /opt/cabinet && npx vitest run src/utils/subscriptionDisplayLabel.test.ts src/locales/fa-user-terminology.test.ts
cd /opt/cabinet && npm run type-check
```

Expected: tests PASS; `tsc` clean. If `ConfigDeliverySheet` fails types, fix only that file.

- [ ] **Step 5: Commit**

```bash
cd /opt/cabinet
git add src/components/subscription/ConfigDeliverySheet.tsx src/utils/subscriptionDisplayLabel.ts src/utils/subscriptionDisplayLabel.test.ts src/pages/Subscription.tsx src/components/subscription/SubscriptionListCard.tsx src/locales/fa.json
git commit -m "$(cat <<'EOF'
feat(cabinet): first-connect sheet and subscription labels

EOF
)"
```

---

### Task 6: Agent verification + user smoke (STOP)

**Files:** none required if Task 1–5 PASS.

- [ ] **Step 1: Agent suite**

```bash
cd /opt/cabinet && npx vitest run src/i18n.defaults.test.ts src/utils/formatDate.test.ts src/utils/uiLocale.test.ts src/utils/ltrIsolate.test.ts src/components/subscription/TrafficUsageText.test.ts src/locales/fa-user-terminology.test.ts src/utils/subscriptionDisplayLabel.test.ts
cd /opt/cabinet && npm run type-check
cd /opt/cabinet && npx biome check src/i18n.ts src/utils/formatDate.ts src/utils/uiLocale.ts src/utils/ltrIsolate.tsx src/components/subscription/TrafficUsageText.tsx src/components/subscription/ConfigDeliverySheet.tsx src/utils/subscriptionDisplayLabel.ts src/pages/Subscription.tsx src/components/subscription/SubscriptionListCard.tsx
```

Expected: all PASS. If Biome fails, `npx biome check --write` on those files and amend **only if** the commit is yours, unpushed, and the hook modified files — otherwise a new commit `chore: biome Layer A`.

- [ ] **Step 2: Recreate cabinet frontend only** (do not rebuild remnawave_bot)

```bash
cd /opt/cabinet && docker compose -f docker-compose.yml -f docker-compose.rc.yml up -d --build cabinet_frontend
```

Expected: container healthy; `GET https://panel.rookari.com/` still 200.

- [ ] **Step 3: User smoke (STOP — user-visible)**

مسیر / انتظار:

1. مسیر: باز کردن `https://panel.rookari.com` بدون `cabinet_language` در localStorage (پنجرهٔ ناشناس). انتظار: اولین رنگ UI فارسی و راست‌به‌چپ است، نه روسی.
2. مسیر: ورود با تلگرام تست → اشتراک من. انتظار: تاریخ پایان شمسی با رقم انگلیسی (مثلاً `1405/...`)؛ حجم به صورت LTR؛ لینک کانفیگ از `https://` شروع می‌شود.
3. مسیر: دکمهٔ اتصال / دریافت کانفیگ. انتظار: شیت QR + کپی؛ متن «دستگاه» روی مسیر کاربر دیده نشود (تعداد کاربر / اتصال).

Operator replies `تایید` or `2 FAIL: …`.

Do **not** start M7 from this smoke. Layer C (`/sales`) stays a later plan.

---

## Spec coverage (self-review)

| Spec Layer A | Task |
|---|---|
| A1 fa + RTL html | Task 1 |
| A2 Jalali | Task 2 |
| A3 wording | Task 4 |
| A4 RTL isolate | Task 3 |
| A5 subscription UX | Task 5 (Disable sheet skipped — no API) |
| Layer B/C / M7 | Explicitly out of plan |

Placeholders: none. `applyTelegramLanguage` kept as a deprecated wrapper so `main.tsx` does not need a third commit.
