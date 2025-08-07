# Risks and Open Questions

## Risks
- **API Changes**: Companies House API is not versioned; backward-incompatible changes could break the SDK.
- **Rate Limiting**: Unexpected rate caps from Companies House could degrade client reliability under load.
- **Async-only Approach**: Some users may lack `asyncio` context or prefer sync clients.
- **Community Engagement**: Adoption might be slow if `chwrapper` remains dominant.

## Open Questions _(Resolved)_
- ❌ Sync wrapper (`CompaniesHouseSyncClient`) will **not** be included in v1.0
- ❌ No support planned for non-Python tooling like OpenAPI specs
- ❌ No client-level caching for now to maintain simplicity