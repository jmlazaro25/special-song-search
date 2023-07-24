import streamlit as st
from PIL import Image

import special_song_search as sss

# Reused strings
ARTIST = 'artist'
RECORDING = 'recording'
ARTIST_TAGS = 'artist_tags'
RECORDING_TAGS = 'recording_tags'
ARTIST_TAGS_WEIGHT = 'artist_tags_weight'
RECORDING_TAGS_WEIGHT = 'recording_tags_weight'
RECOMMENDATIONS = 'recommendations'


def main() -> None:

    st.set_page_config(
        page_title='Special Song Search',
        page_icon=Image.open('images/3s_logo_no_sub.png'),
        layout='wide',
        initial_sidebar_state='auto',
        menu_items=None
    )

    st.markdown("""
        <style>
            .block-container {padding-top: 0 !important;}
        </style>""",
        unsafe_allow_html=True,
    )

    st.title('Special Song Search')

    with st.expander("How Special Song Search works:"):
        st.text("""
        Motivation:
            Existing song recomendation services:
            - Use stubborn collaborative models which are slow to learn your individual preferences
            - Make repeated suggestions too often which also limits discovery potential
            - Collect personal data

        Build:
            1. Artist and recording metadata are collected from the MusicBrainz API.
            2. Data is stored database-agnostically via SQLalchemy (see schema below).
            3. Values entered on this webpage are used to query recordings from the database.
                - This includes selecting a score which is a linear sum of match values plus a random factor which will also be exposed to the user.

        Usage:
            1. Add any number of artist-related or recording-related tags you like.
            2. Give each tag as well as each category a weight.
                - They do not need to be on any particular scale but should be relative to each other for best results.
            3. Submit at the bottom of the "Options" column.
            4. Stay tuned for more options like recording length and number of recommendations.
        """)
        st.markdown(
        """[Github repository](https://github.com/jmlazaro25/special-song-search)""",
        unsafe_allow_html=True
        )
        st.image(Image.open('images/sss_db_white.drawio.png'))

    col_1, col_2 = st.columns((2,2))

    sql_session = init_sql_session()
    with sql_session:

        with col_1:
            st.header('Options')

            # Artist Tags
            display_tags(sql_session, ARTIST)

            # Recording Tags
            display_tags(sql_session, RECORDING)

            # Other recording params

            # Submit
            st.button('Submit', on_click=lambda: get_recommendations(sql_session))

        with col_2:
            st.header('Recommendations')
            if RECOMMENDATIONS in st.session_state:
                display_recommendations()

    st.divider()
    st.button('Clear', on_click=clear)

    return

@st.cache_resource
def init_sql_session():
    _, sql_sessionmaker = sss.database.init_db('main')
    return sql_sessionmaker()

@st.cache_data
def get_tag_options_cached(_session, tag_type):
    return sss.recommend.get_tag_options(_session, tag_type)

def increase_tags(tags):
    if not st.session_state[tags]:
        st.session_state[tags] = [1]
    else:
        st.session_state[tags].append(st.session_state[tags][-1] + 1)

def display_tags(session, tag_type):

    def display_tag(tag_num):
        tag, weight, rm = st.columns((4, 1, 0.5))
        options = get_tag_options_cached(session, tag_type)
        label_vis = 'visible' if tag_num == 0 else 'collapsed'
        tag.selectbox(
            label='Tag',
            options=options,
            key=f'{tag_type}_tag_{tag_num}',
            placeholder='tag',
            label_visibility=label_vis
            )
        weight.number_input(
            label='Weight',
            key=f'{tag_type}_weight_{tag_num}',
            label_visibility=label_vis
            )
        def del_tag():
            del st.session_state[f'{tag_type}_tag_{tag_num}']
            del st.session_state[f'{tag_type}_weight_{tag_num}']
        rm.button(':no_entry:', key=f'rm_{tag_type}_{tag_num}', on_click=del_tag)

    if tag_type == ARTIST:
        tags = ARTIST_TAGS
        weight = ARTIST_TAGS_WEIGHT
    elif tag_type == RECORDING:
        tags = RECORDING_TAGS
        weight = RECORDING_TAGS_WEIGHT

    st.subheader(f'{tag_type} tags'.title())
    st.number_input(
        label=f'total {tag_type} tags weight'.title(),
        key=weight
    )

    if tags not in st.session_state:
        st.session_state[tags] = []

    for n in st.session_state[tags]:
        display_tag(tag_num=n)

    st.button(f'add {tag_type} tag'.title(), on_click=lambda: increase_tags(tags))
    st.divider()

#@st.cache_data
def get_recommendations(_session):
    def get_tags(tag_type):
        if tag_type == ARTIST:
            tags = ARTIST_TAGS
        elif tag_type == RECORDING:
            tags = RECORDING_TAGS
        return {
            st.session_state[f'{tag_type}_tag_{tag_num}']:
            st.session_state[f'{tag_type}_weight_{tag_num}']
            for tag_num in st.session_state[tags]
        }

    st.session_state[RECOMMENDATIONS] = \
        sss.recommend.recommend(
            _session,
            artist_tags = get_tags(ARTIST),
            recording_tags = get_tags(RECORDING),
            recording_length = tuple(),
            weights = {
                key: st.session_state[f'{key}_weight'] for key in (
                ARTIST_TAGS,
                RECORDING_TAGS
                ) if f'{key}_weight' in st.session_state
                },
            randomness = 1.,
            limit = 10
        )

def display_recommendations():
    for n, rec in enumerate(st.session_state[RECOMMENDATIONS]):
        st.divider()
        st.markdown(f"##### {n}. {rec['recording']['title']}")
        st.text(f"Score: {rec['score']:.2f}")
        st.text(', '.join([artist['name'] for artist in rec['artists']]))
        st.markdown(f"""
        [MusicBrainz]({sss.musicb.RECORDING_PERM_LINK.format(rec['recording']['mbid'])})
        [ListenBrainz]({sss.musicb.LISTEN_LINK.format(rec['recording']['mbid'])})
        """)

def clear():
    for key in st.session_state:
        del st.session_state[key]


if __name__ == '__main__':
    main()
