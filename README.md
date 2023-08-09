# Special Song Search
https://special-song-search.onrender.com

## Table of Contents
[Introduction](#introduction)<br>
[Build](#build)<br>
[Data Preview](#data_preview)

## Introduction <a name="introduction"></a>
Special-song-search is a web application that allows you to search for new songs fitting all of your requirments.

Rather than using a machine learning model which needs to collect your data to make some acceptable recommendations, SpecialSong Search provides several options and relies on you to specify what is most important to you. This means:
1. It doesn't have to store your data.
2. It can quickly alter its recomendations.
3. If you like the results, it won't keep re-recommending the same small set of songs as some other recomendation engines do.

Here is an example:

![Special Song Search Screenshot](/images/display_example.png)

## Build <a name="build"></a>
This is the result of:
1. Collecting open artist and song (recording) data from [MusicBrainz](https://musicbrainz.org/)'s API,
2. Storing it in a new database using SQLAlchemy for faster access,
   - This repo contains an SQLite database, but the code is database agnostic to enable scaling
4. And creating a Streamlit app with which users can interact.

## Data Preview <a name="data_preview"></a>
In the modest data collection that has been done so far, the top 30 recording tags account for slightly over half of tags used:
![Top 30 Recording Tags Histogram](/images/recording_tag_freq.png)

Notably, rock has several variations appearing in the top 30 recording tags: "alternative rock," "pop rock," "indie rock," "classic rock," "hard rock," "folk rock," "progressive rock," and "blues rock." This also occurs with other genre tags such pop. This begs the question: How much of this is overlap (i.e. recordings being labelled "rock" and one or more variations vs. just being labelled "rock")?

![Rock Tags Heatmap](/images/rock_heatmap.png)

This heatmap shows the count of recordings with a tag-pair as a fraction of the count of the tag on the diagnol for the tag-pair's row. The bright left-most column indicates that recordings tagged with any other variation of rock are also likely tagged with rock itself. For anyone who likes other forms of rock, but not alternative rock, they should rest assured that even though it is the most common subset of rock in this dataset, it still only accounts for a fifth of all rock and they can search for another subgenre with little overlap. Anyone wanting to slowly explore new genres or subgenres can choose their favorite tag and search for new tags with which it often appears together.

`data_analysis.ipynb` shows how these plots can be generated and goes into more detail about the data.
