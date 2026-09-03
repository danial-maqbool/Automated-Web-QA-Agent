# Safe Testing & Ethical Testing Guardrails

## 1. Authorized Testing Scope
WebQA Agent is built specifically for quality assurance on authorized systems:
- Environments you own or manage;
- Local development instances (e.g., `localhost:3000`, `127.0.0.1:5173`);
- Staging and preview deployments;
- Explicitly permitted staging or QA environments.

The system explicitly does **not** implement:
- CAPTCHA bypass or bot obfuscation;
- Credential stuffing, brute-forcing, or password cracking;
- Authentication bypass or privilege escalation;
- Paywall or billing gate bypass;
- Denial-of-Service (DoS) or unbounded load testing;
- Automated mass account creation or spam generation;
- Automated financial transactions or payment completion.

---

## 2. Action Safety Classifier

During automated exploration and button testing, every actionable element (button, link, form submit, input) is evaluated before interaction.

### Classification Categories:

| Classification | Action Behavior | Examples |
|---|---|---|
| **SAFE** | Executed automatically in quick/full exploratory scans | Navigation, search inputs, tabs, dropdowns, accordions, safe filters |
| **CAUTION** | Requires explicit project-level configuration to execute | Non-critical form submissions, contact queries, modal triggers |
| **BLOCKED** | Strictly prevented by default across all autonomous runs | Delete, remove account, pay, checkout, buy, submit order, publish, transfer |

### Blocked Action Keywords
WebQA inspects text content, `aria-label`, `title`, `name`, `id`, `data-testid`, and form `action` URLs for blocked tokens including:
- `delete`, `remove`, `destroy`, `drop`
- `purchase`, `buy`, `pay`, `checkout`, `charge`, `order`, `subscribe`
- `publish`, `deploy`, `send`, `post`, `broadcast`
- `transfer`, `terminate`, `deactivate`, `disable account`

---

## 3. Data Protection & Redaction

### Network and Console Redaction
To protect test environments and credentials, the network monitor automatically redacts sensitive headers and payloads before persistence:
- Headers: `Authorization`, `Proxy-Authorization`, `Cookie`, `Set-Cookie`, `X-Api-Key`, `X-Auth-Token`
- Payload fields: `password`, `secret`, `token`, `access_token`, `refresh_token`, `api_key`, `card_number`, `cvv`

### Storage Isolation
- Authentication cookies and Playwright storage states (`data/auth/`) are stored locally and gitignored.
- Credentials and tokens are never written into reports or database issue exports.
