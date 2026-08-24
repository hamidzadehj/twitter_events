# Twitter Events: A Multidimensional Indicator Framework for Interpreting Social Media Events

This repository contains the implementation and supporting materials for a research framework that interprets social-media events through multiple complementary indicators rather than a single volume-based signal.

In this project, an **event** is a coordinated or naturally emerging change in Twitter/X activity that becomes visible through shifts in scale, engagement, timing, user composition, power concentration, network structure, and sentiment. An event is not defined by tweet count alone.

Repository: [github.com/hamidzadehj/twitter_events](https://github.com/hamidzadehj/twitter_events)

## Contents

- [Project status](#project-status)
- [Project goals](#project-goals)
- [What the framework measures](#what-the-framework-measures)
- [Method](#method)
- [Dataset](#dataset)
- [Repository layout](#repository-layout)
- [Requirements](#requirements)
- [Reproducing the experiment](#reproducing-the-experiment)
- [Input and output file contracts](#input-and-output-file-contracts)
- [Validation and safety rules](#validation-and-safety-rules)
- [Statistical analysis](#statistical-analysis)
- [Data availability, privacy, and ethics](#data-availability-privacy-and-ethics)
- [Limitations](#limitations)
- [Citation](#citation)

## Project status

| Workstream | Status |
|---|---|
| Research code extraction | Complete |
| Repository skeleton | Complete |
| Dataset directory structure | Complete |
| Paper-to-code alignment review | In progress |
| End-to-end reproduction script | Not yet verified |

The repository currently contains a single source file in `Code/` and an empty dataset placeholder in `Dataset/`. The exact runtime entrypoint, command-line interface, and required dependencies should be confirmed from the code before production use.

## Project goals

This project is intended to support event interpretation on Twitter/X using a multidimensional analytical view. The framework is designed to reduce overreliance on any single indicator such as raw tweet volume.

The main goals are:

1. Measure event scale and reach.
2. Measure engagement and attention.
3. Capture temporal dynamics such as acceleration.
4. Study user diversity and composition.
5. Identify concentration of power or influence.
6. Characterize interaction-network structure.
7. Analyze sentiment polarity and discrete emotions.

## What the framework measures

The framework centers on the following analytical dimensions:

- event scale and reach;
- attention and engagement;
- temporal acceleration;
- user diversity and repeated participation;
- power concentration;
- interaction-network structure;
- sentiment polarity; and
- discrete emotions.

## Method

### 1. Event-level aggregation

The analysis is performed on time-binned social-media activity. For each event window, the framework aggregates tweet counts, interaction counts, and user-level participation signals.

### 2. Temporal dynamics

To capture changes over time, the framework uses an acceleration-style measure based on second-order differences in volume:

$$
\text{Acceleration Index} = \frac{1}{T} \sum_{t=3}^{ \frac{\max(vmax(v_t - 2v_{t-1} + v_{t-2}, 0)}{v_t}
$$

where:

- $T$ is the number of time windows;
- $v_t$ is the volume in window $t$.

### 3. User diversity

To quantify user diversity and concentration, the framework uses entropy-based measures such as Shannon entropy:

$$
H = -\sum_{i=1}^{k} \rho_i \ln(\rho_i)
$$

where:

- $k$ is the number of user groups or categories;
- $\rho_i$ is the proportion of group $i$.

### 4. Effective diversity

A standard Hill-number formulation can also be used to express effective diversity:

$$
D_q = \left(\sum_{i=1}^{S} p_i^q\right)^{\frac{1}{1-q}}
$$

where:

- $S$ is the number of groups;
- $p_i$ is the relative frequency of group $i$;
- $q$ controls sensitivity to common versus rare groups.

## Dataset

The repository includes a `Dataset/` directory intended for input data or derived artifacts. At the moment, the directory is only a placeholder and does not contain published raw data.

If your local version includes event data, the README should document:

- source platform;
- collection period;
- event definition;
- sampling strategy;
- included fields;
- privacy handling;
- preprocessing steps.

## Repository layout
```text
twitter_events/
├── Code/
│   └── Emad-Source.py
├── Dataset/
│   └── .gitkeep
└── README.md
