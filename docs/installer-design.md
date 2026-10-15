# Installer design reference

The current homepage and get-started page are the design reference. Their
page-specific styles override the older purple/cyan defaults in `global.css`.
No separate corporate design guide is present in this repository.

| Element | Website evidence | Terminal treatment |
| --- | --- | --- |
| Accent | `body.landing` in `frontend/src/pages/index.astro`: `#9cbedc`; the get-started page and brand symbol use the related `#a9c5df` | Exact `#9cbedc` for status marks on terminals advertising truecolor; xterm color 110 (`#87afd7`) is the blue approximation for 256-color terminals. Basic terminals retain their foreground. |
| Surfaces and text | Both pages use charcoal `#18191b` and off-white `#e7e7e4`; command surfaces use `#111214` / `#141517` | The installer preserves the user's terminal background and normal text color. Essential text stays readable in the user's theme; only decorative progress/status marks use the accent. |
| Wordmark | Both pages show lowercase “deploy your startup”; `BrandMark.astro` combines a terminal prompt and rocket | Lowercase wordmark with `>_`, the text-compatible part of that mark. This is a terminal adaptation, not a reproduction of the SVG logo. |
| Copy | Homepage: “Ideas in. Startups out.” and “Build your idea. Find out what works.” | Uses those exact phrases. |
| Type | Inter for headings and JetBrains Mono for commands | Inherits the user's monospace terminal font; does not install fonts or change terminal preferences. |
| Motion | Homepage factory rocket travels left-to-right over eight seconds; its nodes pulse on arrival. The hero rocket also launches when the install command is copied. | A four-position `›···` indicator travels left-to-right during the silent GitHub connection check, with a one-second cycle. Verified authentication replaces it with `✓`. Installation steps keep static headings so detailed package logs remain readable. This adapts the direction and purpose of the motion, not its artwork or timing. |
| Reduced motion | `global.css` disables animation under `prefers-reduced-motion` | `STARTUP_NO_ANIMATION=1` disables motion while keeping supported colors. Terminals do not expose the browser preference; the flag follows the companion CLI convention. |

When validating changes, compare terminal output against the active homepage
palette and copy. Check truecolor, 256-color and basic terminals, motion opt-out,
redirected output, cancellation and the installer produced by the Astro build.
Record the scenarios actually executed with the change.

Checks with local download and GitHub stand-ins do not establish live macOS
rendering, real OAuth approval, or which revision is currently deployed at the
public website.

## Suggested follow-up

Consolidate the active page palettes into shared brand variables, then remove
obsolete purple/cyan rules after checking their remaining consumers. The current
overrides make it easy to mistake unused defaults for the active design. Keep
the terminal compatibility fallbacks explicit rather than promising exact RGB
colors on every terminal.

Apply the same palette to the companion CLI's existing wizard output in a
separate change: its headings and rocket wordmark still use named ANSI cyan.
The installer handoff does not override colors chosen by the CLI or GitHub CLI.
