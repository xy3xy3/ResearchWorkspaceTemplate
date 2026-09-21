# Figure workflow

Quantitative: establish the claim, exact data artifact, units, metric direction, uncertainty meaning, and comparison conditions. Choose a chart form that exposes the intended comparison without distorting scale. Do not silently omit failed runs, choose only favorable seeds, reverse error bars, or use truncated axes without a clear reason and disclosure. A plotting helper does not supply statistical justification.

The bundled CSV tool produces one series with no automatic aggregation. For repeated measures/multiple groups, author a proper analysis/plot script and keep its input data. Error magnitudes are supplied values, not inferred confidence intervals. Matplotlib is an optional local dependency. Preserve both editable source and provenance; rerendering alone does not verify science.

Method diagram: map real modules and their inputs/outputs before layout. Separate data flow, control flow, losses, and inference/training paths. Check arrows against actual computation and name each symbol consistently with the paper. Favor a readable final publication size over arbitrary aspect ratios. Keep SVG groups/text or TikZ source semantically editable. Raster illustrations are allowed when appropriate but must not be called editable vector diagrams.

Visual review checks labels, overlap, clipping, font availability, contrast, whole-figure balance, uncertainty display, scientific topology and factual captions. Record limitations when visual inspection is unavailable; file existence is insufficient.

LaTeX integration example, using an actual created figure folder:

```latex
\begin{figure}[t]
  \centering
  \includegraphics[width=\linewidth]{figures/main-comparison/figure.pdf}
  \caption{Replace with an evidence-backed description of the actual comparison.}
  \label{fig:main-comparison}
\end{figure}
```

Rendered paper figures and their sources belong to the independent paper repository. The no-image policy for ref/ concerns downloaded literature, not the figures authored for the user's own paper.
