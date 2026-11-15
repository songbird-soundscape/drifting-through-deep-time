# Next steps and handoff

Notes for picking this work up in a new chat. Paste this file, or its link, into that chat to begin.

## Where things live

| What | Where |
|---|---|
| Drifting Through Deep Time (repo, MIT) | https://github.com/songbird-soundscape/drifting-through-deep-time |
| The Open Commons of Learning (repo, CC BY 4.0) | https://github.com/songbird-soundscape/open-commons |
| Live sites (once Pages is on) | https://songbird-soundscape.github.io/drifting-through-deep-time/ · https://songbird-soundscape.github.io/open-commons/ |

Each site is a single `index.html`. Drifting Through Deep Time also loads `data/` and `sprites/`.

## Access a new chat will need

- **GitHub:** the Claude GitHub App must be installed on `songbird-soundscape` with access to both repos (it already is). In a new Claude Code session, add both repos, or ask Claude to attach them.
- **Things only you can do on github.com** (Claude's session can't change these settings):
  - Settings → Pages → Deploy from branch `main` / root, for **both** repos.
  - Settings → General → Features → turn on **Discussions** for `open-commons` (the forum).
  - The About box on `drifting-through-deep-time`: description, website and topics.
- **Testing tip:** the map library (`pako`) comes from cdnjs, which may be blocked in a cloud session. Get it with `npm pack pako@2.1.0` and serve it to Playwright with `context.route(/pako_inflate/, …)`. The globe then renders properly in tests.

## Ideas saved for later

### Drifting Through Deep Time

1. **Seasonal migrations and phenology:** a "this year" view next to deep time. Jan → Dec on the slider, with animal migrations moving and the land greening and browning.
   - Suggested first version: global satellite greenness (MODIS/VIIRS, public domain) plus 4–6 well-known migrations (Arctic tern, monarch, a stork, caribou, a whale, a warbler).
   - Possible data: eBird Status & Trends (free, but needs a key and has license terms), Movebank (licenses vary by study), USA-NPN (US phenology).
   - Decide: which species and regions (maybe the birds you band?), and whether the data servers can be reached from the session.
2. **Phones:** the plant tree now grows with playback (no tap needed); check that it feels right on a real phone.
3. **Computers:** possibly slim the play bar further to just the play button.

### Posting Drifting Through Deep Time elsewhere (later)

Turn on GitHub Pages first, so the links work. Then, in this order:

1. **Zenodo:** link GitHub, switch on this repo, and make a release such as "v1.0" to get a DOI. Use this one DOI everywhere.
2. **SERC Teach the Earth:** submit an activity write-up.
3. **QUBES:** post it citing the Zenodo DOI. Don't take a second DOI.
4. **OER Commons:** add a listing.
5. **Wikiversity:** paste `docs/wikiversity-draft.wiki` (ready to go).

Keep the site and repo as the one real home. Send corrections to one place, either the Wikiversity talk page or GitHub issues. Claude offered to build a submission kit with descriptions, keywords, a citation and a SERC-format activity.

### The Open Commons of Learning

4. **Once Pages is live:**
   - Remake the QR sign so it points to `https://songbird-soundscape.github.io/open-commons/`.
   - Draft the forum categories and a welcome post.
   - Draft an announcement.
5. **Network map:**
   - Optionally add all 26 library books.
   - Add gap books and an Open access shelf.
   - Check the direction of the "mentoring" labels.
   - Add more of your own projects as knowledge hubs. They'll show up in step 1 of **Explore projects** (`#explore`).
6. **Wording:** clarify prospective students vs foundation-year students.
