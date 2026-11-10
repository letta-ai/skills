---
name: datacircle
description: Datacircle's open API lists every GTM API and says who is best for each, with no key.
homepage: https://datacircle.dev
---

# datacircle

Find the best GTM APIs. We benchmark all the GTM APIs and we put the results on our website, https://datacircle.dev.

## Use

The API is at https://api.datacircle.dev/v1, with no key. Its spec is https://api.datacircle.dev/v1/openapi.json.

```bash
curl -s https://api.datacircle.dev/v1/apis
curl -s https://api.datacircle.dev/v1/apis/{slug}/best
curl -s https://api.datacircle.dev/v1/plans
curl -s https://api.datacircle.dev/v1/providers/{slug}
```

Read the spec for each call's filters. The limit is 60 calls a minute from one address.
