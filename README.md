# Twitter Events: A Multidimensional Indicator Framework for Interpreting Social Media Events

This repository contains the implementation and supporting materials for a research framework that interprets social-media events through multiple complementary indicators rather than a single volume-based signal. The framework is designed to provide a comprehensive, explainable, and multidimensional view of social-media events on Twitter/X.

Repository: [github.com/hamidzadehj/twitter_events](https://github.com/hamidzadehj/twitter_events)

## Contents

- [Project status](#project-status)
- [Project goals](#project-goals)
- [What the framework measures](#what-the-framework-measures)
- [Mathematical formulation](#mathematical-formulation)
- [Method](#method)
- [Experimental results](#experimental-results)
- [Repository layout](#repository-layout)
- [Requirements](#requirements)
- [Citation](#citation)

## Project status

| Workstream | Status |
|---|---|
| Research framework implementation | Complete |
| Mathematical model definition | Complete |
| Dataset structure | Complete |
| Empirical validation | In progress |

## Project goals

This project addresses the limitations of interpreting social-media events based on a single indicator (e.g., raw tweet volume). The framework covers seven distinct dimensions:

1. **Event Scale and Reach**
2. **Attention and Engagement**
3. **Temporal Dynamics**
4. **User Diversity and Composition**
5. **Power Concentration**
6. **Interaction-Network Structure**
7. **Sentiment Polarity and Discrete Emotions**

## What the framework measures

The framework evaluates events by aggregating activity data over defined temporal windows. It differentiates between simple activity spikes and complex, multidimensional events by analyzing user participation, network dynamics, and emotional variance.

## Mathematical formulation

The framework utilizes three primary indicators for analytical rigor:

### 1. Acceleration Index
To quantify the surge or decline in activity relative to previous intervals:

$$
\text{Acceleration Index} = \frac{1}{T} \sum_{t=3}^{T} \frac{\max(v_t - 2v_{t-1} + v_{t-2}, 0)}{v_t}
$$

Where:
- $T$: Total number of temporal windows.
- $v_t$: Number of tweets in time window $t$.

### 2. Shannon Entropy
Used to evaluate the diversity and distribution of user groups within an event:

$$
H = -\sum_{i=1}^{k} \rho_i \ln(\rho_i)
$$

Where:
- $k$: Number of unique user groups/categories.
- $\rho_i$: Proportion of the $i$-th group in the total activity.

### 3. Hill Numbers
Used to calculate the effective diversity of groups (Effective Number of Groups):

$$
D_q = \left(\sum_{i=1}^{S} p_i^q\right)^{\frac{1}{1-q}}
$$

Where:
- $S$: Total number of groups.
- $p_i$: Relative frequency (proportion) of the $i$-th group.
- $q$: Sensitivity parameter (order of diversity).

## Method

The pipeline processes raw Twitter/X data into time-binned aggregates. By calculating these indices across the seven dimensions, the framework can classify events (e.g., hashtag campaigns vs. breaking news events) based on their structural and behavioral fingerprints.

## Experimental results

The framework has been tested on a dataset of 203,353 tweets from 53,990 unique accounts. Key findings include:

| Metric | Result |
| :--- | :--- |
| **Engagement Rate (E1)** | 15.73% |
| **Virality Rate (E1)** | 4.61% |
| **Positive Sentiment Polarity** | ~88% |
| **Dominant Emotion (Disappointment)** | ~85% |

## Repository layout
```text
twitter_events/
├── Code/
│   └── Emad-Source.py
├── Dataset/
│   └── .gitkeep
└── README.md
