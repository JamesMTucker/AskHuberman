# Ask Andrew Huberman

<img src="https://hubermanlab.com/wp-content/uploads/2021/05/Huberman-Lab-Podcast-Intro-1920x1080-1-1080x608.jpeg">


## Description

Dr. Andrew Huberman is a neuroscientist at Stanford University. He has a YouTube channel where he posts educational videos about neuroscience. This repo contains machine learning code that analyzes Andrew Huberman's public facing scientific education materials. The code contained herein is not endorsed by Dr. Huberman, Stanford University, or any other entity.

Dr. Huberman's podcasts contain a wealth of information about neuroscience. However, the podcasts are long and it is difficult to find specific information. This repo contains code that uses machine learning to analyze the podcasts and provide a searchable interface, that includes a transcript of the podcast, and a list of topics discussed in the podcast. Various machine learning models furthermore connect Dr. Huberman's podcasts to other podcasts, and to other scientific papers in the PubMed and Semantic Scholar databases.

## Machine Learning's Role in Exploring Andrew Huberman's Contents:

For a machine learning-focused website, Dr. Andrew Huberman's content offers a treasure trove of insights into wellness, neuroscience, nutrition, and health. Here's how machine learning will be leveraged in our application:

1. **Content Categorization**: Machine learning algorithms categorize the vast amount of content available, making it easier for users to find specific topics related to wellness, nutrition, or health.
2. **Graph Database and Analysis**: By using a graph database, machine identifies relationships between various content pieces, helping users discover related content. The relationships are localized to `Ask Huberman`, and are globalized with other wellness, nutrition, and health content in our other applications, such `Ask Attia` and `Ask Patrick`.
3. **Recommendation Systems**: Based on user behavior and preferences, machine learning recommends relevant articles, podcasts, or research from Dr. Huberman's content, along with research from other applications such as `Ask Attia` and `Ask Patrick`.
4. **Sentiment Analysis**: By analyzing user comments and feedback, machine learning gauges the reception of specific content pieces, helping to highlight the most impactful ones.
5. **Predictive Analysis**: Using Dr. Huberman's insights, machine learning predicts potential health trends or emerging areas of interest in the wellness domain. The predictive measures are made in concert with neuroscience articles published and available on $BioRxiv$, $MedRxiv$, PubMed, and Semantic Scholar.
6. **Natural Language Processing** (NLP): Given Dr. Huberman's specialization in neuroscience, NLP is used to extract key insights, summarize content, and even answer user queries related to field of neuroscience, wellness, and health.

## Installation

On a linux machine, run `make` to build the environment. Mac and Windows versions of the environment are not currently supported, but will soon supported via Docker.
