# Diagrams

SVG diagrams corresponding to the figures referenced in the book. All diagrams are vector-format (SVG) — scalable to any print or screen resolution without quality loss.

## Files

| File | Figure | Chapter | Description |
|------|--------|---------|-------------|
| `fig_03_4_nlp_pipeline.svg` | Fig. 3.4 | Ch. 3 | NLP processing pipeline (tokenisation → intent → entity → DM → response) |
| `fig_08_1_fsm_dialogue.svg` | Fig. 8.1 | Ch. 8 | Finite State Machine for the flight booking dialogue |
| `fig_10_2_platform_comparison.svg` | Fig. 10.2 | Ch. 10 | Bot platform comparison matrix (Dialogflow, Rasa, OpenAI, Lex, Bot Framework) |
| `fig_11_1_architecture_overview.svg` | Fig. 11.1 | Ch. 11 | End-to-end chatbot system architecture |
| `fig_14_1_analytics_funnel.svg` | Fig. 14.1 | Ch. 14 | Conversation analytics funnel with KPI summary |

## Viewing

Open any `.svg` file in a modern web browser or vector editor (Inkscape, Adobe Illustrator, Figma). They can also be embedded directly in HTML:

```html
<img src="resources/diagrams/fig_03_4_nlp_pipeline.svg" alt="NLP Pipeline" />
```

Or inline for full CSS control:
```html
<!-- paste SVG content directly into your HTML -->
```

## Exporting to PNG / PDF

To export for print layouts, use Inkscape CLI:
```bash
inkscape fig_08_1_fsm_dialogue.svg --export-png=fig_08_1_fsm_dialogue.png --export-dpi=300
```

Or with ImageMagick:
```bash
convert -density 300 fig_11_1_architecture_overview.svg fig_11_1_architecture_overview.png
```
