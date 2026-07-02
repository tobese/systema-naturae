# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: navigation.spec.ts >> CROSS-FAMILY >> clicking a family from class focus navigates to that family
- Location: tests/navigation.spec.ts:244:3

# Error details

```
Error: page.waitForSelector: Target page, context or browser has been closed
Call log:
  - waiting for locator('[data-rank]') to be visible

```

```
Error: browserContext.close: Target page, context or browser has been closed
```