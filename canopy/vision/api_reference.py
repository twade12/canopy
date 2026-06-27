"""Curated API reference for the in-app docs page (see /api/reference)."""

API_REFERENCE = [
    {"group": "Projects", "endpoints": [
        {"method": "GET", "path": "/api/vehicles", "use": "List all projects (with tags).",
         "example": "curl http://localhost:8088/api/vehicles"},
        {"method": "POST", "path": "/api/vehicles", "use": "Create a project.",
         "example": "curl -X POST http://localhost:8088/api/vehicles -H 'Content-Type: application/json' -d '{\"label\":\"2016 F-250 PCM\"}'"},
        {"method": "GET", "path": "/api/vehicles/{id}", "use": "Full project detail (diagrams, pinouts, memories, messages, tags).",
         "example": "curl http://localhost:8088/api/vehicles/1"},
        {"method": "PATCH", "path": "/api/vehicles/{id}", "use": "Update identity (vin/year/make/model/label).",
         "example": "curl -X PATCH http://localhost:8088/api/vehicles/1 -H 'Content-Type: application/json' -d '{\"make\":\"Ford\"}'"},
        {"method": "DELETE", "path": "/api/vehicles/{id}", "use": "Delete a project."},
    ]},
    {"group": "Diagrams", "endpoints": [
        {"method": "POST", "path": "/api/vehicles/{id}/diagram", "use": "Upload an image or PDF diagram (multipart 'file').",
         "example": "curl -X POST http://localhost:8088/api/vehicles/1/diagram -F file=@diagram.pdf"},
        {"method": "GET", "path": "/api/diagram/{did}/image?page=N", "use": "Render a diagram page to PNG.",
         "example": "curl 'http://localhost:8088/api/diagram/1/image?page=22' -o page.png"},
    ]},
    {"group": "AI extraction", "endpoints": [
        {"method": "POST", "path": "/api/vehicles/{id}/extract", "use": "Extract pinout for a page (or all_pages).",
         "example": "curl -X POST http://localhost:8088/api/vehicles/1/extract -H 'Content-Type: application/json' -d '{\"page\":22}'"},
        {"method": "POST", "path": "/api/vehicles/{id}/identify", "use": "Read VIN/year/make/model from a page."},
        {"method": "POST", "path": "/api/vehicles/{id}/extract-tags", "use": "AI-extract searchable tags from a page."},
        {"method": "POST", "path": "/api/vehicles/{id}/can-plan", "use": "Generate a CAN bench wiring plan."},
    ]},
    {"group": "Chat & memory", "endpoints": [
        {"method": "POST", "path": "/api/vehicles/{id}/chat", "use": "Ask a question (non-streaming).",
         "example": "curl -X POST http://localhost:8088/api/vehicles/1/chat -H 'Content-Type: application/json' -d '{\"message\":\"Which pins are CAN?\",\"page\":22}'"},
        {"method": "POST", "path": "/api/vehicles/{id}/chat/stream", "use": "Ask a question (SSE token stream)."},
        {"method": "GET/POST", "path": "/api/vehicles/{id}/memories", "use": "List / add memories (embedding-deduped)."},
        {"method": "DELETE", "path": "/api/memories/{mid}", "use": "Delete a memory."},
    ]},
    {"group": "Tags", "endpoints": [
        {"method": "GET/POST", "path": "/api/vehicles/{id}/tags", "use": "List / add a tag.",
         "example": "curl -X POST http://localhost:8088/api/vehicles/1/tags -H 'Content-Type: application/json' -d '{\"tag\":\"Duramax\"}'"},
        {"method": "DELETE", "path": "/api/vehicles/{id}/tags/{tag}", "use": "Remove a tag."},
    ]},
]
