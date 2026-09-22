# API Reference

The Reader Companion backend exposes an asynchronous REST API built with FastAPI.

---

## Endpoints

### 1. `POST /api/upload`
Uploads and parses a PDF document.

- **Headers**: `Content-Type: multipart/form-data`
- **Body**: Form data containing `file` (binary PDF stream).
- **Response Headers**:
  - `X-Doc-Id`: Unique 8-character session identifier (e.g. `e3b0c442`).
- **Response Body**: Array of `Paragraph` objects:
  ```json
  [
    {
      "id": 0,
      "text": "Full cleaned paragraph text.",
      "sentences": [
        "First sentence in paragraph.",
        "Second sentence in paragraph."
      ],
      "page": 1
    }
  ]
  ```

---

### 2. `POST /api/text`
Submits raw text for paragraph chunking, cleaning, and sentence segmentation.

- **Headers**: `Content-Type: application/json`
- **Request Body**:
  ```json
  {
    "text": "First paragraph.\n\nSecond paragraph text..."
  }
  ```
- **Response Headers**:
  - `X-Doc-Id`: Unique session identifier.
- **Response Body**: Array of `Paragraph` objects.

---

### 3. `GET /api/audio`
Synthesizes or retrieves cached audio for a paragraph or individual sentence.

- **Query Parameters**:
  | Parameter | Type | Required | Default | Description |
  |---|---|---|---|---|
  | `id` | `int` | Yes | - | Target paragraph ID |
  | `voice` | `string` | No | `af` | Voice identifier (`af`, `am_adam`, `af_bella`, `am_michael`) |
  | `lang` | `string` | No | `en-us` | Phonemizer language code |
  | `sentence_idx` | `int` | No | `-1` | Zero-based sentence index within paragraph (`-1` reads full paragraph) |
  | `doc_id` | `string` | No | `null` | Active document ID (rejects with 409 if outdated) |
- **Response Headers**:
  - `Content-Type`: `audio/wav`
  - `X-From-Cache`: `"true"` if served from disk cache; `"false"` if synthesized.
  - `X-Doc-Id`: Current active document session ID.
  - `Cache-Control`: `no-cache, no-store, must-revalidate`
- **Response**: Binary WAV audio data.

---

### 4. `GET /api/status`
Returns real-time engine health and audio cache metrics.

- **Response Body**:
  ```json
  {
    "status": "ready",
    "doc_id": "e3b0c442",
    "cache": {
      "file_count": 14,
      "total_size_mb": 1.85
    },
    "paragraphs_count": 8
  }
  ```

---

### 5. `POST /api/preload`
Explicitly queues background synthesis for an upcoming sentence without blocking the caller.

- **Query Parameters**: Same as `/api/audio`.
- **Response**:
  ```json
  { "status": "queued" }
  ```
