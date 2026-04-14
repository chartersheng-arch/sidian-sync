# Cloudflare Browser Rendering Skill Reference

**Description**: Expert knowledge for Cloudflare Browser Rendering - control headless Chrome on Cloudflare's global network for browser automation, screenshots, PDFs, web scraping, testing, and content generation.

**When to use**: Any task involving Cloudflare Browser Rendering including: taking screenshots, generating PDFs, web scraping, browser automation, testing web applications, extracting structured data, capturing page metrics, or automating browser interactions.

## Decision Tree

### REST API vs Workers Bindings

**Use REST API when:**
- One-off, stateless tasks (screenshot, PDF, content fetch)
- No Workers infrastructure yet
- Simple integrations from external services
- Need quick prototyping without deployment

**Use Workers Bindings when:**
- Complex browser automation workflows
- Need session reuse for performance
- Multiple page interactions per request
- Custom scripting and logic required
- Building production applications

### Puppeteer vs Playwright

| Feature | Puppeteer | Playwright |
|---------|-----------|------------|
| API Style | Chrome DevTools Protocol | High-level abstractions |
| Selectors | CSS, XPath | CSS, text, role, test-id |
| Best for | Advanced control, CDP access | Quick automation, testing |
| Learning curve | Steeper | Gentler |

**Use Puppeteer:** Need CDP protocol access, Chrome-specific features, migration from existing Puppeteer code
**Use Playwright:** Modern selector APIs, cross-browser patterns, faster development

## Tier Limits Summary

| Limit | Free Tier | Paid Tier |
|-------|-----------|-----------|
| Daily browser time | 10 minutes | Unlimited* |
| Concurrent sessions | 3 | 30 |
| Requests per minute | 6 | 180 |

*Subject to fair-use policy. See [gotchas.md](skills/02-claw%20skills/cloudflare-deploy/references/browser-rendering/gotchas.md) for details.

## Reading Order

**New to Browser Rendering:**
1. [configuration.md](skills/02-claw%20skills/cloudflare-deploy/references/browser-rendering/configuration.md) - Setup and deployment
2. [patterns.md](skills/02-claw%20skills/cloudflare-deploy/references/browser-rendering/patterns.md) - Common use cases with examples
3. [api.md](skills/02-claw%20skills/cloudflare-deploy/references/browser-rendering/api.md) - API reference
4. [gotchas.md](skills/02-claw%20skills/cloudflare-deploy/references/browser-rendering/gotchas.md) - Avoid common pitfalls

**Specific task:**
- **Setup/deployment** → [configuration.md](skills/02-claw%20skills/cloudflare-deploy/references/browser-rendering/configuration.md)
- **API reference/endpoints** → [api.md](skills/02-claw%20skills/cloudflare-deploy/references/browser-rendering/api.md)
- **Example code/patterns** → [patterns.md](skills/02-claw%20skills/cloudflare-deploy/references/browser-rendering/patterns.md)
- **Debugging/troubleshooting** → [gotchas.md](skills/02-claw%20skills/cloudflare-deploy/references/browser-rendering/gotchas.md)

**REST API users:**
- Start with [api.md](skills/02-claw%20skills/cloudflare-deploy/references/browser-rendering/api.md) REST API section
- Check [gotchas.md](skills/02-claw%20skills/cloudflare-deploy/references/browser-rendering/gotchas.md) for rate limits

**Workers users:**
- Start with [configuration.md](skills/02-claw%20skills/cloudflare-deploy/references/browser-rendering/configuration.md)
- Review [patterns.md](skills/02-claw%20skills/cloudflare-deploy/references/browser-rendering/patterns.md) for session management
- Reference [api.md](skills/02-claw%20skills/cloudflare-deploy/references/browser-rendering/api.md) for Workers Bindings

## In This Reference

- **[configuration.md](skills/02-claw%20skills/cloudflare-deploy/references/browser-rendering/configuration.md)** - Setup, deployment, wrangler config, compatibility
- **[api.md](skills/02-claw%20skills/cloudflare-deploy/references/browser-rendering/api.md)** - REST API endpoints + Workers Bindings (Puppeteer/Playwright)
- **[patterns.md](skills/02-claw%20skills/cloudflare-deploy/references/browser-rendering/patterns.md)** - Common patterns, use cases, real examples
- **[gotchas.md](skills/02-claw%20skills/cloudflare-deploy/references/browser-rendering/gotchas.md)** - Troubleshooting, best practices, tier limits, common errors

## See Also

- [Cloudflare Docs](https://developers.cloudflare.com/browser-rendering/)
