# n8n Connection Types Reference

This document explains the different connection types used in n8n workflows and how to structure them correctly when creating workflows programmatically.

## Connection Structure Overview

In n8n, connections are defined as a dictionary where:
- **Keys** are the source node names
- **Values** describe the output and target nodes

```json
{
  "connections": {
    "Source Node Name": {
      "main": [
        [
          {
            "node": "Target Node Name",
            "type": "main",
            "index": 0
          }
        ]
      ]
    }
  }
}
```

## Standard Connections

### Main (Default) Connection Type

The `main` connection type is the standard data flow between nodes.

**Structure:**
```json
{
  "Source Node": {
    "main": [
      [
        { "node": "Target Node", "type": "main", "index": 0 }
      ]
    ]
  }
}
```

**Example - Linear Flow:**
```json
{
  "connections": {
    "Start": {
      "main": [
        [
          { "node": "HTTP Request", "type": "main", "index": 0 }
        ]
      ]
    },
    "HTTP Request": {
      "main": [
        [
          { "node": "Set", "type": "main", "index": 0 }
        ]
      ]
    }
  }
}
```

### Multiple Outputs (Branches)

Some nodes have multiple outputs (e.g., IF node, Switch node). Each output is a separate array.

**IF Node Example (2 outputs: true/false):**
```json
{
  "IF": {
    "main": [
      [
        { "node": "True Branch Node", "type": "main", "index": 0 }
      ],
      [
        { "node": "False Branch Node", "type": "main", "index": 0 }
      ]
    ]
  }
}
```

**Switch Node Example (3+ outputs):**
```json
{
  "Switch": {
    "main": [
      [
        { "node": "Case 1 Node", "type": "main", "index": 0 }
      ],
      [
        { "node": "Case 2 Node", "type": "main", "index": 0 }
      ],
      [
        { "node": "Default Node", "type": "main", "index": 0 }
      ]
    ]
  }
}
```

### Multiple Targets from Same Output

One output can connect to multiple target nodes.

```json
{
  "Source": {
    "main": [
      [
        { "node": "Target A", "type": "main", "index": 0 },
        { "node": "Target B", "type": "main", "index": 0 }
      ]
    ]
  }
}
```

## AI Node Connections

AI-enabled workflows use special connection types for AI components.

### AI Language Model Connection

Connects an AI model to a node that uses it.

**Type:** `ai_languageModel`

```json
{
  "OpenAI Chat Model": {
    "ai_languageModel": [
      [
        { "node": "AI Agent", "type": "ai_languageModel", "index": 0 }
      ]
    ]
  }
}
```

### AI Tool Connection

Connects tools to an AI agent.

**Type:** `ai_tool`

```json
{
  "Calculator Tool": {
    "ai_tool": [
      [
        { "node": "AI Agent", "type": "ai_tool", "index": 0 }
      ]
    ]
  }
}
```

### AI Memory Connection

Connects memory stores to AI agents.

**Type:** `ai_memory`

```json
{
  "Window Buffer Memory": {
    "ai_memory": [
      [
        { "node": "AI Agent", "type": "ai_memory", "index": 0 }
      ]
    ]
  }
}
```

### AI Output Parser Connection

Connects output parsers to AI chains.

**Type:** `ai_outputParser`

```json
{
  "Structured Output Parser": {
    "ai_outputParser": [
      [
        { "node": "Basic LLM Chain", "type": "ai_outputParser", "index": 0 }
      ]
    ]
  }
}
```

### AI Retriever Connection

Connects document retrievers to AI chains.

**Type:** `ai_retriever`

```json
{
  "Vector Store Retriever": {
    "ai_retriever": [
      [
        { "node": "Retrieval QA Chain", "type": "ai_retriever", "index": 0 }
      ]
    ]
  }
}
```

### AI Document Connection

Connects document loaders to vector stores or splitters.

**Type:** `ai_document`

```json
{
  "File Loader": {
    "ai_document": [
      [
        { "node": "Text Splitter", "type": "ai_document", "index": 0 }
      ]
    ]
  }
}
```

### AI Embeddings Connection

Connects embedding models to vector stores.

**Type:** `ai_embedding`

```json
{
  "OpenAI Embeddings": {
    "ai_embedding": [
      [
        { "node": "Pinecone Vector Store", "type": "ai_embedding", "index": 0 }
      ]
    ]
  }
}
```

### AI Vector Store Connection

Connects vector stores to retrievers or chains.

**Type:** `ai_vectorStore`

```json
{
  "Pinecone Vector Store": {
    "ai_vectorStore": [
      [
        { "node": "Vector Store Retriever", "type": "ai_vectorStore", "index": 0 }
      ]
    ]
  }
}
```

## Complete AI Workflow Example

Here's a complete example showing an AI agent with tools and memory:

```json
{
  "connections": {
    "When clicking 'Test workflow'": {
      "main": [
        [
          { "node": "AI Agent", "type": "main", "index": 0 }
        ]
      ]
    },
    "OpenAI Chat Model": {
      "ai_languageModel": [
        [
          { "node": "AI Agent", "type": "ai_languageModel", "index": 0 }
        ]
      ]
    },
    "Calculator": {
      "ai_tool": [
        [
          { "node": "AI Agent", "type": "ai_tool", "index": 0 }
        ]
      ]
    },
    "Wikipedia": {
      "ai_tool": [
        [
          { "node": "AI Agent", "type": "ai_tool", "index": 0 }
        ]
      ]
    },
    "Window Buffer Memory": {
      "ai_memory": [
        [
          { "node": "AI Agent", "type": "ai_memory", "index": 0 }
        ]
      ]
    }
  }
}
```

## Connection Type Summary Table

| Connection Type | Purpose | Common Use Cases |
|----------------|---------|------------------|
| `main` | Standard data flow | All regular node connections |
| `ai_languageModel` | AI model to agent/chain | OpenAI, Anthropic, Ollama models |
| `ai_tool` | Tool to AI agent | Calculator, Wikipedia, HTTP tools |
| `ai_memory` | Memory to AI agent | Buffer memory, conversation history |
| `ai_outputParser` | Parser to AI chain | JSON parser, structured output |
| `ai_retriever` | Retriever to QA chain | Vector store retriever |
| `ai_document` | Documents to splitter/store | PDF loader, file loader |
| `ai_embedding` | Embeddings to vector store | OpenAI embeddings |
| `ai_vectorStore` | Vector store to retriever | Pinecone, Qdrant, Chroma |

## Connection Index

The `index` field specifies which input of the target node to connect to:
- Most nodes have a single input: `"index": 0`
- Merge nodes may have multiple inputs: `"index": 0`, `"index": 1`, etc.

**Merge Node Example:**
```json
{
  "connections": {
    "Branch A": {
      "main": [
        [
          { "node": "Merge", "type": "main", "index": 0 }
        ]
      ]
    },
    "Branch B": {
      "main": [
        [
          { "node": "Merge", "type": "main", "index": 1 }
        ]
      ]
    }
  }
}
```

## Validation Rules

When creating connections programmatically:

1. **Source node names must match exactly** - The key must be the exact name of a node in the `nodes` array
2. **Target node names must exist** - The `node` field must reference an existing node
3. **Connection types must be compatible** - AI connection types only work with AI-enabled nodes
4. **Output indices must exist** - Don't reference output index 2 on a node with only 2 outputs (0 and 1)
5. **Empty arrays are valid** - `"main": [[]]` is valid for nodes with no outgoing connections

## Tips

- Use the `validate_workflow` tool to check connections before creating a workflow
- Use `get_workflow` to inspect existing workflows and understand their connection structure
- The `clone_workflow` tool preserves all connections when duplicating workflows
