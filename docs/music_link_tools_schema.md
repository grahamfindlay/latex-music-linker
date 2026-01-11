# Tool Schema: Music Linking Pipeline

This document defines platform-agnostic tool interfaces for resolving music entities to smart links.

The tools are intended to be callable by an AI agent or any orchestration system. They do not assume any particular vendor and may be implemented as local functions, HTTP services, or RPC endpoints.

---

## Overview of Tools

There are two primary tools:

1. **Platform Search Resolver** (`music_platform_resolver`)  
2. **Smart Link Resolver** (`smart_link_resolver`)

The recommended call order is:

1. The agent identifies a music entity (album or track) and calls **`music_platform_resolver`**.  
2. The agent passes the returned platform URL to **`smart_link_resolver`**.  
3. The agent inserts the resulting smart link into the LaTeX document.

---

## 1. Tool: `music_platform_resolver`

### Purpose

Given a music entity description (title, artist, type, optional year), this tool finds the best matching result on a target platform (e.g., Apple Music) and returns a canonical platform URL.

The tool may internally use the Apple iTunes Search API, Spotify Web API, or any other suitable service, but this is an implementation detail. The agent only needs to know the input/output schema.

### Interface

**Name:** `music_platform_resolver`

**Input (JSON object):**

```json
{
  "name": "string",
  "artist": "string",
  "type": "string",
  "year": 2025,
  "country": "string"
}
```

#### Input Fields

- `name` (string, required):  
  The title of the music entity (album or track). Example: "God Does Like Ugly".

- `artist` (string, required):  
  The primary artist name. Example: "JID".

- `type` (string, required):  
  The type of music entity. Must be one of:
  - "album"
  - "track"

- `year` (integer, optional):  
  Year of release. Used to disambiguate multiple releases. Example: 2025.

- `country` (string, optional):  
  Country code used for platform search (e.g., "us", "gb").  
  If omitted, an implementation-defined default may be used (commonly "us").

### Output (JSON object):

```json
{
  "platform": "string",
  "url": "string",
  "confidence": 0.98,
  "raw_response": {}
}
```

#### Output Fields

- `platform` (string, required):  
  Name of the platform for which the URL is valid. Example: "apple_music".

- `url` (string, required):  
  Canonical URL to the album or track on the platform. Example:  
  "https://music.apple.com/us/album/god-does-like-ugly/1832251919"

- `confidence` (number, optional):  
  A score between 0.0 and 1.0 indicating confidence in the match. Example: 0.98.

- `raw_response` (object, optional):  
  The raw response from the underlying search API (if available).  
  This can be omitted or truncated if not needed.

### Error Conditions

If no suitable match is found:

```json
{
  "platform": null,
  "url": null,
  "confidence": 0.0,
  "raw_response": {
    "error": "No match found"
  }
}
```

The agent should interpret `url == null` as a signal to skip linking for that entity.

---

## 2. Tool: `smart_link_resolver`

### Purpose

Given a platform-specific music URL (album or track), this tool produces a platform-agnostic smart link URL, typically via a redirector (e.g., Songlink/Odesli).

This is done **without** calling Songlink/Odesli's official API, to avoid rate-limit constraints. Instead, the tool uses their redirect mechanism (e.g., "https://song.link/<platform_url>"), follows the HTTP redirect, and returns the final URL.

### Interface

**Name:** `smart_link_resolver`

**Input (JSON object):**

```json
{
  "platform_url": "string"
}
```

#### Input Fields

- `platform_url` (string, required):  
  A canonical URL pointing to an album or track on a music platform, such as Apple Music or Spotify.  
  Example: "https://music.apple.com/us/album/god-does-like-ugly/1832251919".

### Output (JSON object):

```json
{
  "smartlink_url": "string",
  "redirector_url": "string"
}
```

#### Output Fields

- `smartlink_url` (string, required):  
  The final smart link URL, after following the redirect. Example:  
  "https://album.link/i/1832251919" or "https://song.link/i/1812517950".

- `redirector_url` (string, optional):  
  The intermediate URL used to obtain the smart link, typically constructed as:  
  "https://song.link/<platform_url>".

### Behavior

Implementation guidelines:

1. Construct a redirector URL:
   `https://song.link/<platform_url>`
2. Perform an HTTP GET request following redirects.
3. Capture the final URL after the redirect chain as `smartlink_url`.

If the request fails, set `smartlink_url` to null and include an error message in an optional diagnostic field (implementation-specific).

### Error Conditions

If the request fails (network error, non-2xx status, etc.):

```json
{
  "smartlink_url": null,
  "redirector_url": "https://song.link/https://music.apple.com/us/album/god-does-like-ugly/1832251919",
  "error": "network failure: <details>"
}
```

The agent should treat `smartlink_url == null` as a failure to obtain a smart link and may either skip linking or fall back to the original platform URL.

---

## 3. Recommended Agent Usage Pattern

1. Identify a music entity within the LaTeX document:
   - Infer `name`, `artist`, `type`, and optional `year` from context.

2. Call `music_platform_resolver` with:
   ```json
   {
     "name": "God Does Like Ugly",
     "artist": "JID",
     "type": "album",
     "year": 2025,
     "country": "us"
   }
   ```

3. If `url` is non-null, call `smart_link_resolver`:
   ```json
   {
     "platform_url": "https://music.apple.com/us/album/god-does-like-ugly/1832251919"
   }
   ```

4. If `smartlink_url` is non-null, insert into LaTeX as:
   ```latex
   \href{SMARTLINK_URL}{\textit{Title}}
   ```

5. If either tool fails to provide a usable URL, leave the LaTeX text unchanged and optionally log or report the failure.

---

## 4. Notes on Implementation Flexibility

- These tools can be implemented as:
  - Local functions in a script
  - HTTP microservices
  - Serverless functions
  - Any other callable interface

- The AI agent does not need to know internal details (e.g., iTunes URL formats).  
  It only needs the I/O contracts described here.

- Additional fields can be added to the outputs (e.g., debug information, multiple candidate URLs) as long as the documented fields remain stable.
