# Multi-Tenancy Reference

Manage agents across tenants using tags.

## Tag Format

Tags are `key:value` strings on agents. Filtering uses AND logic — all specified tags must match.

```yaml
agents:
  - name: acme-support
    tags:
      - "tenant:acme-corp"
      - "role:support"
      - "env:production"
```

## Patterns

### B2B

```yaml
tags:
  - "tenant:client-id"
  - "role:support"
```

### B2B2C

```yaml
tags:
  - "user:user-id"
  - "client:client-id"
  - "role:assistant"
```

## Filtering

Tags work across all relevant commands:

```bash
lettactl get agents --tags "tenant:acme-corp"
lettactl get agents --tags "role:support,env:production"
lettactl describe agent <name>
lettactl send --tags "tenant:acme-corp" "Update"
lettactl report memory --tags "tenant:acme-corp"
```

## SDK: Dynamic Tenant Provisioning

```typescript
async function provisionTenant(tenantId: string) {
  const config = ctl.createFleetConfig()
    .addAgent({
      name: `${tenantId}-support`,
      description: `Support for ${tenantId}`,
      tags: [`tenant:${tenantId}`, 'role:support'],
      system_prompt: { from_file: 'prompts/support.md' },
      llm_config: { model: 'google_ai/gemini-2.5-pro', context_window: 32000 },
      shared_blocks: ['company-kb'],
    })
    .build();

  await ctl.deployFleet(config);
}
```

## Scale

- Server-side filtering for performance
- Async pagination (1000 items per page)
- Concurrency limit of 5 for update operations
