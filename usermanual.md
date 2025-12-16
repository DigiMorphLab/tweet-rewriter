# Web3 Tweet Rewriter User Manual

## 1. Quick Start
This project is a multi-model tweet rewriting tool designed for Web3 contexts.
**Note:** The rewriting process is primarily based on "Rewrite Intent". You simply provide the intent, and the system automatically selects the corresponding persona group to generate the tweet.

## 2. Core Logic
The system uses a "De-AI" approach to generate human-like content:
**Original Text + Rewrite Goal + Persona Library**

By combining the factual content of the original text with a specific rewrite goal and a matched persona, we avoid generic AI-sounding output and achieve authentic voice.

## 3. Rewrite Goals & Persona Types
We support 7 rewrite goals mapped to 5 persona types.

### Persona Types
- **Type A**: Traders & Degens (High Risk)
- **Type B**: Airdrop Farmers & Interaction (Price Sensitive)
- **Type C**: Builders & Techies (Junior/Worker)
- **Type D**: Vibes & NFT (Culture Driven)
- **Type E**: Realists & Normies (Outsider/Edge)

### Intent-Persona Mapping Logic

| Rewrite Intent | Mapped Persona Groups | Logic |
| :--- | :--- | :--- |
| **Authentic Experience (KOC)** | **Type B** (Farmer), **Type E** (Observer) | Real users who care about costs (B) or normal usage (E) are most likely to share authentic feedback. |
| **Professional Analysis (Trader)** | **Type A** (Trader), **Type C** (Builder) | Traders (A) care about price logic; Builders (C) understand the tech stack implication. |
| **News Relay (Media)** | **Type E** (Observer), **Type C** (Builder) | Observers (E) often retweet news; Builders (C) share industry updates. |
| **Light Sharing (Social)** | **Type D** (Vibes), **Type E** (Observer) | Vibe-focused users (D) and casual observers (E) engage in light social sharing. |
| **Alpha Call (Degen)** | **Type A** (Trader), **Type D** (Vibes) | Traders (A) want profit; Vibe users (D) hype up the community. |
| **Rational Skepticism (Skeptic)** | **Type C** (Builder), **Type A** (Trader) | Builders (C) spot technical flaws; Traders (A) spot bad tokenomics/Ponzi schemes. |
| **Practical Tutorial (Farmer)** | **Type B** (Farmer) | Airdrop farmers are the primary creators and consumers of "How-to" guides. |
