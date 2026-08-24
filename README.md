\# Twitter Events



A Multidimensional Indicator Framework for Interpreting Social Media Events



This repository contains the source code and dataset-related resources for analyzing and interpreting social media events on Twitter/X using a multidimensional indicator framework.



The framework is introduced in the paper:



> \*\*A Multidimensional Indicator Framework for Interpreting Social Media Events\*\*



The proposed framework analyzes social media events through multiple complementary dimensions instead of relying on a single indicator such as the number of tweets or total interactions.



\---



\## Overview



The volume of tweets associated with an event does not necessarily represent meaningful user participation, information diffusion, public attention, or influence.



For example, an event may generate a large number of tweets but involve limited interaction among users. Conversely, an event with fewer tweets may show stronger engagement, broader participation, or more effective information diffusion.



To address this issue, this project introduces a multidimensional analytical framework covering the following seven dimensions:



1\. Event scale and reach

2\. Attention and engagement

3\. Temporal dynamics

4\. User diversity and composition

5\. Power concentration

6\. Interaction-network structure

7\. Sentiment polarity and discrete emotions



The framework is designed for Sentiment polarity and discrete emotions



The framework is designed for communication analysis

\- Campaign evaluation

\- Public opinion analysis

\- Information diffusion analysis

\- Social network analysis

\- Event interpretation and comparison



\---



\## Research Paper



\### Title



\*\*A Multidimensional Indicator Framework for Interpreting Social Media Events\*\*



\### Authors



\- Emad Ghavidel, Faculty of Computer Engineering and Information Technology, Sadjad University, Mashhad, Iran

\- Mohammadreza Khorrami, Department of Computer Engineering, Sharif University of Technology, Tehran, Iran

\- Javad Hamidzadeh, Faculty of Computer Engineering and Information Technology, Sadjad University, Mashhad, Iran

\- Abbas Ajami Khales, Department of Computer Engineering, Ferdowsi University, Mashhad, Iran

\- Seyyed Iman Doosti Moosavi, Khorasan Institute of Higher Education, Mashhad, Iran



\### Abstract



This project presents a multidimensional and interpretable framework for analyzing social media events on Twitter/X.



The framework evaluates events through seven groups of indicators, including event scale and reach, attention and engagement, temporal dynamics, user diversity and composition, power concentration, interaction-network structure, and sentiment polarity with discrete emotions.



The empirical analysis uses 203,353 tweets from five events on Twitter/X, involving 53,990 unique user accounts. The data are analyzed cumulatively and in one-hour time windows.



The proposed framework covers all seven analytical dimensions, while the strongest multidimensional baseline considered in the study covers only three dimensions. Therefore, the proposed framework provides an absolute coverage improvement of four dimensions.



\---



\## Dataset



The study analyzes five Twitter/X events collected between November 2025 and January 2026:



\- Two hashtag-based campaigns

\- Three news-related events



The dataset contains:



\- 203,353 tweets

\- 53,990 unique user accounts

\- Tweet interaction metadata

\- View counts

\- Like counts

\- Repost counts

\- Quote counts

\- Reply counts

\- User-related features

\- Temporal activity information



The data are aggregated and analyzed using one-hour time windows.



The exact campaign hashtags are not publicly disclosed in the paper in order to protect user anonymity.



\### Dataset Availability



The `Dataset` directory is reserved for dataset-related files. At the current stage, the directory contains a `.gitkeep` file.



Raw Twitter/X data, user identifiers, API credentials, and other sensitive information must not be committed to this repository.



\---



\## Framework Dimensions



\### 1. Event Scale and Reach



This dimension measures the overall size and visibility of an event using indicators such as:



\- Number of tweets

\- Number of unique users

\- Number of interactions

\- Number of views

\- Event reach



\### 2. Attention and Engagement



This dimension evaluates how actively users interact with event-related content.



Potential interaction signals include:



\- Likes

\- Reposts

\- Quotes

\- Replies

\- Views

\- User participation



The exact formulas for the engagement and virality rates are defined in the implementation or supplementary project documentation. They are not fully specified in the paper.



\### 3. Temporal Dynamics



Temporal indicators analyze how event activity changes over time.



The framework uses one-hour time windows to identify:



\- Activity peaks

\- Growth patterns

\- Sudden changes

\- Event acceleration

\- Natural or artificially amplified activity waves



The acceleration index is defined as:



\\\[

\\text{Acceleration Index}

=

\\frac{1}{T}

\\sum\_{t=3}^{T}

\\frac{

\\max(v\_t - 2v\_{t-1} + v\_{t-2}, 0)

}{

v\_t

}

\\]



where:



\- \\(T\\) is the number of time intervals

\- \\(v\_t\\) is the number of tweets in time interval \\(t\\)



\### 4. User Diversity and Composition



This dimension measures the diversity and composition of participating user groups.



Shannon entropy is used to measure the diversity and distribution of political user groups:



\\\[

H = -\\sum\_{i=1}^{k} \\rho\_i \\ln(\\rho\_i)

\\]



where:



\- \\(k\\) is the number of user groups

\- \\(\\rho\_i\\) is the proportion of group \\(i\\)



The framework also uses the Hill number to represent the effective number of groups. The complete implementation details and parameter settings are provided in the source code when available.



\### 5. Power Concentration



Power concentration measures whether the attention or influence associated with an event is distributed broadly or concentrated among a small number of users.



This dimension is relevant for identifying:



\- Influential users

\- Coordinated activity

\- Concentrated information diffusion

\- Unequal distribution of interactions

\- Repeated participation by highly active accounts



\### 6. Interaction-N activities Structure



The interaction network represents relationships among users based on activities such as:



\- Replies

\- Reposts

\- Quotes

\- Mentions

\- Other available interactions



The network dimension is used to analyze:



\- Network connectivity

\- Interaction structure

\- User influence

\- Repeated-user activity

\- Network power

\- Possible coordination patterns



The exact graph construction procedure and the complete definition of network power depend on the implementation.



\### 7. Sentiment Polarity and Discrete Emotions



The framework distinguishes between general sentiment polarity and discrete emotions.



A positive sentiment score does not necessarily indicate the absence of negative emotions. For example, the paper reports that event E2 had approximately:



\- 88% positive sentiment polarity

\- Approximately 85% prevalence of disappointment



This example demonstrates why sentiment polarity and discrete emotions should be analyzed separately.



\---



\## Experimental Results



The study evaluates five real-world Twitter/X events.



The main reported results include:



| Indicator | Result |

|---|--- Unique user accounts | 53,203,353 |

| Unique user accounts | 53,990 |

| Tweets in event E5 | 91,554 |

| Interactions in event E5 | 742,609 |

| Engagement rate of event E1 | 15.73% |

| Virality rate of event E1 | 4.61% |

| Positive polarity in event E2 | Approximately 88% |

| Dominant disappointment emotion in event E2 | Approximately 85% |



\### Shannon Entropy Results



| Event | Shannon Entropy |

|---|---:|

| E3 | 1.28 |

| E4 | 1.18 |

| E1 | 1.15 |

| E2 | 0.94 |

| E5 | 0.91 |



\### Main Findings



\- Event E5 had the highest number of tweets.

\- Event E1 achieved the highest engagement rate.

\- Event E1 also showed the highest virality rate.

\- Hashtag-based campaigns showed greater acceleration than news events.

\- Hashtag-based campaigns showed higher repeated-user activity.

\- Hashtag-based campaigns showed greater power concentration.

\- The proposed framework covers seven analytical dimensions.

\- The strongest multidimensional comparison method covered three dimensions.

\- The proposed framework therefore improves multidimensional coverage by four dimensions.



\---



\## Repository Structure



The current repository contains the following directories:

```text

twitter\_events/

├── Code/                  # Source code and implementation files

├── Dataset/               # Dataset files or dataset references

└── README.md              # Project documentation



