# WebQA Deterministic QA Rules Engine

WebQA Agent employs a rule-based deterministic scoring and defect identification engine. Every rule operates independently and does not require external AI connectivity.

---

## QA Rule Catalog

| Rule ID | Category | Name | Trigger Condition | Severity | Confidence | Remediation |
|---|---|---|---|---|---|---|
| `LINK_HTTP_404` | Navigation | Broken Link (404) | Navigation or resource returns HTTP 404 | HIGH | 1.0 | Fix URL or restore missing destination route |
| `LINK_HTTP_500` | Navigation | Server Error (5xx) | Destination returns HTTP 500-599 | CRITICAL | 1.0 | Investigate server-side backend error |
| `LINK_EMPTY_HREF` | Navigation | Empty Anchor Href | `<a href="">` or `<a href="#">` without handler | LOW | 0.9 | Supply valid route or convert to semantic `<button>` |
| `LINK_MALFORMED` | Navigation | Malformed URL | Link target fails standard URI parsing | MEDIUM | 0.95 | Correct malformed URL syntax |
| `CONSOLE_UNCAUGHT_ERR` | Console | Uncaught Exception | `window.onerror` or unhandled promise rejection | HIGH | 0.98 | Fix underlying JavaScript exception |
| `CONSOLE_REACT_HYDRATION` | Console | React Hydration Mismatch | Console log matches React SSR hydration error pattern | MEDIUM | 0.95 | Align client render with SSR markup |
| `CONSOLE_CSP_VIOLATION` | Console | Content Security Policy | CSP directive blocks inline script/style/eval | MEDIUM | 0.95 | Update CSP header or remove non-compliant script |
| `NET_REQUEST_FAILED` | Network | Network Request Failed | Fetch/XHR request aborted or connection failed | HIGH | 0.95 | Verify API endpoint availability and CORS configuration |
| `NET_STATUS_5XX` | Network | API Server Error | Backend API returns 500, 502, 503, or 504 | CRITICAL | 1.0 | Inspect API logs and backend exceptions |
| `NET_STATUS_4XX` | Network | Client Error on Fetch | Backend API returns 400, 401, 403, 404 | MEDIUM | 1.0 | Verify request parameters, payloads, or auth tokens |
| `IMG_BROKEN_SRC` | Content | Broken Image | Image request failed or naturalWidth === 0 | MEDIUM | 0.98 | Provide valid image path or fallback graphic |
| `IMG_MISSING_ALT` | Accessibility | Image Missing Alt Text | `<img>` lacks `alt` attribute or empty non-decorative | LOW | 0.95 | Add descriptive `alt` attribute for screen readers |
| `FORM_REQ_EMPTY_SUBMIT` | Form | Missing Required Validation | Form submits successfully with empty required inputs | HIGH | 0.9 | Add client/server validation to required fields |
| `FORM_INVALID_EMAIL` | Form | Invalid Email Accepted | Non-email value accepted without input validation | MEDIUM | 0.9 | Use `type="email"` and server-side email validation |
| `BTN_NO_RESPONSE` | Functional | Dead Interactive Button | Clickable button produces no state change, network call, or event | LOW | 0.8 | Attach click handler or disable inactive button |
| `LAYOUT_HORIZ_OVERFLOW` | Responsive | Horizontal Viewport Leak | `document.documentElement.scrollWidth > window.innerWidth` | MEDIUM | 0.95 | Constrain width, apply `max-width: 100%`, fix margins |
| `A11Y_AXE_VIOLATION` | Accessibility | WCAG Violation | Evaluated from local `axe-core` scan | Variable | 0.95 | Follow WCAG remediation instructions per violation ID |
| `SEO_MISSING_TITLE` | SEO | Missing Page Title | `<title>` tag missing, blank, or whitespace | LOW | 1.0 | Add descriptive `<title>` tag |
| `SEO_MISSING_DESC` | SEO | Missing Meta Description | `<meta name="description">` missing or empty | INFO | 1.0 | Provide meta description for search indexers |
| `PERF_LCP_BUDGET` | Performance | LCP Threshold Exceeded | Measured LCP exceeds configured project budget | MEDIUM | 0.85 | Optimize critical image assets and server response times |
| `VISUAL_REGRESSION_DELTA`| Visual | Layout Drift / Regression | Pixel diff percentage exceeds baseline tolerance | HIGH | 0.9 | Inspect visual diff against established baseline |
