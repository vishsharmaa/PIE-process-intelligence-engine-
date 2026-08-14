---
title: "Semiconductor Fab Process Control and Yield Management"
publisher: "SEMI Standards"
url: "https://example.com/semiconductor-process-control"
year: 2023
doc_type: "standard"
credibility_tier: 1
---

Semiconductor fabrication (fab) process control represents the most data-intensive manufacturing environment in existence. A modern 300mm wafer fab generates over 10 terabytes of process data per day across 500–800 process steps, with thousands of sensors monitoring each step. Statistical process control, run-to-run control, and fault detection and classification (FDC) systems operate continuously to maintain nanometer-scale precision.

Run-to-run (R2R) control adjusts process recipe parameters between wafer lots based on metrology measurements and process history. R2R controllers use exponentially weighted moving average (EWMA) models to estimate process drift and preemptively correct for it. In chemical mechanical planarization (CMP), R2R control adjusts polishing time and downforce based on removal rate measurements from the previous lot, maintaining thickness uniformity within ±0.5nm across a 300mm wafer.

Fault Detection and Classification (FDC) analyzes real-time sensor data during wafer processing to detect equipment faults before they produce out-of-spec wafers. FDC systems compare current sensor traces against golden reference traces using multivariate statistical methods (PCA, PLS) and ML models. Detected faults trigger automated wafer holds, equipment alerts, and maintenance dispatches. Leading FDC systems achieve fault detection rates above 90% with false alarm rates below 5%.

Yield management in semiconductor manufacturing tracks defect density, parametric yield, and functional yield across process layers and product types. Yield Management Systems (YMS) correlate yield loss to specific process layers, equipment, and process parameters using statistical regression and ML. Spatial yield mapping — analyzing the wafer map pattern of failing die — provides diagnostic information about equipment and process root causes (chamber contamination, edge effects, systematic vs. random defects).

Advanced process control (APC) encompasses all levels of automated control: Equipment Control (individual machine setpoints), Run-to-Run Control (lot-level adjustments), and Supervisory Control (facility-wide optimization). APC maturity is a key differentiator between leading-edge fabs (sub-7nm nodes) and commodity fabs. The complexity of APC systems at leading-edge nodes requires hundreds of engineers to develop, maintain, and continuously improve.
