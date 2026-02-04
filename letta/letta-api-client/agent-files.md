# Agent Files & Folders

## Agent Files (.af) - Import/Export

Agent Files (.af) are portable snapshots of an agent's configuration, memory, and tools.

### Exporting an Agent

```python
# Export to .af format
schema = client.agents.export_file(agent_id=agent.id)

# Save to file
with open("my_agent.af", "w") as f:
    import json
    json.dump(schema, f)
```

```typescript
const schema = await client.agents.exportFile(agent.id);
```

### Importing an Agent

```python
# Import from .af file
with open("my_agent.af", "rb") as f:
    agent = client.agents.import_file(file=f)

print(f"Imported agent: {agent.id}")
```

```typescript
import { readFileSync } from "fs";

const file = new Blob([readFileSync("my_agent.af")]);
const agent = await client.agents.importFile(file);
```

### What's Included in .af Files

| Included | Not Included |
|----------|--------------|
| Model configuration | Archival memory passages |
| Memory blocks | Attached folders/files |
| Attached tools | Agent secrets |
| System instructions | Message history |
| Agent metadata | MCP server connections |

### Migration Checklist

When moving an agent to a new environment:

1. Export .af file
2. Import to new environment
3. Re-configure secrets (`client.agents.update(secrets={...})`)
4. Re-upload and attach folders
5. Restore archival memory if needed
6. Reconnect MCP servers

---

## Folders - Attaching Files to Agents

Give agents access to documents via the Folders API.

### Creating and Uploading

```python
# Create a folder
folder = client.folders.create(name="knowledge_base")

# Upload files
with open("product_manual.pdf", "rb") as f:
    client.folders.files.upload(file=f, folder_id=folder.id)

with open("faq.txt", "rb") as f:
    client.folders.files.upload(file=f, folder_id=folder.id)
```

```typescript
import { createReadStream } from "fs";

const folder = await client.folders.create({ name: "knowledge_base" });

await client.folders.files.upload(
  createReadStream("product_manual.pdf"),
  folder.id
);
```

### Attaching to Agent

```python
# Attach folder to agent
client.agents.folders.attach(agent_id=agent.id, folder_id=folder.id)

# Agent now has filesystem tools to read these files
```

```typescript
await client.agents.folders.attach(agent.id, folder.id);
```

### How Agents Use Files

When you attach a folder:
1. Filesystem tools are automatically added to the agent
2. Agent can read, search, and reference file contents
3. Files are chunked and indexed for retrieval

### Listing Folders and Files

```python
# List folders
folders = client.folders.list()
for folder in folders:
    print(f"{folder.id}: {folder.name}")

# List files in a folder
files = client.folders.files.list(folder_id=folder.id)
for file in files:
    print(f"  {file.id}: {file.name}")
```

### Detaching Folders

```python
client.agents.folders.detach(agent_id=agent.id, folder_id=folder.id)
```

### Best Practices

1. **Organize by topic** - Create separate folders for different knowledge domains
2. **Keep files focused** - Smaller, focused documents work better than massive files
3. **Use descriptive names** - Helps agent understand content
4. **PDF and text work best** - Structured formats are easier to parse
