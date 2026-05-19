# UI Verification

Since `demo/src/ui/` contains DOM code, it cannot be automatically tested with vitest.
Use the following manual checklist instead.

## Before state (basic random)

Open `demo/index.html` in a browser (no server needed — plain file).

- [ ] Page loads without console errors
- [ ] "번호 뽑기" button is visible
- [ ] Game count selector shows 1–5 options
- [ ] Clicking the button generates 6 lotto balls
- [ ] Each ball shows a number in [1, 45]
- [ ] No duplicate numbers in one draw
- [ ] Ball color matches the range:
  - 1–10: yellow
  - 11–20: blue
  - 21–30: red
  - 31–40: black/dark
  - 41–45: green
- [ ] Multiple games display correctly
- [ ] Repeated clicks replace previous results

## Saving a screenshot

After confirming the above, save a screenshot to `logs/`:

```
logs/<YYYY-MM-DD>-before-ui.png
logs/<YYYY-MM-DD>-after-ui.png
```

This satisfies **Garbage collection** (pillar ③) — evidence that the feature was verified.
