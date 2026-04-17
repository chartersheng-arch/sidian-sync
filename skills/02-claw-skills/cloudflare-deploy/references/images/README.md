# Cloudflare Images Skill Reference

**Cloudflare Images** is an end-to-end image management solution providing storage, transformation, optimization, and delivery at scale via Cloudflare's global network.

## Quick Decision Tree

**Need to:**
- **Transform in Worker?** → [api.md](skills/02-claw-skills/cloudflare-deploy/references/images/api.md#workers-binding-api-2026-primary-method) (Workers Binding API)
- **Upload from Worker?** → [api.md](skills/02-claw-skills/cloudflare-deploy/references/images/api.md#upload-from-worker) (REST API)
- **Upload from client?** → [patterns.md](skills/02-claw-skills/cloudflare-deploy/references/images/patterns.md#upload-from-client-direct-creator-upload) (Direct Creator Upload)
- **Set up variants?** → [configuration.md](skills/02-claw-skills/cloudflare-deploy/references/images/configuration.md#variants-configuration)
- **Serve responsive images?** → [patterns.md](skills/02-claw-skills/cloudflare-deploy/references/images/patterns.md#responsive-images)
- **Add watermarks?** → [patterns.md](skills/02-claw-skills/cloudflare-deploy/references/images/patterns.md#watermarking)
- **Fix errors?** → [gotchas.md](skills/02-claw-skills/cloudflare-deploy/references/images/gotchas.md#common-errors)

## Reading Order

**For building image upload/transform feature:**
1. [configuration.md](skills/02-claw-skills/cloudflare-deploy/references/images/configuration.md) - Setup Workers binding
2. [api.md](skills/02-claw-skills/cloudflare-deploy/references/images/api.md#workers-binding-api-2026-primary-method) - Learn transform API
3. [patterns.md](skills/02-claw-skills/cloudflare-deploy/references/images/patterns.md#upload-from-client-direct-creator-upload) - Direct upload pattern
4. [gotchas.md](skills/02-claw-skills/cloudflare-deploy/references/images/gotchas.md) - Check limits and errors

**For URL-based transforms:**
1. [configuration.md](skills/02-claw-skills/cloudflare-deploy/references/images/configuration.md#variants-configuration) - Create variants
2. [api.md](skills/02-claw-skills/cloudflare-deploy/references/images/api.md#url-transform-api) - URL syntax
3. [patterns.md](skills/02-claw-skills/cloudflare-deploy/references/images/patterns.md#responsive-images) - Responsive patterns

**For troubleshooting:**
1. [gotchas.md](skills/02-claw-skills/cloudflare-deploy/references/images/gotchas.md#common-errors) - Error messages
2. [gotchas.md](skills/02-claw-skills/cloudflare-deploy/references/images/gotchas.md#limits) - Size/format limits

## Core Methods

| Method | Use Case | Location |
|--------|----------|----------|
| `env.IMAGES.input().transform()` | Transform in Worker | [api.md:11](skills/02-claw-skills/cloudflare-deploy/references/images/api.md) |
| REST API `/images/v1` | Upload images | [api.md:57](skills/02-claw-skills/cloudflare-deploy/references/images/api.md) |
| Direct Creator Upload | Client-side upload | [api.md:127](skills/02-claw-skills/cloudflare-deploy/references/images/api.md) |
| URL transforms | Static image delivery | [api.md:112](skills/02-claw-skills/cloudflare-deploy/references/images/api.md) |

## In This Reference

- **[api.md](skills/02-claw-skills/cloudflare-deploy/references/images/api.md)** - Complete API: Workers binding, REST endpoints, URL transforms
- **[configuration.md](skills/02-claw-skills/cloudflare-deploy/references/images/configuration.md)** - Setup: wrangler.toml, variants, auth, signed URLs
- **[patterns.md](skills/02-claw-skills/cloudflare-deploy/references/images/patterns.md)** - Patterns: responsive images, watermarks, format negotiation, caching
- **[gotchas.md](skills/02-claw-skills/cloudflare-deploy/references/images/gotchas.md)** - Troubleshooting: limits, errors, best practices

## Key Features

- **Automatic Optimization** - AVIF/WebP format negotiation
- **On-the-fly Transforms** - Resize, crop, blur, sharpen via URL or API
- **Workers Binding** - Transform images in Workers (2026 primary method)
- **Direct Upload** - Secure client-side uploads without backend proxy
- **Global Delivery** - Cached at 300+ Cloudflare data centers
- **Watermarking** - Overlay images programmatically

## See Also

- [Official Docs](https://developers.cloudflare.com/images/)
- [Workers Examples](https://developers.cloudflare.com/images/tutorials/)
