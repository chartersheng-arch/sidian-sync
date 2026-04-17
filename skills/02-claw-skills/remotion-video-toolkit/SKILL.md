---
name: remotion-video-toolkit
description: Complete toolkit for programmatic video creation with Remotion + React. Covers animations, timing, rendering (CLI/Node.js/Lambda/Cloud Run), captions, 3D, charts, text effects, transitions, and media handling. Use when writing Remotion code, building video generation pipelines, or creating data-driven video templates.
---

# Remotion Video Toolkit

Write React components, get real MP4 videos. This skill teaches your AI agent how to build with Remotion — from a first animation to a production rendering pipeline.

29 rules. Every major Remotion feature covered.

---

## What you can build with this

**Personalized video at scale**
Feed user data as JSON props, render a unique video per user. Think Spotify Wrapped, GitHub Unwrapped, onboarding walkthroughs — one template, thousands of outputs.

**Automated social media clips**
Pull live data (stats, leaderboards, product metrics) and render daily or weekly video posts without anyone touching a timeline editor.

**Dynamic ads and marketing videos**
Swap in customer name, product image, pricing. Same template, infinite variations. Render server-side via API or Lambda.

**Animated data visualizations**
Turn dashboards and KPI reports into shareable video clips with animated charts and transitions.

**TikTok and Reels captions**
Transcribe audio, display word-by-word highlighted subtitles, export ready for upload.

**Product showcase videos**
Auto-generate from your database — images, specs, pricing — straight to MP4.

**Educational and explainer content**
Animated course materials, certificate videos, step-by-step walkthroughs — all driven by code.

**Video generation as a service**
Expose rendering as an HTTP endpoint. Your app sends JSON, gets back a video file.

---

## Requirements

- **Node.js** 18+
- **React** 18+ (Remotion renders React components frame-by-frame)
- **Remotion** — scaffold with `npx create-video@latest`
- **FFmpeg** — ships with `@remotion/renderer`, no separate install needed
- For serverless rendering: **AWS** account (Lambda) or **GCP** account (Cloud Run)

---

## What's inside

### Core

| Rule | Description |
|------|-------------|
| [Compositions](compositions.md) | Define videos, stills, folders, default props, dynamic metadata |
| [Rendering](rendering.md) | CLI, Node.js API, AWS Lambda, Cloud Run, Express server patterns |
| [Calculate metadata](calculate-metadata.md) | Set duration, dimensions, and props dynamically at render time |

### Animation and timing

| Rule | Description |
|------|-------------|
| [Animations](skills/02-claw-skills/remotion-video-toolkit/rules/animations.md) | Fade, scale, rotate, slide |
| [Timing](timing.md) | Interpolation curves, easing, spring physics |
| [Sequencing](sequencing.md) | Delay, chain, and orchestrate scenes |
| [Transitions](transitions.md) | Scene-to-scene transitions |
| [Trimming](trimming.md) | Cut the start or end of any animation |

### Text and typography

| Rule | Description |
|------|-------------|
| [Text animations](text-animations.md) | Typewriter, word highlight, reveal effects |
| [Fonts](fonts.md) | Google Fonts and local font loading |
| [Measuring text](measuring-text.md) | Fit text to containers, detect overflow |

### Media

| Rule | Description |
|------|-------------|
| [Videos](videos.md) | Embed, trim, speed, volume, loop, pitch shift |
| [Audio](audio.md) | Import, trim, fade, volume and speed control |
| [Images](images.md) | The Img component |
| [GIFs](gifs.md) | Timeline-synced GIF playback |
| [Assets](assets.md) | Importing any media into compositions |
| [Decode check](can-decode.md) | Validate browser compatibility |

### Captions and subtitles

| Rule | Description |
|------|-------------|
| [Transcribe captions](transcribe-captions.md) | Audio to captions via Whisper, Deepgram, or AssemblyAI |
| [Display captions](display-captions.md) | TikTok-style word-by-word highlighting |
| [Import SRT](import-srt-captions.md) | Load existing .srt files |

### Data visualization

| Rule | Description |
|------|-------------|
| [Charts](charts.md) | Animated bar charts, line graphs, data-driven visuals |

### Advanced

| Rule | Description |
|------|-------------|
| [3D content](3d.md) | Three.js and React Three Fiber |
| [Lottie](lottie.md) | After Effects animations via Lottie |
| [TailwindCSS](tailwind.md) | Style compositions with Tailwind |
| [DOM measurement](measuring-dom-nodes.md) | Measure element dimensions at render time |

### Media utilities

| Rule | Description |
|------|-------------|
| [Video duration](get-video-duration.md) | Get length in seconds |
| [Video dimensions](get-video-dimensions.md) | Get width and height |
| [Audio duration](get-audio-duration.md) | Get audio length |
| [Extract frames](extract-frames.md) | Pull frames at specific timestamps |

---

## Quick start

```bash
# Scaffold a project
npx create-video@latest my-video

# Preview in browser
cd my-video && npm start

# Render to MP4
npx remotion render src/index.ts MyComposition out/video.mp4

# Pass dynamic data
npx remotion render src/index.ts MyComposition out.mp4 --props '{"title": "Hello"}'
```

---

## Contribute

**Source:** [github.com/shreefentsar/remotion-video-toolkit](https://github.com/shreefentsar/remotion-video-toolkit)

Missing something? Found a better approach? Open a PR — new rules, improved examples, bug fixes all welcome.

Built by [Zone 99](https://99.zone)
